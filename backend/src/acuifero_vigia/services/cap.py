from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"
ET.register_namespace("", CAP_NS)


SEVERITY_MAP = {
    "green": "Minor",
    "yellow": "Minor",
    "orange": "Moderate",
    "red": "Severe",
    "info": "Minor",
    "minor": "Minor",
    "moderate": "Moderate",
    "severe": "Severe",
}


def _cap(parent: ET.Element, name: str, text: Any) -> ET.Element:
    child = ET.SubElement(parent, f"{{{CAP_NS}}}{name}")
    child.text = "" if text is None else str(text)
    return child


def build_cap_xml(event: dict[str, Any]) -> str:
    now = event.get("sent") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    identifier = event.get("identifier") or f"acuifero-{hashlib.sha256(repr(event).encode()).hexdigest()[:16]}"
    severity = SEVERITY_MAP.get(str(event.get("severity", "minor")).lower(), "Minor")
    lat = event.get("lat", -34.6037)
    lon = event.get("lon", -58.3816)
    radius = float(event.get("radius_m", 500.0))
    delta = radius / 111320.0
    polygon = event.get("polygon") or (
        f"{lat-delta:.6f},{lon-delta:.6f} {lat-delta:.6f},{lon+delta:.6f} "
        f"{lat+delta:.6f},{lon+delta:.6f} {lat+delta:.6f},{lon-delta:.6f} {lat-delta:.6f},{lon-delta:.6f}"
    )

    alert = ET.Element(f"{{{CAP_NS}}}alert")
    _cap(alert, "identifier", identifier)
    _cap(alert, "sender", event.get("sender", "acuifero-vigia@demo.local"))
    _cap(alert, "sent", now)
    _cap(alert, "status", event.get("status", "Actual"))
    _cap(alert, "msgType", event.get("msgType", "Alert"))
    _cap(alert, "scope", event.get("scope", "Restricted"))
    _cap(alert, "code", "SINAGIR-compatible")
    _cap(alert, "note", "Sistema complementario experimental; no reemplaza canales oficiales SMN/Defensa Civil.")

    info = ET.SubElement(alert, f"{{{CAP_NS}}}info")
    _cap(info, "language", "es-AR")
    _cap(info, "category", "Met")
    _cap(info, "event", event.get("event", "Inundacion"))
    _cap(info, "responseType", "Monitor")
    _cap(info, "urgency", event.get("urgency", "Expected"))
    _cap(info, "severity", severity)
    _cap(info, "certainty", event.get("certainty", "Likely"))
    _cap(info, "senderName", "Acuifero 4 + Vigia")
    _cap(info, "headline", event.get("headline", "Alerta por posible inundacion"))
    _cap(info, "description", event.get("description", event.get("summary", "Senales locales indican riesgo hidrometeorologico.")))
    _cap(info, "instruction", event.get("instruction", "Monitorear el area y validar con Defensa Civil antes de difusion publica."))
    _cap(info, "web", event.get("web", "https://www.argentina.gob.ar/sinagir"))

    signature = hashlib.sha256(ET.tostring(alert, encoding="utf-8")).hexdigest()
    parameter = ET.SubElement(info, f"{{{CAP_NS}}}parameter")
    _cap(parameter, "valueName", "acuifero-signature-sha256")
    _cap(parameter, "value", signature)

    area = ET.SubElement(info, f"{{{CAP_NS}}}area")
    _cap(area, "areaDesc", event.get("areaDesc", event.get("site_id", "Area operativa Acuifero Vigia")))
    _cap(area, "polygon", polygon)
    geocode = ET.SubElement(area, f"{{{CAP_NS}}}geocode")
    _cap(geocode, "valueName", "SINAGIR/SINAME sitio")
    _cap(geocode, "value", event.get("site_id", "demo-site"))
    return ET.tostring(alert, encoding="utf-8", xml_declaration=True).decode("utf-8")


def write_cap_sample(path: str | Path) -> None:
    sample = build_cap_xml(
        {
            "site_id": "demo-arroyo",
            "lat": -34.6037,
            "lon": -58.3816,
            "severity": "moderate",
            "headline": "Alerta preventiva por crecida en arroyo",
            "instruction": "Evitar cruces bajos y reportar cambios a Defensa Civil municipal.",
            "summary": "Nodo visual y reporte ciudadano coinciden dentro de la ventana operativa.",
        }
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(sample, encoding="utf-8")
