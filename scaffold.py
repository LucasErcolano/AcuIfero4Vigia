import os
from pathlib import Path

dirs = [
    "backend/src/acuifero_vigia/api",
    "backend/src/acuifero_vigia/core",
    "backend/src/acuifero_vigia/db",
    "backend/src/acuifero_vigia/models",
    "backend/src/acuifero_vigia/schemas",
    "backend/src/acuifero_vigia/services",
    "backend/src/acuifero_vigia/adapters",
    "backend/src/acuifero_vigia/utils",
    "backend/data",
    "backend/tests",
    "frontend",
    "shared/schemas",
    "fixtures/media",
    "fixtures/generated",
    "scripts",
    "docs"
]

files = [
    "backend/data/.gitkeep",
    "backend/src/acuifero_vigia/__init__.py",
    "backend/src/acuifero_vigia/main.py",
    "backend/pyproject.toml",
    "shared/schemas/volunteer-report.schema.json",
    "shared/schemas/node-event.schema.json",
    "shared/schemas/fused-alert.schema.json",
    "scripts/setup.ps1",
    "scripts/dev.ps1",
    "scripts/seed.ps1",
    "scripts/demo.ps1",
    "docs/architecture.md",
    "docs/demo-script.md",
    "docs/edge-notes.md",
    "README.md"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

for f in files:
    Path(f).touch(exist_ok=True)

print("Scaffolding complete.")
