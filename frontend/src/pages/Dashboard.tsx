import { useEffect } from 'react';
import { useAppStore } from '../store';
import { AlertTriangle, MapPin, CheckCircle2 } from 'lucide-react';

export default function Dashboard() {
  const { sites, alerts, fetchSites, fetchAlerts, isOnline } = useAppStore();

  useEffect(() => {
    if (isOnline) {
      fetchSites();
      fetchAlerts();
    }
  }, [fetchSites, fetchAlerts, isOnline]);

  const levelColors = {
    green: 'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    orange: 'bg-orange-100 text-orange-800 border-orange-200',
    red: 'bg-red-100 text-red-800 border-red-200',
  };

  return (
    <div className="space-y-6 pb-20">
      <section>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle className="text-orange-500" />
          Active Alerts
        </h2>
        {alerts.length === 0 ? (
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg flex items-center gap-3 text-gray-500">
            <CheckCircle2 className="text-green-500" />
            No active alerts at the moment.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border flex gap-3 ${levelColors[alert.level]}`}
              >
                <AlertTriangle className="shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold">{alert.site_id}</h3>
                  <p className="text-sm mt-1">{alert.summary}</p>
                  <div className="text-xs mt-2 opacity-80">
                    Score: {(alert.score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <MapPin className="text-blue-500" />
          Monitored Sites
        </h2>
        <div className="grid gap-3 md:grid-cols-2">
          {sites.map((site) => (
            <div key={site.id} className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-gray-900">{site.name}</h3>
                  <p className="text-sm text-gray-500">{site.region}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full font-medium ${site.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {site.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
          {sites.length === 0 && isOnline && (
            <div className="text-gray-500 text-sm">No sites found.</div>
          )}
          {!isOnline && sites.length === 0 && (
            <div className="text-gray-500 text-sm">Offline. Sites not loaded.</div>
          )}
        </div>
      </section>
    </div>
  );
}
