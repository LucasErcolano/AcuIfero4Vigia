from __future__ import annotations

import json
from typing import Optional

from sqlmodel import Session, select

from acuifero_vigia.adapters.llm import OpenAICompatibleLLM
from acuifero_vigia.models.domain import (
    FusedAlert,
    HydrometSnapshot,
    NodeObservation,
    ParsedObservation,
    VolunteerReport,
)
from acuifero_vigia.services.reasoning import generate_alert_reasoning, serialize_chain



def level_from_score(score: float) -> str:
    if score >= 0.82:
        return "red"
    if score >= 0.62:
        return "orange"
    if score >= 0.4:
        return "yellow"
    return "green"



def recompute_site_alert(
    session: Session,
    site_id: str,
    llm: Optional[OpenAICompatibleLLM] = None,
) -> FusedAlert:
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
        reasoning = generate_alert_reasoning(
            level="green",
            fused_score=0.0,
            node_obs=None,
            volunteer_parsed=None,
            hydromet=None,
            rules_fired=["Sin senales recientes"],
            llm=None,
        )
        alert = FusedAlert(
            site_id=site_id,
            level="green",
            score=0.0,
            trigger_source="fused",
            summary="No recent signals available",
            decision_trace=json.dumps(["No node, volunteer, or hydromet signals found"]),
            local_alarm_triggered=False,
            reasoning_summary=reasoning.llm_summary,
            reasoning_chain=serialize_chain(reasoning.llm_chain_of_thought),
            reasoning_model=reasoning.model_name,
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

    rules_fired = [item[2] for item in weighted_components] + [f"supporting_sources={supporting_sources}"]

    node_snapshot = {
        "waterline_ratio": latest_node.waterline_ratio,
        "rise_velocity": latest_node.rise_velocity,
        "crossed_critical_line": latest_node.crossed_critical_line,
        "confidence": latest_node.confidence,
    } if latest_node else None
    volunteer_snapshot = {
        "water_level_category": latest_parsed.water_level_category,
        "trend": latest_parsed.trend,
        "road_status": latest_parsed.road_status,
        "bridge_status": latest_parsed.bridge_status,
        "urgency": latest_parsed.urgency,
        "summary": latest_parsed.summary,
    } if latest_parsed else None
    hydromet_snapshot = {
        "precipitation_mm": latest_hydromet.precipitation_mm,
        "river_discharge": latest_hydromet.river_discharge,
        "river_discharge_trend": latest_hydromet.river_discharge_trend,
    } if latest_hydromet else None

    reasoning = generate_alert_reasoning(
        level=level,
        fused_score=weighted_score,
        node_obs=node_snapshot,
        volunteer_parsed=volunteer_snapshot,
        hydromet=hydromet_snapshot,
        rules_fired=rules_fired,
        llm=llm if level != "green" else None,
    )

    alert = FusedAlert(
        site_id=site_id,
        level=level,
        score=round(weighted_score, 4),
        trigger_source=max_source,
        summary=" | ".join(summary_parts[:3]),
        decision_trace=json.dumps(rules_fired),
        local_alarm_triggered=local_alarm_triggered,
        reasoning_summary=reasoning.llm_summary,
        reasoning_chain=serialize_chain(reasoning.llm_chain_of_thought),
        reasoning_model=reasoning.model_name,
    )
    session.add(alert)
    return alert
