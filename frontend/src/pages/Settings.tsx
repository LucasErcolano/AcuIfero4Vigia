import { useEffect, useState } from 'react';
import { API_BASE, useAppStore } from '../store';
import { CheckCircle2, Cpu, ServerCrash, UploadCloud, Waves } from 'lucide-react';

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
    provider: string;
    backend: string;
    vision_backend: string;
    engine_ready: boolean;
    engine_detail: string;
    model_path: string;
    cache_dir: string;
    data_dir: string;
    multimodal_enabled: boolean;
    multimodal_verifier_enabled: boolean;
    multimodal_base_url: string;
    multimodal_model: string;
    multimodal_min_interval_seconds: number;
    multimodal_score_threshold: number;
    multimodal_confidence_threshold: number;
    multimodal_image_max_side: number;
    multimodal_max_frames: number;
    multimodal_frame_sample_seconds: number;
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
  const { syncStatus, fetchSyncStatus, flushQueue, queueCount } = useAppStore();
  const [isFlushing, setIsFlushing] = useState(false);

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
    fetchSyncStatus();
    const interval = setInterval(fetchSyncStatus, 8000);
    return () => clearInterval(interval);
  }, [fetchSyncStatus]);

  const onFlush = async () => {
    setIsFlushing(true);
    try {
      await flushQueue();
      await fetchSyncStatus();
    } finally {
      setIsFlushing(false);
    }
  };

  const acuiferoReadyLabel = runtime?.acuifero?.provider === 'ollama'
    ? 'Ollama dev runtime ready'
    : 'LiteRT runtime ready';
  const acuiferoNotReadyLabel = runtime?.acuifero?.provider === 'ollama'
    ? 'Ollama dev runtime not ready'
    : 'LiteRT runtime not ready';

  return (
    <div className="space-y-6 pb-20">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Runtime Status</h2>
        <p className="text-sm text-gray-500 mt-1">
          Fixed Acuifero node runtime plus live hydromet enrichment.
        </p>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-blue-600" /> Sync status
          </h3>
          <button
            onClick={onFlush}
            disabled={isFlushing || queueCount === 0}
            className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isFlushing ? 'Flushing...' : `Flush queue (${queueCount})`}
          </button>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3">
            <div className="text-xs uppercase tracking-wide text-yellow-700 font-semibold">Pending</div>
            <div className="mt-1 text-xl font-bold text-yellow-900">{syncStatus?.pending ?? 0}</div>
          </div>
          <div className="rounded-lg border border-green-200 bg-green-50 p-3">
            <div className="text-xs uppercase tracking-wide text-green-700 font-semibold">Sincronizado</div>
            <div className="mt-1 text-xl font-bold text-green-900">{syncStatus?.synced ?? 0}</div>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <div className="text-xs uppercase tracking-wide text-red-700 font-semibold">Failed</div>
            <div className="mt-1 text-xl font-bold text-red-900">{syncStatus?.failed ?? 0}</div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600" /> Vigia / dev runtime
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
          The fixed Acuifero node now targets an embedded LiteRT-LM runtime with Gemma 4 E2B. The Pi 8 profile is a minimum
          demo with one small frame every few minutes; the Pi 16/prod profile uses more frames and context. `ACUIFERO_NODE_PROVIDER=ollama`
          remains a development-only Acuifero path plus the standard Vigia/local experimentation path.
        </p>
        {runtime?.acuifero && (
          <div className="grid gap-3 text-sm text-gray-700 sm:grid-cols-2">
            <div><span className="text-gray-500">Node profile:</span> {runtime.acuifero.node_profile}</div>
            <div><span className="text-gray-500">Provider:</span> {runtime.acuifero.provider}</div>
            <div><span className="text-gray-500">Backend:</span> {runtime.acuifero.backend}</div>
            <div><span className="text-gray-500">Vision backend:</span> {runtime.acuifero.vision_backend}</div>
            <div className="flex items-center gap-2">
              {runtime.acuifero.engine_ready ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <ServerCrash className="w-4 h-4 text-red-600" />}
              <span>{runtime.acuifero.engine_ready ? acuiferoReadyLabel : acuiferoNotReadyLabel}</span>
            </div>
            <div className="break-all"><span className="text-gray-500">Model path:</span> {runtime.acuifero.model_path}</div>
            <div className="break-all"><span className="text-gray-500">Cache dir:</span> {runtime.acuifero.cache_dir}</div>
            <div className="break-all"><span className="text-gray-500">Data dir:</span> {runtime.acuifero.data_dir}</div>
            <div><span className="text-gray-500">Gemma multimodal:</span> {runtime.acuifero.multimodal_enabled ? 'Enabled' : 'Disabled'}</div>
            <div className="break-all"><span className="text-gray-500">Dev multimodal URL:</span> {runtime.acuifero.multimodal_base_url}</div>
            <div><span className="text-gray-500">Multimodal model:</span> {runtime.acuifero.multimodal_model}</div>
            <div><span className="text-gray-500">Frames per analysis:</span> {runtime.acuifero.multimodal_max_frames}</div>
            <div><span className="text-gray-500">Frame sample spacing:</span> {runtime.acuifero.multimodal_frame_sample_seconds}s</div>
            <div><span className="text-gray-500">Image max side:</span> {runtime.acuifero.multimodal_image_max_side}px</div>
            <div><span className="text-gray-500">Context:</span> {runtime.acuifero.multimodal_num_ctx} tokens</div>
            <div><span className="text-gray-500">Timeout:</span> {runtime.acuifero.multimodal_timeout_seconds}s</div>
            <div><span className="text-gray-500">Curated frames:</span> {runtime.acuifero.max_curated_frames}</div>
            <div><span className="text-gray-500">Artifact retention:</span> {runtime.acuifero.artifact_retention_days} days</div>
          </div>
        )}
        <pre className="overflow-x-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-100">
{`ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-multimodal-demo
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_NODE_PROVIDER=litert
ACUIFERO_NODE_MODEL_PATH=backend/data/models/gemma-4-E2B-it.litertlm
ACUIFERO_NODE_BACKEND=cpu
ACUIFERO_NODE_VISION_BACKEND=cpu
ACUIFERO_NODE_CACHE_DIR=backend/data/litert-cache
ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=false
ACUIFERO_NODE_MAX_OUTPUT_TOKENS=256
ACUIFERO_MULTIMODAL_ENABLED=true
ACUIFERO_MULTIMODAL_VERIFIER_ENABLED=false
ACUIFERO_MULTIMODAL_MODEL=gemma-4-E2B-it.litertlm
ACUIFERO_MULTIMODAL_MAX_FRAMES=1
ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=300
ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512
ACUIFERO_MULTIMODAL_NUM_CTX=1024
ACUIFERO_MULTIMODAL_TIMEOUT_SECONDS=300
ACUIFERO_MAX_CURATED_FRAMES=1
ACUIFERO_ARTIFACT_RETENTION_DAYS=3`}
        </pre>
        <p className="text-sm text-gray-600">
          Use `./scripts/run_acuifero_pi8_multimodal_demo.sh` for the Pi 8 demo or `./scripts/run_acuifero_pi16_multimodal_prod.sh`
          for the production profile. If the embedded model is unavailable, Acuifero records the prepared frames and returns a
          conservative manual-review fallback instead of silently switching to Ollama.
        </p>
      </section>
    </div>
  );
}
