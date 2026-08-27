import { Link } from "react-router-dom";
import { STATUS } from "../../theme";

const SEVERITY_COLOR = {
  LOW: STATUS.good,
  MEDIUM: STATUS.warning,
  HIGH: STATUS.serious,
  CRITICAL: STATUS.critical,
};

export default function AlertCard({ alert }) {
  return (
    <div className="alert-card">
      <div className="alert-card-header">
        <span
          className="severity-dot"
          style={{ backgroundColor: SEVERITY_COLOR[alert.severity] || STATUS.warning }}
        />
        <span className="alert-card-title">
          {alert.alert_type === "BLACKLISTED_VEHICLE" ? "Blacklisted vehicle" : alert.alert_type}
        </span>
        <span className="alert-card-time">{new Date(alert.created_at).toLocaleTimeString()}</span>
      </div>

      <div className="alert-card-body">
        <div>
          Plate: <strong>{alert.plate_number}</strong>
        </div>
        {alert.camera_code && (
          <div>
            Camera: {alert.camera_code} -- {alert.location_name}
          </div>
        )}
        <div className="alert-card-message">{alert.message}</div>
      </div>

      <div className="alert-card-footer">
        <span className={`status-pill status-pill-${alert.status?.toLowerCase()}`}>{alert.status}</span>
        <Link to={`/search?plate=${alert.plate_number}`}>View trajectory &rarr;</Link>
      </div>
    </div>
  );
}
