import { useEffect, useState } from 'react';
import { API_BASE } from '../store';
import { CheckCircle2, Cpu, ServerCrash, Waves } from 'lucide-react';

interface RuntimeStatus {
  is_online: boolean;
  llm: {
    enabled: boolean;
    reachable: boolean;
    base_url: string;
    model: string;
    detail: string;
  };
  acuifero?: {
    node_profile: string;
    data_dir: string;
    multimodal_enabled: boolean;
    multimodal_verifier_enabled: boolean;
    multimodal_base_url: string;
    multimodal_model: string;
    multimodal_min_interval_seconds: number;
    multimodal_score_threshold: number;
    multimodal_confidence_threshold: number;
    multimodal_image_max_side: number;
    multimodal_num_ctx: number;
    multimodal_timeout_seconds: number;
    max_curated_frames: number;
    artifact_retention_days: number;
  };
  hydromet: {
    enabled: boolean;
    reachable: boolean;
    detail: string;
  };
}

export default function Settings() {
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRuntime = async () => {
      try {
        const response = await fetch(`${API_BASE}/settings/runtime`);
        if (!response.ok) {
          throw new Error(await response.text());
        }
        setRuntime(await response.json());
      } catch (loadError) {
        console.error(loadError);
        setError('Could not load runtime status.');
      }
    };

    loadRuntime();
  }, []);

  return (
    <div className="space-y-6 pb-20">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Runtime Status</h2>
        <p className="text-sm text-gray-500 mt-1">
          Fixed Acuifero node runtime plus live hydromet enrichment.
        </p>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600" /> Gemma runtime
          </h3>
          {runtime ? (
            <div className="mt-4 space-y-3 text-sm text-gray-700">
              <div className="flex items-center gap-2">
                {runtime.llm.reachable ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <ServerCrash className="w-4 h-4 text-red-600" />}
                <span>{runtime.llm.reachable ? 'LLM endpoint reachable' : 'LLM endpoint not reachable'}</span>
              </div>
              <div><span className="text-gray-500">Enabled:</span> {runtime.llm.enabled ? 'Yes' : 'No'}</div>
              <div><span className="text-gray-500">Base URL:</span> {runtime.llm.base_url}</div>
              <div><span className="text-gray-500">Model:</span> {runtime.llm.model}</div>
              <div><span className="text-gray-500">Detail:</span> {runtime.llm.detail}</div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-gray-500">Loading runtime status...</p>
          )}
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Waves className="w-5 h-5 text-cyan-600" /> Hydromet provider
          </h3>
          {runtime ? (
            <div className="mt-4 space-y-3 text-sm text-gray-700">
              <div className="flex items-center gap-2">
                {runtime.hydromet.reachable ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <ServerCrash className="w-4 h-4 text-red-600" />}
                <span>{runtime.hydromet.reachable ? 'Provider reachable' : 'Provider not reachable'}</span>
              </div>
              <div><span className="text-gray-500">Enabled:</span> {runtime.hydromet.enabled ? 'Yes' : 'No'}</div>
              <div><span className="text-gray-500">Detail:</span> {runtime.hydromet.detail}</div>
              <div><span className="text-gray-500">Backend connectivity toggle:</span> {runtime.is_online ? 'Online' : 'Offline'}</div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-gray-500">Loading provider status...</p>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm space-y-4">
        <h3 className="font-semibold text-gray-900">Acuifero fixed-node setup</h3>
        <p className="text-sm text-gray-600">
          The fixed Acuifero node targets Raspberry Pi 5 with 8 GB RAM, SSD-backed local data, a compact text-first Gemma guard,
          and an occasional Gemma 4 multimodal verifier over one curated frame.
          Vigia is a separate volunteer/user node.
        </p>
        {runtime?.acuifero && (
          <div className="grid gap-3 text-sm text-gray-700 sm:grid-cols-2">
            <div><span className="text-gray-500">Node profile:</span> {runtime.acuifero.node_profile}</div>
            <div className="break-all"><span className="text-gray-500">Data dir:</span> {runtime.acuifero.data_dir}</div>
            <div><span className="text-gray-500">Primary multimodal:</span> {runtime.acuifero.multimodal_enabled ? 'Enabled' : 'Disabled'}</div>
            <div><span className="text-gray-500">Verifier:</span> {runtime.acuifero.multimodal_verifier_enabled ? 'Enabled' : 'Disabled'}</div>
            <div className="break-all"><span className="text-gray-500">Verifier URL:</span> {runtime.acuifero.multimodal_base_url}</div>
            <div><span className="text-gray-500">Verifier model:</span> {runtime.acuifero.multimodal_model}</div>
            <div><span className="text-gray-500">Verifier cadence:</span> {runtime.acuifero.multimodal_min_interval_seconds}s</div>
            <div><span className="text-gray-500">Verifier score trigger:</span> {runtime.acuifero.multimodal_score_threshold.toFixed(2)}</div>
            <div><span className="text-gray-500">Verifier confidence trigger:</span> {runtime.acuifero.multimodal_confidence_threshold.toFixed(2)}</div>
            <div><span className="text-gray-500">Verifier image max side:</span> {runtime.acuifero.multimodal_image_max_side}px</div>
            <div><span className="text-gray-500">Verifier context:</span> {runtime.acuifero.multimodal_num_ctx} tokens</div>
            <div><span className="text-gray-500">Curated frames:</span> {runtime.acuifero.max_curated_frames}</div>
            <div><span className="text-gray-500">Artifact retention:</span> {runtime.acuifero.artifact_retention_days} days</div>
          </div>
        )}
        <pre className="overflow-x-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-100">
{`ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-hybrid
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_LLM_ENABLED=true
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
ACUIFERO_MULTIMODAL_ENABLED=false
ACUIFERO_MULTIMODAL_VERIFIER_ENABLED=true
ACUIFERO_MULTIMODAL_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_MULTIMODAL_MODEL=gemma4:e2b
ACUIFERO_MULTIMODAL_MIN_INTERVAL_SECONDS=300
ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=768
ACUIFERO_MULTIMODAL_NUM_CTX=2048
ACUIFERO_MULTIMODAL_TIMEOUT_SECONDS=180
ACUIFERO_MAX_CURATED_FRAMES=3
ACUIFERO_ARTIFACT_RETENTION_DAYS=7`}
        </pre>
        <p className="text-sm text-gray-600">
          Use `./scripts/run_acuifero_pi8_hybrid.sh` from the repo root to start Ollama, pull the selected Gemma 4 model, seed the edge DB, and run the API.
          If the local model is down, Acuifero keeps producing a deterministic fixed-node assessment from the temporal evidence builder.
        </p>
      </section>
    </div>
  );
}
