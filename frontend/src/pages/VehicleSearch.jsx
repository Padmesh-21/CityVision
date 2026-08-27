import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CityMap from "../components/Map/CityMap";
import { vehicleApi } from "../services/api";

export default function VehicleSearch() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [plateInput, setPlateInput] = useState(searchParams.get("plate") || "");
  const [vehicle, setVehicle] = useState(null);
  const [trajectory, setTrajectory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const runSearch = async (plate) => {
    const normalized = plate.trim().toUpperCase();
    if (!normalized) return;

    setIsLoading(true);
    setError("");
    setHasSearched(true);
    try {
      const [vehicleRes, trajectoryRes] = await Promise.all([
        vehicleApi.get(normalized),
        vehicleApi.trajectory(normalized),
      ]);
      setVehicle(vehicleRes.data);
      setTrajectory(trajectoryRes.data.trajectory);
    } catch {
      setVehicle(null);
      setTrajectory([]);
      setError(`No vehicle found for plate "${normalized}".`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const plateFromUrl = searchParams.get("plate");
    if (plateFromUrl) runSearch(plateFromUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = (event) => {
    event.preventDefault();
    setSearchParams(plateInput ? { plate: plateInput.trim().toUpperCase() } : {});
    runSearch(plateInput);
  };

  return (
    <div>
      <h1>Vehicle Search</h1>

      <form className="search-form" onSubmit={handleSubmit}>
        <input
          placeholder="Enter license plate, e.g. TN09AB1234"
          value={plateInput}
          onChange={(event) => setPlateInput(event.target.value)}
          autoFocus
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <div className="form-error">{error}</div>}

      {vehicle && (
        <div className="vehicle-result">
          <section className="vehicle-summary">
            <h2>{vehicle.plate_number}</h2>
            <dl>
              <dt>Vehicle type</dt>
              <dd>{vehicle.vehicle_type}</dd>
              <dt>First seen</dt>
              <dd>{vehicle.first_seen ? new Date(vehicle.first_seen).toLocaleString() : "--"}</dd>
              <dt>Last seen</dt>
              <dd>{vehicle.last_seen ? new Date(vehicle.last_seen).toLocaleString() : "--"}</dd>
              <dt>Total detections</dt>
              <dd>{vehicle.total_detections}</dd>
            </dl>

            <h3>Route</h3>
            <ol className="trajectory-steps">
              {trajectory.map((point, index) => (
                <li key={`${point.camera}-${point.timestamp}`}>
                  <strong>{point.camera}</strong> -- {point.location}
                  <div className="trajectory-step-meta">
                    {new Date(point.timestamp).toLocaleString()} &middot; {point.direction || "n/a"} &middot;{" "}
                    {(point.confidence * 100).toFixed(0)}% confidence
                  </div>
                  {index < trajectory.length - 1 && <div className="trajectory-arrow">&darr;</div>}
                </li>
              ))}
            </ol>
          </section>

          <section className="vehicle-map">
            <CityMap trajectory={trajectory} height={520} />
          </section>
        </div>
      )}

      {!vehicle && hasSearched && !isLoading && !error && (
        <p className="muted-text">No results.</p>
      )}
    </div>
  );
}
