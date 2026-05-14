"""Compatibility module for older imports.

The fixed Acuifero node no longer runs an OpenCV heuristic analyzer. Use
`services.acuifero_assessment.MultimodalEvidenceBuilder` plus the Gemma 4
multimodal runner instead.
"""

from acuifero_vigia.services.acuifero_assessment import AcuiferoAssessmentEngine, MultimodalEvidenceBuilder


__all__ = ["AcuiferoAssessmentEngine", "MultimodalEvidenceBuilder"]
