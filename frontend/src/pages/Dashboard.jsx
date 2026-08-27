import { useEffect, useState } from "react";
import CityMap from "../components/Map/CityMap";
import StatCard from "../components/Analytics/StatCard";
import HourlyTrafficChart from "../components/Analytics/HourlyTrafficChart";
import AlertCard from "../components/Alert/AlertCard";
import { alertApi, analyticsApi, cameraApi } from "../services/api";

const ALERTS_POLL_MS = 15000;

export default function Dashboard() {
  const [cameras, setCameras] = useState([]);
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadInitial() {
      try {
        const [camerasRes, summaryRes, alertsRes] = await Promise.all([
          cameraApi.list(),
          analyticsApi.summary(),
          alertApi.list({ ordering: "-created_at" }),
        ]);
        if (cancelled) return;
        setCameras(camerasRes.data.results ?? camerasRes.data);
        setSummary(summaryRes.data);
        setAlerts((alertsRes.data.results ?? alertsRes.data).slice(0, 8));
      } catch {
        if (!cancelled) setError("Could not load dashboard data.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadInitial();

    // Alerts are polled for near-real-time freshness; a push-based
    // WebSocket update replaces this in Step 7 without changing the UI.
    const interval = setInterval(async () => {
      try {
        const { data } = await alertApi.list({ ordering: "-created_at" });
        if (!cancelled) setAlerts((data.results ?? data).slice(0, 8));
      } catch {
        // transient poll failure -- next tick will retry
      }
    }, ALERTS_POLL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (isLoading) return <div className="page-loading">Loading dashboard...</div>;
  if (error) return <div className="page-error">{error}</div>;

  // The Alert API returns camera_code, not coordinates directly -- join
  // against the cameras already loaded rather than adding a redundant
  // lat/lon copy to the backend serializer.
  const alertMapPoints = alerts
    .map((alert) => {
      const camera = cameras.find((c) => c.camera_code === alert.camera_code);
      return camera ? { ...alert, latitude: camera.latitude, longitude: camera.longitude } : null;
    })
    .filter(Boolean);

  return (
    <div className="dashboard-grid">
      <section className="stats-row">
        <StatCard label="Total detections" value={summary.total_detections} />
        <StatCard label="Unique vehicles" value={summary.unique_vehicles} />
        <StatCard label="Cameras online" value={cameras.filter((c) => c.status === "ACTIVE").length} />
        <StatCard label="Active alerts" value={alerts.filter((a) => a.status === "NEW").length} />
      </section>

      <section className="dashboard-map-section">
        <h2>City map</h2>
        <CityMap cameras={cameras} alerts={alertMapPoints} height={420} />
      </section>

      <section className="dashboard-side">
        <h2>Recent alerts</h2>
        <div className="alert-list">
          {alerts.length === 0 && <p className="muted-text">No alerts yet.</p>}
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      </section>

      <section className="dashboard-chart-section">
        <h2>Traffic by hour</h2>
        <HourlyTrafficChart data={summary.hourly_traffic} />
      </section>
    </div>
  );
}
