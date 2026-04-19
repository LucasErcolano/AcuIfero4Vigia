import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { API_BASE } from '../store';
import { LoaderCircle, Save } from 'lucide-react';

function parsePoints(raw?: string | null) {
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as number[][];
  } catch {
    return null;
  }
}

function getBoundingBox(points?: number[][] | null) {
  if (!points || points.length === 0) {
    return null;
  }
  const xs = points.map((point) => point[0]);
  const ys = points.map((point) => point[1]);
  return {
    width: Math.max(...xs),
    height: Math.max(...ys),
    top: Math.min(...ys),
    bottom: Math.max(...ys),
  };
}

function toAssetUrl(assetPath?: string | null) {
  if (!assetPath) {
    return null;
  }
  if (assetPath.startsWith('http://') || assetPath.startsWith('https://')) {
    return assetPath;
  }
  const apiOrigin = API_BASE.replace(/\/api\/?$/, '');
  return `${apiOrigin}${assetPath}`;
}

export default function Calibration() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [frameWidth, setFrameWidth] = useState(640);
  const [frameHeight, setFrameHeight] = useState(480);
  const [roiTop, setRoiTop] = useState(40);
  const [roiBottom, setRoiBottom] = useState(430);
  const [criticalY, setCriticalY] = useState(170);
  const [referenceY, setReferenceY] = useState(260);
  const [notes, setNotes] = useState('');
  const [sampleFrameUrl, setSampleFrameUrl] = useState<string | null>(null);
  const [sampleVideoSourceUrl, setSampleVideoSourceUrl] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      return;
    }

    const loadCalibration = async () => {
      try {
        const [siteResponse, calibrationResponse] = await Promise.all([
          fetch(`${API_BASE}/sites/${id}`),
          fetch(`${API_BASE}/sites/${id}/calibration`),
        ]);

        if (siteResponse.ok) {
          const sitePayload = await siteResponse.json();
          setSampleFrameUrl(toAssetUrl(sitePayload?.sample_frame_url));
          setSampleVideoSourceUrl(sitePayload?.sample_video_source_url ?? null);
        }

        if (!calibrationResponse.ok) {
          return;
        }
        const calibrationPayload = await calibrationResponse.json();
        const calibration = {
          roi_polygon: parsePoints(calibrationPayload?.roi_polygon),
          critical_line: parsePoints(calibrationPayload?.critical_line),
          reference_line: parsePoints(calibrationPayload?.reference_line),
          notes: calibrationPayload?.notes,
        };
        const roiBounds = getBoundingBox(calibration?.roi_polygon);
        if (roiBounds) {
          setFrameWidth(Math.max(roiBounds.width, 640));
          setFrameHeight(Math.max(roiBounds.height, 480));
          setRoiTop(roiBounds.top);
          setRoiBottom(roiBounds.bottom);
        }
        if (Array.isArray(calibration?.critical_line) && calibration.critical_line.length >= 2) {
          setCriticalY(calibration.critical_line[0][1]);
        }
        if (Array.isArray(calibration?.reference_line) && calibration.reference_line.length >= 2) {
          setReferenceY(calibration.reference_line[0][1]);
        }
        setNotes(calibration?.notes ?? '');
      } catch (loadError) {
        console.error(loadError);
      }
    };

    loadCalibration();
  }, [id]);

  const saveCalibration = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id) {
      return;
    }

    setIsSaving(true);
    setMessage(null);
    setError(null);

    const payload = {
      roi_polygon: [
        [0, roiTop],
        [frameWidth, roiTop],
        [frameWidth, roiBottom],
        [0, roiBottom],
      ],
      critical_line: [
        [0, criticalY],
        [frameWidth, criticalY],
      ],
      reference_line: [
        [0, referenceY],
        [frameWidth, referenceY],
      ],
      notes,
    };

    try {
      const response = await fetch(`${API_BASE}/sites/${id}/calibration`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setMessage('Calibration saved.');
      setTimeout(() => navigate(`/sites/${id}`), 800);
    } catch (saveError) {
      console.error(saveError);
      setError('Failed to save calibration.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 pb-20">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Site Calibration</h2>
        <p className="text-sm text-gray-500 mt-1">
          Save a rectangular ROI and two threshold lines. This page is tied to the site reference frame so the numeric values map to a real fixed-camera view.
        </p>
      </div>

      {sampleFrameUrl && (
        <section className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <img src={sampleFrameUrl} alt="Site reference frame for calibration" className="w-full object-cover" />
          <div className="px-5 py-4 text-sm text-gray-600 flex items-center justify-between gap-4 flex-wrap">
            <span>Use this stored frame as the pixel reference when adjusting ROI and threshold lines.</span>
            {sampleVideoSourceUrl && (
              <a href={sampleVideoSourceUrl} target="_blank" rel="noreferrer" className="font-medium text-blue-700 hover:text-blue-800">
                Original source
              </a>
            )}
          </div>
        </section>
      )}

      <form onSubmit={saveCalibration} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm font-medium text-gray-700">
            Frame width
            <input
              type="number"
              value={frameWidth}
              onChange={(event) => setFrameWidth(Number(event.target.value))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-gray-700">
            Frame height
            <input
              type="number"
              value={frameHeight}
              onChange={(event) => setFrameHeight(Number(event.target.value))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-gray-700">
            ROI top Y
            <input
              type="number"
              value={roiTop}
              onChange={(event) => setRoiTop(Number(event.target.value))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-gray-700">
            ROI bottom Y
            <input
              type="number"
              value={roiBottom}
              onChange={(event) => setRoiBottom(Number(event.target.value))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-gray-700">
            Critical line Y
            <input
              type="number"
              value={criticalY}
              onChange={(event) => setCriticalY(Number(event.target.value))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-gray-700">
            Reference line Y
            <input
              type="number"
              value={referenceY}
              onChange={(event) => setReferenceY(Number(event.target.value))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </label>
        </div>

        <label className="block text-sm font-medium text-gray-700">
          Notes
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            className="mt-1 min-h-[100px] w-full rounded-lg border border-gray-300 px-3 py-2"
            placeholder="Describe the camera position, frame reference and any caveats for this site."
          />
        </label>

        {message && <div className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">{message}</div>}
        {error && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}

        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isSaving ? <LoaderCircle className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {isSaving ? 'Saving...' : 'Save calibration'}
        </button>
      </form>
    </div>
  );
}
