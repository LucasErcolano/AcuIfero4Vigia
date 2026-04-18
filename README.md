# Acuifero 4 + Vigia

A hybrid flood early-warning MVP that combines a fixed river/bridge monitoring node (Acuifero 4) with a mobile-friendly offline-first volunteer reporting app (Vigia). The system operates on a shared local decision engine, enabling offline-capable alert generation and resilient edge-to-central data synchronization, ensuring that even when the internet fails, local observations and local actions still work seamlessly.

## Architecture

```
[ Fixed Node ] --(Video/Images)--> [ FastAPI Backend (Acuifero) ]
                                            |
[ Volunteer App ] --(Reports/Offline)--> [ SQLite (edge.db) ] --> [ Sync Queue ] --> [ Central.db ]
(Vigia / PWA)                               |
                                      [ Decision Engine ]
                                            |
                                      [ Local Alarms ]
```

## Local Setup

1. **Prerequisites:** Python 3.12+, Node.js (v24+), and npm installed. The build uses `uv` for python dependencies.
2. **Run the Setup Script with execution-policy bypass for this session:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
   ```
   This will scaffold the Python environment, install frontend dependencies, and seed the local SQLite databases.
3. **Start the Dev Servers:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
   ```
   The script launches the backend and frontend as separate processes and prints their PIDs. The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:5173`.

If you prefer, you can first run `Set-ExecutionPolicy -Scope Process Bypass` in the current terminal and then call the scripts normally.

## Demo Flow Steps

1. Run the `setup.ps1` and `dev.ps1` scripts in two separate terminals.
2. In a third terminal, run the automated demo script to simulate the full lifecycle:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\demo.ps1
   ```
   The demo is a backend-only smoke script and assumes the API is already running on `http://localhost:8000`.
3. **Manual Flow:**
   - Open the web app at `http://localhost:5173`.
   - Go to the "Report" page.
   - Toggle "Offline Mode" in the header to simulate a connectivity loss.
   - Submit a test observation with the transcript "El agua paso la marca critica".
   - The report will be saved to the IndexedDB offline queue.
   - Go to the "Queue" page to view pending reports.
   - Toggle the network back to "Online Mode" and click "Sync Now" to flush the queue to the backend and then to `central.db`.

## Known Limitations

- **Computer Vision:** Currently using a mocked representation for the MVP due to hardware constraints. Future versions will integrate OpenCV heuristic algorithms and temporal median smoothing.
- **Audio Processing:** ASR model (Whisper/Faster-Whisper) is prepared in the backend requirements but disabled by default to prioritize quick startup.
- **Actuators:** Local alarms are simulated via server terminal prints rather than actual GPIO output.
- **Central DB Sync:** Sync simulation writes locally to `central.db` instead of remote servers.

## Future AI Edge Integration Notes

The codebase is designed with adapter hooks for later Google AI Edge / LiteRT-LM deployment.
- **Text Structuring:** `RuleBasedTextStructuringAdapter` can be replaced with `FunctionGemma 270M` for advanced tool-calling and offline JSON serialization.
- **Inference Strategy:** `Gemma 4 E2B` could replace the rule-based logic for advanced heuristic text analysis without needing an external API if memory limitations on the target device are bypassed.
- **Video Analysis:** Advanced multimodality models might replace the CPU-bound classical OpenCV if a GPU pipeline becomes available.
