import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAppStore } from '../store';
import { Activity, FileText, UploadCloud, Wifi, WifiOff } from 'lucide-react';
import { useEffect } from 'react';

export default function Layout() {
  const { isOnline, queueCount, checkConnectivity, setOnline } = useAppStore();
  const location = useLocation();

  useEffect(() => {
    // Initial check
    checkConnectivity();
    // Poll every 10 seconds
    const interval = setInterval(() => {
      checkConnectivity();
    }, 10000);
    return () => clearInterval(interval);
  }, [checkConnectivity]);

  const toggleOffline = async () => {
    const nextStatus = !isOnline;
    // We can also inform the backend, but for this MVP frontend simulation is fine
    // Or we hit the backend toggle endpoint if it exists.
    try {
        await fetch('http://localhost:8000/api/settings/connectivity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_online: nextStatus })
        });
    } catch (e) {
        console.error("Could not toggle backend offline status", e);
    }
    setOnline(nextStatus);
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <Activity className="w-5 h-5" /> },
    { path: '/report', label: 'Report', icon: <FileText className="w-5 h-5" /> },
    { 
      path: '/queue', 
      label: `Queue (${queueCount})`, 
      icon: <UploadCloud className="w-5 h-5" /> 
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 flex flex-col font-sans">
      <header className="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Activity className="w-6 h-6" /> Acuifero 4 + Vigia
        </h1>
        
        <button 
          onClick={toggleOffline}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
            isOnline ? 'bg-green-500 hover:bg-green-400' : 'bg-red-500 hover:bg-red-400'
          }`}
        >
          {isOnline ? (
            <><Wifi className="w-4 h-4" /> Online</>
          ) : (
            <><WifiOff className="w-4 h-4" /> Offline</>
          )}
        </button>
      </header>

      <main className="flex-1 p-4 max-w-4xl mx-auto w-full">
        <Outlet />
      </main>

      <nav className="bg-white border-t border-gray-200 flex justify-around p-3 pb-safe fixed bottom-0 w-full md:relative">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-colors ${
                isActive ? 'text-blue-600 bg-blue-50' : 'text-gray-500 hover:text-blue-500 hover:bg-gray-50'
              }`}
            >
              {item.icon}
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
