import { useEffect, useState } from "react";
import AlertCard from "../components/Alert/AlertCard";
import { useAuth } from "../hooks/useAuth";
import { alertApi, blacklistApi } from "../services/api";

const POLL_MS = 15000;
const STATUS_FILTERS = ["ALL", "NEW", "ACKNOWLEDGED", "RESOLVED"];

export default function Alerts() {
  const { canWrite } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);

  const [blacklist, setBlacklist] = useState([]);
  const [newPlate, setNewPlate] = useState("");
  const [newReason, setNewReason] = useState("");
  const [blacklistError, setBlacklistError] = useState("");

  const loadAlerts = async () => {
    const { data } = await alertApi.list({ ordering: "-created_at" });
    setAlerts(data.results ?? data);
  };

  const loadBlacklist = async () => {
    const { data } = await blacklistApi.list();
    setBlacklist(data.results ?? data);
  };

  useEffect(() => {
    Promise.all([loadAlerts(), loadBlacklist()]).finally(() => setIsLoading(false));
    const interval = setInterval(loadAlerts, POLL_MS);
    return () => clearInterval(interval);
  }, []);

  const handleAddToBlacklist = async (event) => {
    event.preventDefault();
    setBlacklistError("");
    try {
      await blacklistApi.create({ plate_number: newPlate.trim().toUpperCase(), reason: newReason.trim() });
      setNewPlate("");
      setNewReason("");
      await loadBlacklist();
    } catch (err) {
      setBlacklistError(err.response?.data?.plate_number?.[0] || "Could not add plate to blacklist.");
    }
  };

  const handleResolveBlacklist = async (entry) => {
    await blacklistApi.update(entry.id, { ...entry, status: entry.status === "ACTIVE" ? "RESOLVED" : "ACTIVE" });
    await loadBlacklist();
  };

  const visibleAlerts = statusFilter === "ALL" ? alerts : alerts.filter((a) => a.status === statusFilter);

  if (isLoading) return <div className="page-loading">Loading alerts...</div>;

  return (
    <div className="alerts-page">
      <section>
        <h1>Alerts</h1>
        <div className="filter-row">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status}
              className={"chip-button" + (statusFilter === status ? " chip-button-active" : "")}
              onClick={() => setStatusFilter(status)}
            >
              {status}
            </button>
          ))}
        </div>

        <div className="alert-list">
          {visibleAlerts.length === 0 && <p className="muted-text">No alerts match this filter.</p>}
          {visibleAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      </section>

      <section className="blacklist-panel">
        <h2>Blacklist</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Plate</th>
              <th>Reason</th>
              <th>Status</th>
              {canWrite && <th />}
            </tr>
          </thead>
          <tbody>
            {blacklist.map((entry) => (
              <tr key={entry.id}>
                <td>{entry.plate_number}</td>
                <td>{entry.reason}</td>
                <td>
                  <span className={`status-pill status-pill-${entry.status.toLowerCase()}`}>
                    {entry.status}
                  </span>
                </td>
                {canWrite && (
                  <td>
                    <button className="link-button" onClick={() => handleResolveBlacklist(entry)}>
                      {entry.status === "ACTIVE" ? "Resolve" : "Reactivate"}
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {blacklist.length === 0 && (
              <tr>
                <td colSpan={4} className="muted-text">
                  No blacklist entries.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {canWrite && (
          <form className="inline-form" onSubmit={handleAddToBlacklist}>
            <input
              placeholder="Plate number"
              value={newPlate}
              onChange={(e) => setNewPlate(e.target.value)}
              required
            />
            <input
              placeholder="Reason (e.g. Stolen Vehicle)"
              value={newReason}
              onChange={(e) => setNewReason(e.target.value)}
              required
            />
            <button type="submit">Add to blacklist</button>
          </form>
        )}
        {blacklistError && <div className="form-error">{blacklistError}</div>}
      </section>
    </div>
  );
}
