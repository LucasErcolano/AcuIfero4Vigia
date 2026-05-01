"""Auditable thinking-mode chain for FusedAlert severity decisions.

Runs a Spanish-language prompt through the local Gemma endpoint and produces a
ReasoningBlock that accompanies the deterministic decision_trace. Green alerts
skip the LLM (cost/latency). If Ollama is down, a rule-fallback summary is
generated so alert emission never blocks on model availability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from acuifero_vigia.adapters.llm import OpenAICompatibleLLM


@dataclass
class ReasoningBlock:
    llm_summary: str
    llm_chain_of_thought: list[str] = field(default_factory=list)
    model_name: str = "rule-fallback"


SYSTEM_PROMPT_ES = (
    "Sos un analista del sistema de alerta temprana de inundaciones "
    "Acuifero 4 + Vigia. Tu tarea es producir una explicacion auditable en "
    "espanol rioplatense sobre por que se emitio una alerta con cierto nivel "
    "de severidad. Siempre nombra las senales concretas por su nombre "
    "(waterline_ratio, rise_velocity, crossed_critical_line, water_level_category, "
    "trend, road_status, bridge_status, hydromet) y escribi en 2 a 3 oraciones. "
    "No inventes datos que no esten en el contexto. No uses markdown."
)


def _render_inputs(
    node_obs: Optional[dict[str, Any]],
    volunteer_parsed: Optional[dict[str, Any]],
    hydromet: Optional[dict[str, Any]],
    fused_score: float,
    level: str,
    rules_fired: list[str],
) -> str:
    parts: list[str] = []
    parts.append(f"Nivel fusionado: {level} (score={fused_score:.2f}).")
    if node_obs:
        parts.append(
            "Nodo fijo: "
            f"waterline_ratio={node_obs.get('waterline_ratio', 0):.2f}, "
            f"rise_velocity={node_obs.get('rise_velocity', 0):.2f}, "
            f"crossed_critical_line={node_obs.get('crossed_critical_line', False)}, "
            f"confidence={node_obs.get('confidence', 0):.2f}."
        )
        if node_obs.get("temporal_summary"):
            parts.append(f"Resumen temporal nodo: {node_obs.get('temporal_summary')}.")
        if node_obs.get("runner_name"):
            parts.append(
                f"Runner nodo: {node_obs.get('runner_name')} modo={node_obs.get('runner_mode', 'unknown')}, "
                f"fallback={node_obs.get('fallback_used', False)}."
            )
    else:
        parts.append("Nodo fijo: sin observaciones recientes.")
    if volunteer_parsed:
        parts.append(
            "Reporte voluntario: "
            f"water_level_category={volunteer_parsed.get('water_level_category', 'unknown')}, "
            f"trend={volunteer_parsed.get('trend', 'unknown')}, "
            f"road_status={volunteer_parsed.get('road_status', 'unknown')}, "
            f"bridge_status={volunteer_parsed.get('bridge_status', 'unknown')}, "
            f"urgency={volunteer_parsed.get('urgency', 'unknown')}."
        )
    else:
        parts.append("Reporte voluntario: no hay reportes recientes.")
    if hydromet:
        parts.append(
            "Hidromet: "
            f"precipitacion_mm={hydromet.get('precipitation_mm', 0):.1f}, "
            f"caudal={hydromet.get('river_discharge', 'NA')}, "
            f"tendencia={hydromet.get('river_discharge_trend', 'NA')}."
        )
    if rules_fired:
        parts.append("Reglas deterministicas: " + "; ".join(rules_fired) + ".")
    parts.append(
        "Produci dos o tres oraciones que expliquen por que este nivel, "
        "citando al menos dos senales concretas. Luego, en una linea aparte "
        "comenzada con 'Cadena:', listar 2 o 3 pasos de razonamiento separados por ' -> '."
    )
    return "\n".join(parts)


def _parse_llm_output(raw: str) -> tuple[str, list[str]]:
    summary = raw.strip()
    chain: list[str] = []
    if "Cadena:" in summary:
        head, _, tail = summary.partition("Cadena:")
        summary = head.strip()
        chain = [step.strip() for step in tail.split("->") if step.strip()]
    if not chain:
        # Split into up-to-3 sentence-like fragments as a coarse CoT surrogate.
        pieces = [p.strip() for p in summary.replace("\n", " ").split(".") if p.strip()]
        chain = pieces[:3]
    return summary, chain[:5]


def _fallback(level: str, rules_fired: list[str]) -> ReasoningBlock:
    rules = rules_fired or ["sin reglas deterministicas disparadas"]
    summary = (
        f"Alerta {level} emitida por regla local. "
        f"Senales activas: {', '.join(rules[:3])}. "
        "Gemma no disponible, se usa resumen deterministico."
    )
    return ReasoningBlock(
        llm_summary=summary,
        llm_chain_of_thought=rules[:3],
        model_name="rule-fallback",
    )


def generate_alert_reasoning(
    level: str,
    fused_score: float,
    node_obs: Optional[dict[str, Any]],
    volunteer_parsed: Optional[dict[str, Any]],
    hydromet: Optional[dict[str, Any]],
    rules_fired: list[str],
    llm: Optional[OpenAICompatibleLLM] = None,
) -> ReasoningBlock:
    """Produce a Spanish reasoning block for an alert.

    Green alerts return an empty-ish block with only a rule-based single-line
    summary (no LLM call). Yellow/orange/red call the LLM with a deterministic
    fallback.
    """
    if level == "green":
        return ReasoningBlock(
            llm_summary="Nivel verde: no se supera umbral de riesgo. No se invoca Gemma.",
            llm_chain_of_thought=["sin senales sobre umbral"],
            model_name="rule-skip-green",
        )

    if llm is None:
        return _fallback(level, rules_fired)

    user_prompt = _render_inputs(node_obs, volunteer_parsed, hydromet, fused_score, level, rules_fired)
    raw = llm.generate_text(SYSTEM_PROMPT_ES, user_prompt, max_tokens=320)
    if not raw:
        return _fallback(level, rules_fired)

    summary, chain = _parse_llm_output(raw)
    if not summary:
        return _fallback(level, rules_fired)

    return ReasoningBlock(
        llm_summary=summary,
        llm_chain_of_thought=chain,
        model_name=llm.settings.llm_model,
    )


def serialize_chain(chain: list[str]) -> str:
    return json.dumps(chain, ensure_ascii=True)


def deserialize_chain(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in value] if isinstance(value, list) else []
