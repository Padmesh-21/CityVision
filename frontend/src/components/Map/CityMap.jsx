import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "leaflet.heat";
import { useEffect, useMemo } from "react";
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";

// Default Chennai-area view -- matches this project's simulated camera
// locations (Anna Nagar, Guindy, T Nagar, Adyar). Configurable via props
// so this component isn't hardcoded to one city.
const DEFAULT_CENTER = [13.04, 80.23];
const DEFAULT_ZOOM = 12;

const STATUS_COLORS = {
  ACTIVE: "#22c55e",
  INACTIVE: "#94a3b8",
  OFFLINE: "#ef4444",
};

const alertIcon = new L.DivIcon({
  className: "alert-marker-icon",
  html: "<div class='alert-marker-pulse'>!</div>",
  iconSize: [26, 26],
});

function HeatmapLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length === 0) return undefined;

    const heatPoints = points.map((point) => [
      point.latitude,
      point.longitude,
      point.weight ?? 1,
    ]);
    const layer = L.heatLayer(heatPoints, { radius: 35, blur: 25, maxZoom: 15 });
    layer.addTo(map);

    return () => map.removeLayer(layer);
  }, [map, points]);

  return null;
}

export default function CityMap({
  cameras = [],
  trajectory = [],
  alerts = [],
  heatmapPoints = [],
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  height = 420,
}) {
  const trajectoryLine = useMemo(
    () => trajectory.map((point) => [Number(point.latitude), Number(point.longitude)]),
    [trajectory]
  );

  return (
    <MapContainer center={center} zoom={zoom} style={{ height, width: "100%" }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {heatmapPoints.length > 0 && <HeatmapLayer points={heatmapPoints} />}

      {cameras.map((camera) => (
        <CircleMarker
          key={camera.camera_code}
          center={[Number(camera.latitude), Number(camera.longitude)]}
          radius={9}
          pathOptions={{
            color: STATUS_COLORS[camera.status] || STATUS_COLORS.INACTIVE,
            fillColor: STATUS_COLORS[camera.status] || STATUS_COLORS.INACTIVE,
            fillOpacity: 0.85,
            weight: 2,
          }}
        >
          <Popup>
            <strong>{camera.camera_code}</strong> -- {camera.name}
            <br />
            {camera.location_name}
            <br />
            Status: {camera.status}
          </Popup>
        </CircleMarker>
      ))}

      {alerts.map((alert) => (
        <Marker
          key={alert.id}
          position={[Number(alert.latitude), Number(alert.longitude)]}
          icon={alertIcon}
        >
          <Popup>
            <strong>Blacklisted vehicle</strong>
            <br />
            {alert.plate_number}
            <br />
            {alert.camera_code} -- {alert.location_name}
          </Popup>
        </Marker>
      ))}

      {trajectoryLine.length > 1 && (
        <Polyline positions={trajectoryLine} pathOptions={{ color: "#2563eb", weight: 4, opacity: 0.8 }} />
      )}

      {trajectory.map((point, index) => (
        <CircleMarker
          key={`${point.camera}-${point.timestamp}`}
          center={[Number(point.latitude), Number(point.longitude)]}
          radius={7}
          pathOptions={{ color: "#2563eb", fillColor: "#ffffff", fillOpacity: 1, weight: 3 }}
        >
          <Popup>
            <strong>
              Stop {index + 1}: {point.camera}
            </strong>
            <br />
            {point.location}
            <br />
            {new Date(point.timestamp).toLocaleString()}
            <br />
            Direction: {point.direction || "n/a"}
            <br />
            Confidence: {(point.confidence * 100).toFixed(0)}%
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
