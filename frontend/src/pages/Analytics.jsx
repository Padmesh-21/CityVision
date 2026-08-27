import { useEffect, useState } from "react";
import CameraTrafficChart from "../components/Analytics/CameraTrafficChart";
import HourlyTrafficChart from "../components/Analytics/HourlyTrafficChart";
import CityMap from "../components/Map/CityMap";
import { analyticsApi, cameraApi } from "../services/api";

export default function Analytics() {
  const [cameras, setCameras] = useState([]);
  const [filters, setFilters] = useState({ camera: "", start_date: "", end_date: "" });
  const [summary, setSummary] = useState(null);
  const [routeDensity, setRouteDensity] = useState([]);
  const [averageSpeed, setAverageSpeed] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (activeFilters) => {
    const params = Object.fromEntries(Object.entries(activeFilters).filter(([, value]) => value));
    const routeParams = { start_date: params.start_date, end_date: params.end_date };

    setIsLoading(true);
    setError("");
    try {
      const [summaryRes, routeRes, speedRes, heatmapRes] = await Promise.all([
        analyticsApi.summary(params),
        analyticsApi.routeDensity(routeParams),
        analyticsApi.averageSpeed(routeParams),
        analyticsApi.heatmap(params),
      ]);
      setSummary(summaryRes.data);
      setRouteDensity(routeRes.data.routes);
      setAverageSpeed(speedRes.data.routes);
      setHeatmap(heatmapRes.data.points);
    } catch {
      setError("Could not load analytics.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    cameraApi.list().then((res) => setCameras(res.data.results ?? res.data));
    load(filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilterSubmit = (event) => {
    event.preventDefault();
    load(filters);
  };

  return (
    <div>
      <h1>Traffic Analytics</h1>

      <form className="filter-row" onSubmit={handleFilterSubmit}>
        <select value={filters.camera} onChange={(e) => setFilters({ ...filters, camera: e.target.value })}>
          <option value="">All cameras</option>
          {cameras.map((camera) => (
            <option key={camera.camera_code} value={camera.camera_code}>
              {camera.camera_code} -- {camera.location_name}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={filters.start_date}
          onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
        />
        <span className="filter-separator">to</span>
        <input
          type="date"
          value={filters.end_date}
          onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
        />
        <button type="submit">Apply filters</button>
      </form>

      {error && <div className="form-error">{error}</div>}
      {isLoading && <div className="page-loading">Loading analytics...</div>}

      {!isLoading && summary && (
        <>
          <div className="analytics-grid">
            <section>
              <h2>Vehicles per camera</h2>
              <CameraTrafficChart data={summary.detections_per_camera} />
            </section>
            <section>
              <h2>Traffic by hour</h2>
              <HourlyTrafficChart data={summary.hourly_traffic} />
            </section>
          </div>

          <section>
            <h2>Traffic heatmap</h2>
            <CityMap cameras={cameras} heatmapPoints={heatmap} height={380} />
          </section>

          <div className="analytics-grid">
            <section>
              <h2>Route density</h2>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>From</th>
                    <th>To</th>
                    <th>Vehicles</th>
                  </tr>
                </thead>
                <tbody>
                  {routeDensity.map((route) => (
                    <tr key={`${route.from_camera}-${route.to_camera}`}>
                      <td>
                        {route.from_camera} ({route.from_location})
                      </td>
                      <td>
                        {route.to_camera} ({route.to_location})
                      </td>
                      <td>{route.count}</td>
                    </tr>
                  ))}
                  {routeDensity.length === 0 && (
                    <tr>
                      <td colSpan={3} className="muted-text">
                        No route data yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>

            <section>
              <h2>Estimated average speed</h2>
              <p className="muted-text small-text">
                Estimated speed between camera locations, derived from distance / time between
                consecutive detections of the same vehicle -- not an instantaneous vehicle speed
                measurement.
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Route</th>
                    <th>Distance</th>
                    <th>Est. speed</th>
                    <th>Samples</th>
                  </tr>
                </thead>
                <tbody>
                  {averageSpeed.map((route) => (
                    <tr key={`${route.from_camera}-${route.to_camera}`}>
                      <td>
                        {route.from_camera} &rarr; {route.to_camera}
                      </td>
                      <td>{route.distance_km} km</td>
                      <td>{route.estimated_avg_speed_kmh} km/h</td>
                      <td>{route.sample_count}</td>
                    </tr>
                  ))}
                  {averageSpeed.length === 0 && (
                    <tr>
                      <td colSpan={4} className="muted-text">
                        No route data yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
