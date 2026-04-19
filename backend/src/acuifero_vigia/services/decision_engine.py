from __future__ import annotations

import json

from sqlmodel import Session, select

from acuifero_vigia.models.domain import (
    FusedAlert,
    HydrometSnapshot,
    NodeObservation,
    ParsedObservation,
    VolunteerReport,
)



def level_from_score(score: float) -> str:
    if score >= 0.82:
        return "red"
    if score >= 0.62:
        return "orange"
    if score >= 0.4:
        return "yellow"
    return "green"



def recompute_site_alert(session: Session, site_id: str) -> FusedAlert:
    latest_node = session.exec(
        select(NodeObservation)
        .where(NodeObservation.site_id == site_id)
        .order_by(NodeObservation.ended_at.desc())
    ).first()
    latest_report = session.exec(
        select(VolunteerReport)
        .where(VolunteerReport.site_id == site_id)
        .order_by(VolunteerReport.created_at.desc())
    ).first()
    latest_parsed = None
    if latest_report and latest_report.id is not None:
        latest_parsed = session.exec(
            select(ParsedObservation)
            .where(ParsedObservation.volunteer_report_id == latest_report.id)
            .order_by(ParsedObservation.id.desc())
        ).first()
    latest_hydromet = session.exec(
        select(HydrometSnapshot)
        .where(HydrometSnapshot.site_id == site_id)
        .order_by(HydrometSnapshot.created_at.desc())
    ).first()

    weighted_components: list[tuple[str, float, str]] = []
    if latest_node:
        weighted_components.append(("node", latest_node.severity_score, f"node={latest_node.severity_score:.2f}"))
    if latest_parsed:
        weighted_components.append(("volunteer", latest_parsed.severity_score, f"volunteer={latest_parsed.severity_score:.2f}"))
    if latest_hydromet:
        weighted_components.append(("hydromet", latest_hydromet.signal_score, f"hydromet={latest_hydromet.signal_score:.2f}"))

    if not weighted_components:
        alert = FusedAlert(
            site_id=site_id,
            level="green",
            score=0.0,
            trigger_source="fused",
            summary="No recent signals available",
            decision_trace=json.dumps(["No node, volunteer, or hydromet signals found"]),
            local_alarm_triggered=False,
        )
        session.add(alert)
        return alert

    max_source, max_component, _ = max(weighted_components, key=lambda item: item[1])
    weighted_score = max_component

    supporting_sources = sum(1 for _, score, _ in weighted_components if score >= 0.45)
    if supporting_sources >= 2:
        weighted_score = min(1.0, weighted_score + 0.08 * (supporting_sources - 1))

    level = level_from_score(weighted_score)
    local_alarm_triggered = level in {"orange", "red"}

    summary_parts: list[str] = []
    if latest_node:
        summary_parts.append(
            f"Node ratio {latest_node.waterline_ratio:.2f} ({'crossed' if latest_node.crossed_critical_line else 'below'} critical)"
        )
    if latest_parsed:
        summary_parts.append(latest_parsed.summary)
    if latest_hydromet:
        summary_parts.append(latest_hydromet.summary)

    alert = FusedAlert(
        site_id=site_id,
        level=level,
        score=round(weighted_score, 4),
        trigger_source=max_source,
        summary=" | ".join(summary_parts[:3]),
        decision_trace=json.dumps([item[2] for item in weighted_components] + [f"supporting_sources={supporting_sources}"]),
        local_alarm_triggered=local_alarm_triggered,
    )
    session.add(alert)
    return alert
