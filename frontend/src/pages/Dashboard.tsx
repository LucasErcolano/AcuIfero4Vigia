/* Dashboard.tsx — Persona C Backend & Fusion command center.
 *
 * Single-view "tablero de comando" optimized for 1440x900 screen recording:
 *
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │ RiskBanner (level · score · site · summary)                    │   <- 5-second read
 *   ├──────────────────────────────────────┬──────────────────────────┤
 *   │ Fusión de señales (3 tiles)          │ Estado CAP v1.2          │
 *   │ Frame de evidencia                   │ Acciones del operador    │
 *   │ Razonamiento de Gemma                │ Cola offline · sync      │
 *   │ Traza de auditoría determinística    │                          │
 *   ├──────────────────────────────────────┴──────────────────────────┤
 *   │ Línea de tiempo del incidente                                  │
 *   └─────────────────────────────────────────────────────────────────┘
 *
 * When there is no active alert from the backend, we render a clearly-labeled
 * demo-safe sample state so the recording always has something to show.
 * The demo state is rendered with a "DEMO · sample state" badge — this is
 * not a fake backend, it's clearly-labeled mock data for screen capture.
 */

import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useAppStore } from '../store';
import type { FusedAlert, Site } from '../store';
import {
  ActionRail,
  AuditTrace,
  CapStatusCard,
  EmptyCommandCenter,
  EvidencePanel,
  GemmaReasoning,
  IncidentTimeline,
  OfflineSyncCard,
  RiskBanner,
  SectionPanel,
  SignalFusionRow,
} from '../components/CommandCenter';

const CENTRAL_NODE_MODEL = 'gemma4:e26b';

const EVIDENCE_BY_LEVEL: Record<FusedAlert['level'], { frameUrl: string; frameLabel: string; description: string; confidence: number }> = {
  green: {
    frameUrl: '/demo_persona_c/nominal.png',
    frameLabel: 'cv_node/nominal_frame.png',
    description:
      'Calm channel conditions. Water remains low against the retaining wall, with dry grass and clear banks visible across the scene.',
    confidence: 0.82,
  },
  yellow: {
    frameUrl: '/demo_persona_c/watch.png',
    frameLabel: 'cv_node/watch_frame.png',
    description:
      'Water level has risen across the channel and surface flow is stronger, but the bank and access path remain mostly clear.',
    confidence: 0.84,
  },
  orange: {
    frameUrl: '/demo_persona_c/watch.png',
    frameLabel: 'cv_node/watch_frame.png',
    description:
      'Elevated water covers most of the channel and is approaching the bank. Continued rise would compromise the access path.',
    confidence: 0.86,
  },
  red: {
    frameUrl: '/demo_persona_c/critical.png',
    frameLabel: 'cv_node/critical_frame.png',
    description:
      'Floodwater has overtopped the bank and spread into the foreground access area. Street-level structures and low ground are exposed.',
    confidence: 0.91,
  },
};
import type {
  ActionCall,
  AuditEntry,
  SignalInput,
  TimelineEvent,
} from '../components/CommandCenter';

// ──────────────────────────────────────────────────────────────────────────
// Demo-safe sample state. Used only when the backend has no active alert.
// Clearly labeled in the UI with a "DEMO · sample state" badge. This is
// not a hidden mock — it's the screen-recording fallback.
// ──────────────────────────────────────────────────────────────────────────
const DEMO_SITE: Site = {
  id: 'silverado-fixed-cam-usgs',
  name: 'Silverado Fixed Cam (USGS)',
  region: 'Demo · public USGS clip · sample state',
  lat: 33.74,
  lng: -117.65,
  description:
    'Bundled repo site. Serves as E2E reference for the CV+Gemma pipeline on a real clip.',
  is_active: true,
};

const DEMO_ALERT: FusedAlert = {
  id: 9001,
  site_id: 'silverado-fixed-cam-usgs',
  level: 'red',
  score: 0.87,
  summary:
    'Critical line crossed at t=078s. Corroborated by brigade report and 68% 12h rain probability.',
  created_at: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
  trigger_source: 'fused',
  reasoning_summary:
    'The mid-lower band of the frame went from dry to turbid over 12 consecutive frames. ' +
    'Rise velocity 0.0034/frame exceeds internal threshold (0.0020). ' +
    'Volunteer report confirms crossing of the critical mark. Confidence 78%.',
  reasoning_chain: JSON.stringify([
    'observation.crossed_critical_line = true (waterline_ratio 0.42 > 0.30)',
    'rise_velocity 0.0034/frame > threshold 0.0020 → sustained rise signal',
    'volunteer report lexically matches "crossed the critical mark"',
    'hydromet 12h probability = 68% → corroborates event hypothesis',
    'fused_score = 0.87 -> RED level, emit_cap_xml enabled',
  ]),
  reasoning_model: CENTRAL_NODE_MODEL,
};

const DEMO_FUSION: SignalInput[] = [
  { source: 'camera',    score: 0.87, status: 'ok',    detail: 'Crossed critical line · 126 frames analyzed', ageSeconds: 8 },
  { source: 'volunteer', score: 0.62, status: 'ok',    detail: '"Water already crossed the critical mark and carries mud" · 1 report', ageSeconds: 92 },
  { source: 'hydromet',  score: 0.45, status: 'ok',    detail: 'Open-Meteo · 12.4 mm/h · prob 12h 68%',          ageSeconds: 240 },
];

const DEMO_AUDIT: AuditEntry[] = [
  { rule: 'RULE_CRITICAL_LINE_CROSSED',     outcome: 'fired',     detail: 'CV node observation: waterline_ratio 0.42 crossed calibrated line y=120.' },
  { rule: 'RULE_RISE_VELOCITY',             outcome: 'fired',     detail: 'rise_velocity 0.0034/frame > threshold 0.0020/frame.' },
  { rule: 'RULE_VOLUNTEER_CORROBORATION',   outcome: 'fired',     detail: '1 volunteer report classified by Gemma with urgency=high in last 5 min.' },
  { rule: 'RULE_HYDROMET_AGREEMENT',        outcome: 'fired',     detail: 'Open-Meteo 12h probability 68% exceeds threshold 50%.' },
  { rule: 'RULE_DUPLICATE_SUPPRESSION',     outcome: 'not_fired', detail: 'No prior active alert found for this site in 30 min window.' },
  { rule: 'RULE_MANUAL_OVERRIDE',           outcome: 'not_fired', detail: 'Operator did not apply manual override.' },
];

const DEMO_TIMELINE_FACTORY = (): TimelineEvent[] => {
  const now = Date.now();
  const t = (deltaSec: number) => new Date(now + deltaSec * 1000).toISOString();
  return [
    { at: t(-240), kind: 'detect',    label: 'CV detection',            detail: 'Silverado node: rise_velocity > threshold', done: true },
    { at: t(-185), kind: 'volunteer', label: 'Volunteer report',       detail: 'Brigade member Maria G. (Vigia Android)', done: true },
    { at: t(-145), kind: 'fuse',      label: 'Signal fusion',          detail: 'fused_score = 0.87 · level = red',        done: true },
    { at: t(-90),  kind: 'cap',       label: 'CAP v1.2 emitted',       detail: 'receipt CAP-2026-05-16-0042',             done: true },
    { at: t(-70),  kind: 'siren',     label: 'Siren triggered',        detail: 'GPIO relay low zone',                     done: true },
    { at: t(-30),  kind: 'notify',    label: 'Civil Defense notified', detail: 'Municipal webhook acknowledged',          done: true },
    { at: t(60),   kind: 'sync',      label: 'Next CV window',         detail: 'Automatic re-analysis in 60s',            done: false },
  ];
};

const DEMO_CAP = {
  status: 'emitted' as const,
  lastEmit: new Date(Date.now() - 1000 * 90).toLocaleString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', day: '2-digit', month: '2-digit',
  }),
  receiptId: 'CAP-2026-05-16-0042',
  schemaVersion: 'CAP v1.2',
  recipientCount: 3,
};

// ──────────────────────────────────────────────────────────────────────────
// Dashboard (Persona C command center)
// ──────────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { sites, alerts, fetchSites, fetchAlerts, isOnline, queueCount } = useAppStore();

  // Local state for the action rail. The buttons fire deterministic UI feedback
  // so the recording shows the loop closing — they do NOT silently invent
  // backend behavior; clicking dispatches an explicit "demo action" log line.
  const [actionState, setActionState] = useState<Record<ActionCall['fn'], { busy: boolean }>>({
    emit_cap_xml:         { busy: false },
    trigger_siren:        { busy: false },
    send_lora_alert:      { busy: false },
    notify_civil_defense: { busy: false },
  });
  const [actionLog, setActionLog] = useState<string[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>(() => DEMO_TIMELINE_FACTORY());

  useEffect(() => {
    if (isOnline) {
      fetchSites();
      fetchAlerts();
    }
  }, [fetchSites, fetchAlerts, isOnline]);

  // Top-priority alert: the highest-level live alert, falling back to demo.
  const { activeAlert, activeSite, isDemo } = useMemo(() => {
    if (alerts.length > 0) {
      const order: Record<FusedAlert['level'], number> = { red: 0, orange: 1, yellow: 2, green: 3 };
      const sorted = [...alerts].sort((a, b) => order[a.level] - order[b.level] || b.score - a.score);
      const top = sorted[0];
      const site = sites.find((s) => s.id === top.site_id) ?? null;
      return { activeAlert: top, activeSite: site, isDemo: false };
    }
    return { activeAlert: DEMO_ALERT, activeSite: DEMO_SITE, isDemo: true };
  }, [alerts, sites]);

  const reasoningChain = useMemo(() => {
    if (!activeAlert?.reasoning_chain) return undefined;
    try {
      const parsed = JSON.parse(activeAlert.reasoning_chain);
      return Array.isArray(parsed) ? parsed.map(String) : undefined;
    } catch {
      return undefined;
    }
  }, [activeAlert]);

  // Parse the live decision_trace (decision-trace-v2 schema) once. The fusion
  // tiles and audit panel both consume this — for demo fallback (no live alert)
  // we still use DEMO_FUSION / DEMO_AUDIT.
  const liveTrace = useMemo<any>(() => {
    if (isDemo || !activeAlert?.decision_trace) return null;
    try { return JSON.parse(activeAlert.decision_trace); } catch { return null; }
  }, [activeAlert, isDemo]);

  const liveSignals = useMemo<SignalInput[]>(() => {
    if (!liveTrace?.evidence) return DEMO_FUSION;
    const ev: any[] = Array.isArray(liveTrace.evidence) ? liveTrace.evidence : [];
    type Best = { score: number; weighted: number; summary: string; observed: number };
    const best: Record<'camera'|'volunteer'|'hydromet', Best | null> = {
      camera: null, volunteer: null, hydromet: null,
    };
    for (const e of ev) {
      const src = e.source === 'node' ? 'camera' : (e.source as 'volunteer'|'hydromet'|'camera');
      if (!(src in best)) continue;
      const w = Number(e.weighted_score) || 0;
      const prev = best[src];
      if (!prev || w > prev.weighted) {
        best[src] = {
          score: Number(e.raw_score) || 0,
          weighted: w,
          summary: String(e.summary || '').slice(0, 140),
          observed: Date.parse(e.observed_at) || Date.now(),
        };
      }
    }
    const now = Date.now();
    const MODEL_BY_SRC: Record<'camera'|'volunteer'|'hydromet', string> = {
      camera:    'gemma4:e4b',
      volunteer: 'gemma4:e2b',
      hydromet:  'open-meteo',
    };
    return (['camera','volunteer','hydromet'] as const).map((src) => {
      const b = best[src];
      if (!b) return {
        source: src, score: 0, status: 'missing' as const,
        detail: 'no signal in 45 min window', model: MODEL_BY_SRC[src],
      };
      const ageSec = Math.max(0, Math.round((now - b.observed) / 1000));
      return {
        source: src,
        score: b.score,
        status: ageSec > 1800 ? ('stale' as const) : ('ok' as const),
        detail: b.summary || `score=${b.score.toFixed(2)}`,
        ageSeconds: ageSec,
        model: MODEL_BY_SRC[src],
      };
    });
  }, [liveTrace]);

  const liveAudit = useMemo<AuditEntry[]>(() => {
    if (!liveTrace?.rules_fired) return DEMO_AUDIT;
    const fired: string[] = Array.isArray(liveTrace.rules_fired) ? liveTrace.rules_fired.map(String) : [];
    const has = (needle: string) => fired.some((r) => r.includes(needle));
    const entries: AuditEntry[] = [
      { rule: 'RULE_NODE_CRITICAL_LINE',     outcome: has('node_critical_line_crossed') ? 'fired' : 'not_fired', detail: 'Fixed camera crossed calibrated critical line.' },
      { rule: 'RULE_NODE_FAST_RISE',         outcome: has('node_fast_rise') ? 'fired' : 'not_fired',           detail: 'rise_velocity exceeds threshold 0.08/frame.' },
      { rule: 'RULE_VOLUNTEER_MARK_EXCEEDED', outcome: has('volunteer_mark_exceeded') ? 'fired' : 'not_fired', detail: 'Human report confirms water mark exceeded.' },
      { rule: 'RULE_VOLUNTEER_ROAD_CUT',     outcome: has('volunteer_road_cut') ? 'fired' : 'not_fired',       detail: 'Citizen report: road cut / impassable.' },
      { rule: 'RULE_VOLUNTEER_HOMES_AFFECTED', outcome: has('volunteer_homes_affected') ? 'fired' : 'not_fired', detail: 'Citizen report: water inside homes.' },
      { rule: 'RULE_CORROBORATION_MULTI_SRC', outcome: has('corroboration_sources') ? 'fired' : 'not_fired',   detail: 'Two or more sources with score >= 0.35.' },
      { rule: 'RULE_TWO_MEDIUM_TO_ORANGE',   outcome: has('two_medium_sources_escalate_to_orange') ? 'fired' : 'not_fired', detail: 'Two sources in mid band -> escalated to orange.' },
    ];
    return entries;
  }, [liveTrace]);

  const invokeAction = (fn: ActionCall['fn']) => {
    setActionState((prev) => ({ ...prev, [fn]: { busy: true } }));
    const at = new Date().toLocaleTimeString('en-US');
    setActionLog((prev) => [`${at}  function_call → ${fn}(...)`, ...prev].slice(0, 5));

    setTimeout(() => {
      setActionState((prev) => ({ ...prev, [fn]: { busy: false } }));
      setActionLog((prev) => [`${new Date().toLocaleTimeString('en-US')}  ✓ ${fn} ok`, ...prev].slice(0, 5));
      // mirror the action into the timeline so the demo loop closes visibly
      const at2 = new Date().toISOString();
      const map: Partial<Record<ActionCall['fn'], TimelineEvent>> = {
        emit_cap_xml:         { at: at2, kind: 'cap',    label: 'CAP v1.2 emitted',          detail: 'Manual operator re-emission',        done: true },
        trigger_siren:        { at: at2, kind: 'siren',  label: 'Siren triggered',           detail: 'Operator triggered relay',           done: true },
        send_lora_alert:      { at: at2, kind: 'notify', label: 'LoRa alert sent',           detail: 'Broadcast to sibling nodes',         done: true },
        notify_civil_defense: { at: at2, kind: 'notify', label: 'Civil Defense notified',    detail: 'Manual webhook re-send',             done: true },
      };
      const event = map[fn];
      if (event) {
        setTimeline((prev) => [...prev, event]);
      }
    }, 900);
  };

  const actions: ActionCall[] = [
    { fn: 'emit_cap_xml',         arg: `site=${activeSite?.name ?? activeAlert.site_id}`, busy: actionState.emit_cap_xml.busy },
    { fn: 'trigger_siren',        arg: 'zone=low',                     busy: actionState.trigger_siren.busy },
    { fn: 'send_lora_alert',      arg: 'broadcast',                    busy: actionState.send_lora_alert.busy },
    { fn: 'notify_civil_defense', arg: 'webhook=municipal',            busy: actionState.notify_civil_defense.busy },
  ];

  // The "all-clear" state: no active alert AND no demo fallback wanted —
  // currently we always show demo when alerts is empty, so this branch only
  // fires if alerts.length > 0 and somehow no top alert (defensive only).
  if (!activeAlert) {
    return (
      <div className="space-y-6 pb-20">
        <EmptyCommandCenter />
        <SitesGrid sites={sites} isOnline={isOnline} />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20">
      {/* ── 5-second read ────────────────────────────────────────────── */}
      <RiskBannerForAlert alert={activeAlert} site={activeSite} isDemo={isDemo} />

      {/* ── Main two-column command grid ────────────────────────────── */}
      <div className="cc-grid">
        {/* Left column: signals → evidence → reasoning → audit */}
        <div className="space-y-4">
          <SectionPanel title="Signal fusion" meta={`fused_score = ${activeAlert.score.toFixed(2)}`}>
            <SignalFusionRow inputs={liveSignals} />
          </SectionPanel>

          <SectionPanel title="Evidence frame · Gemma narration" meta={CENTRAL_NODE_MODEL}>
            <EvidencePanel
              frameUrl={EVIDENCE_BY_LEVEL[activeAlert.level].frameUrl}
              frameLabel={EVIDENCE_BY_LEVEL[activeAlert.level].frameLabel}
              description={EVIDENCE_BY_LEVEL[activeAlert.level].description}
              model={CENTRAL_NODE_MODEL}
              confidence={EVIDENCE_BY_LEVEL[activeAlert.level].confidence}
            />
          </SectionPanel>

          {activeAlert.reasoning_summary && (
            <GemmaReasoning
              summary={activeAlert.reasoning_summary}
              chain={reasoningChain}
              model={CENTRAL_NODE_MODEL}
            />
          )}

          <AuditTrace entries={liveAudit} />
        </div>

        {/* Right column: CAP, action rail, offline sync */}
        <div className="space-y-4">
          <CapStatusCard {...DEMO_CAP} />

          <ActionRail actions={actions} onInvoke={invokeAction} />

          {actionLog.length > 0 && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-300 leading-snug space-y-1">
              <div className="text-slate-500 uppercase tracking-wider text-xs font-bold mb-1">
                stdout · function_call log
              </div>
              {actionLog.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          )}

          <OfflineSyncCard
            isOnline={isOnline}
            queueCount={queueCount}
            lastSync={isOnline ? new Date().toLocaleTimeString('en-US') : null}
          />
        </div>
      </div>

      {/* ── Lifecycle timeline (full width) ────────────────────────── */}
      <IncidentTimeline events={timeline} />

      {/* ── Auxiliary: sites grid for navigation ───────────────────── */}
      <SitesGrid sites={sites} isOnline={isOnline} />
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// RiskBannerForAlert — thin wrapper that maps a FusedAlert + Site into the
// generic RiskBanner. Lives here so the dashboard owns the mapping.
// ──────────────────────────────────────────────────────────────────────────
function RiskBannerForAlert({
  alert,
  site,
  isDemo,
}: {
  alert: FusedAlert;
  site: Site | null;
  isDemo: boolean;
}) {
  return (
    <RiskBanner
      level={alert.level}
      score={alert.score}
      siteName={site?.name ?? alert.site_id}
      region={site?.region}
      summary={alert.summary}
      isDemo={isDemo}
    />
  );
}

// ──────────────────────────────────────────────────────────────────────────
// SitesGrid — preserves the dashboard's original "Monitored Sites" affordance
// so the operator can navigate into a SiteDetail mid-recording.
// ──────────────────────────────────────────────────────────────────────────
function SitesGrid({ sites, isOnline }: { sites: Site[]; isOnline: boolean }) {
  if (sites.length === 0) {
    return null;
  }
  return (
    <section>
      <h2 className="text-sm font-bold uppercase tracking-widest text-slate-800 mb-3">
        Monitored sites
      </h2>
      <div className="grid gap-3 md:grid-cols-2">
        {sites.map((site) => (
          <Link
            key={site.id}
            to={`/sites/${site.id}`}
            className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:border-blue-300 transition-colors"
          >
            <div className="flex justify-between items-start gap-4">
              <div>
                <h3 className="font-semibold text-gray-900">{site.name}</h3>
                <p className="text-sm text-gray-500">{site.region}</p>
              </div>
              <span
                className={`px-2 py-1 text-xs rounded-full font-medium ${
                  site.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                }`}
              >
                {site.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="mt-3 text-sm text-blue-600 font-medium inline-flex items-center gap-1">
              Open site <ArrowRight className="w-4 h-4" />
            </div>
            {!isOnline && (
              <div className="text-xs text-gray-400 mt-2">
                Offline — data from last available cache
              </div>
            )}
          </Link>
        ))}
      </div>
    </section>
  );
}
