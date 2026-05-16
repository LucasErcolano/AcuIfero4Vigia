from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = PROJECT_ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from acuifero_vigia.adapters.litert_node import LiteRTNodeRuntime


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a LiteRT-LM smoke prompt for the Acuifero node.")
    parser.add_argument(
        "--prompt",
        default="Responde solo JSON valido: {\"status\":\"ok\",\"engine\":\"litert\"}",
        help="Prompt to send to the model",
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Optional image path for a multimodal smoke prompt",
    )
    args = parser.parse_args()

    runtime = LiteRTNodeRuntime()
    health = runtime.health()
    print(json.dumps(health.__dict__, ensure_ascii=True))

    if not health.reachable:
        raise SystemExit("LiteRT runtime is not ready")

    if args.image is not None:
        result = runtime.generate_multimodal_json(
            "Responde solo JSON valido.",
            args.prompt,
            [args.image],
        )
    else:
        result = runtime.generate_text(
            "Responde de forma breve.",
            args.prompt,
        )

    print(json.dumps({"result": result}, ensure_ascii=True, default=str))


if __name__ == "__main__":
    main()
