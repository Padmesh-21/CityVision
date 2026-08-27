const STATUS_CLASS = {
  ACTIVE: "status-pill-active",
  INACTIVE: "status-pill-inactive",
  OFFLINE: "status-pill-offline",
};

export default function CameraStatusBadge({ status }) {
  return <span className={`status-pill ${STATUS_CLASS[status] || "status-pill-inactive"}`}>{status}</span>;
}
