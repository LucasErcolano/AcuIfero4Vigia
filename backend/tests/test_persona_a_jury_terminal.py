from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[2] / "docs" / "demo" / "persona_a_jury_terminal.py"


def load_module():
    spec = importlib.util.spec_from_file_location("persona_a_jury_terminal", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_dry_run_prints_jury_safe_terminal_output_in_order(capsys, monkeypatch):
    module = load_module()

    def fail_request(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("dry-run must not call backend")

    def fail_smoke(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("dry-run must not call smoke")

    monkeypatch.setattr(module, "request_json", fail_request)
    monkeypatch.setattr(module, "run_real_smoke", fail_smoke)

    assert module.main(["--dry-run", "--no-pace"]) == 0

    output = capsys.readouterr().out
    expected = [
        "PERSONA A - Acuifero edge node",
        "REAL Raspberry Pi 5 - LiteRT-LM",
        "STEP 0 - Real edge hardware",
        "STEP 1 - Runtime identity",
        "STEP 2 - Backend health + runtime config",
        "STEP 3 - Node-analysis proof",
        "STEP 4 - Real Pi LiteRT smoke",
        "STEP 5 - Handoff to Persona C",
    ]
    positions = [output.index(text) for text in expected]
    assert positions == sorted(positions)

    assert "host                 : raspi5" in output
    assert "board                : Raspberry Pi 5 Model B Rev 1.1" in output
    assert "memory               : 7.9 GiB total / 7.3 GiB available" in output
    assert "model file           : gemma-4-E2B-it.litertlm (2.5G)" in output
    assert "litert_lm import     : ok" in output
    assert "provider             : litert" in output
    assert "compute              : text=gpu / image=cpu/cpu" in output
    assert "multimodal_backend   : cpu" in output
    assert "vision_backend       : cpu" in output
    assert "runner.mode          : litert-multimodal-temporal" in output
    assert "assessment_mode      : gemma4-multimodal-v1" in output
    assert "frames_analyzed      : 1" in output
    assert "elapsed_seconds      : 253.81" in output
    assert "rss_mb               : 3128.4" in output
    assert "Persona C Acto 2 uses synchronized cam=52 demo payload." in output
    assert "This Pi run validates the real edge LiteRT runtime behind that narrative." in output
    assert "{" not in output
    assert "}" not in output

    blocked_terms = [
        "git status",
        "branch",
        "branches",
        "worktree",
        "untracked",
        "VM",
        "RTX 3060",
        "OpenCV",
        "E4B",
        "TTFT",
        "tok/s",
        "streaming",
        "accuracy",
        "lead time",
        "chain_of_thought",
        "WARNING",
        "OpenCL",
        "stderr",
    ]
    for term in blocked_terms:
        assert term not in output


def test_smoke_stdout_parser_extracts_only_curated_benchmark_fields():
    module = load_module()

    stdout = "\n".join(
        [
            "not json noise",
            '{"health":{"reachable":true,"detail":"hidden"}}',
            '{"result":{"reasoning_steps":["hidden"]},"benchmark":{"elapsed_seconds":350.184,"rss_mb":3120.04,"backend":"gpu","multimodal_backend":"cpu","multimodal_vision_backend":"cpu","model":"backend/data/models/gemma-4-E2B-it.litertlm"}}',
        ]
    )

    smoke = module.smoke_from_stdout(stdout, returncode=0)

    assert smoke.status == "passed"
    assert smoke.elapsed_seconds == "350.18"
    assert smoke.rss_mb == "3120.0"
    assert smoke.backend == "gpu"
    assert smoke.multimodal_backend == "cpu"
    assert smoke.multimodal_vision_backend == "cpu"
    assert smoke.model == "gemma-4-E2B-it.litertlm"


def test_backend_runtime_parser_exposes_only_curated_fields():
    module = load_module()
    payload = {
        "acuifero": {
            "provider": "litert",
            "backend": "gpu",
            "multimodal_backend": "cpu",
            "multimodal_vision_backend": "cpu",
            "speculative_decoding": True,
            "engine_ready": True,
            "p1_runtime_ready": True,
            "engine_detail": "do not expose",
            "model_path": "/tmp/private/model.litertlm",
        }
    }

    status = module.backend_from_payload(payload)

    assert status.status == "ok"
    assert status.provider == "litert"
    assert status.backend == "gpu"
    assert status.multimodal_backend == "cpu"
    assert status.multimodal_vision_backend == "cpu"
    assert status.speculative_decoding == "true"
    assert status.engine_ready == "true"
    assert status.p1_runtime_ready == "true"
    assert not hasattr(status, "engine_detail")
    assert not hasattr(status, "model_path")


def test_cast_writer_emits_valid_asciinema_v2(tmp_path, capsys):
    module = load_module()
    cast_path = tmp_path / "take.cast"

    assert module.main(["--dry-run", "--no-pace", "--cast-out", str(cast_path)]) == 0
    capsys.readouterr()

    lines = cast_path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    first_event = json.loads(lines[1])
    last_event = json.loads(lines[-1])
    event_text = "\n".join(json.loads(line)[2] for line in lines[1:])

    assert header["version"] == 2
    assert header["width"] == 80
    assert header["height"] == 24
    assert first_event[1] == "o"
    assert "PERSONA A - Acuifero edge node" in event_text
    assert last_event[0] > first_event[0]
    assert "This Pi run validates the real edge LiteRT runtime behind that narrative." in last_event[2]


def test_model_size_format_matches_jury_take_rounding(tmp_path):
    module = load_module()
    model = tmp_path / "gemma-4-E2B-it.litertlm"
    with model.open("wb") as handle:
        handle.truncate(2_588_147_712)

    assert module.format_size(model) == "2.5G"
