import { useEffect, useState } from "react";
import CameraStatusBadge from "../components/Camera/CameraStatusBadge";
import { useAuth } from "../hooks/useAuth";
import { cameraApi } from "../services/api";

const DIRECTIONS = ["NORTH", "SOUTH", "EAST", "WEST", "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST"];
const EMPTY_FORM = {
  camera_code: "",
  name: "",
  location_name: "",
  latitude: "",
  longitude: "",
  direction: "NORTH",
  status: "ACTIVE",
};

export default function Cameras() {
  const { canWrite, isAdmin } = useAuth();
  const [cameras, setCameras] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newApiKey, setNewApiKey] = useState(null);

  const loadCameras = async () => {
    const { data } = await cameraApi.list();
    setCameras(data.results ?? data);
  };

  useEffect(() => {
    loadCameras()
      .catch(() => setError("Could not load cameras."))
      .finally(() => setIsLoading(false));
  }, []);

  const handleCreate = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const { data } = await cameraApi.create(form);
      setNewApiKey({ camera_code: data.camera_code, api_key: data.api_key });
      setForm(EMPTY_FORM);
      await loadCameras();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create camera. Check the fields and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegenerateKey = async (camera) => {
    const { data } = await cameraApi.regenerateApiKey(camera.id);
    setNewApiKey(data);
  };

  if (isLoading) return <div className="page-loading">Loading cameras...</div>;

  return (
    <div>
      <h1>Cameras</h1>

      {newApiKey && (
        <div className="api-key-banner">
          New API key for <strong>{newApiKey.camera_code}</strong> (shown once -- copy it into that
          node's <code>.env</code> now):
          <code className="api-key-value">{newApiKey.api_key}</code>
          <button className="link-button" onClick={() => setNewApiKey(null)}>
            Dismiss
          </button>
        </div>
      )}

      {error && <div className="form-error">{error}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Location</th>
            <th>Direction</th>
            <th>Status</th>
            <th>Last seen</th>
            {isAdmin && <th />}
          </tr>
        </thead>
        <tbody>
          {cameras.map((camera) => (
            <tr key={camera.id}>
              <td>{camera.camera_code}</td>
              <td>{camera.name}</td>
              <td>{camera.location_name}</td>
              <td>{camera.direction}</td>
              <td>
                <CameraStatusBadge status={camera.status} />
              </td>
              <td>{camera.last_seen ? new Date(camera.last_seen).toLocaleString() : "Never"}</td>
              {isAdmin && (
                <td>
                  <button className="link-button" onClick={() => handleRegenerateKey(camera)}>
                    Regenerate key
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {canWrite && (
        <>
          <h2>Add camera</h2>
          <form className="inline-form" onSubmit={handleCreate}>
            <input
              placeholder="Camera code (e.g. CAM005)"
              value={form.camera_code}
              onChange={(e) => setForm({ ...form, camera_code: e.target.value.toUpperCase() })}
              required
            />
            <input
              placeholder="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
            <input
              placeholder="Location name"
              value={form.location_name}
              onChange={(e) => setForm({ ...form, location_name: e.target.value })}
              required
            />
            <input
              placeholder="Latitude"
              type="number"
              step="any"
              value={form.latitude}
              onChange={(e) => setForm({ ...form, latitude: e.target.value })}
              required
            />
            <input
              placeholder="Longitude"
              type="number"
              step="any"
              value={form.longitude}
              onChange={(e) => setForm({ ...form, longitude: e.target.value })}
              required
            />
            <select value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value })}>
              {DIRECTIONS.map((direction) => (
                <option key={direction} value={direction}>
                  {direction}
                </option>
              ))}
            </select>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding..." : "Add camera"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
