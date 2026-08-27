import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const ACCESS_TOKEN_KEY = "cityvision_access_token";
const REFRESH_TOKEN_KEY = "cityvision_refresh_token";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (access, refresh) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On a 401 (expired access token), try exactly one silent refresh before
// giving up and forcing a re-login -- avoids both an infinite retry loop
// and forcing the user to log in again for every short-lived token.
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint = originalRequest.url?.includes("/api/auth/token");

    if (error.response?.status === 401 && !originalRequest._retried && !isAuthEndpoint) {
      originalRequest._retried = true;
      const refreshToken = tokenStorage.getRefresh();
      if (!refreshToken) {
        tokenStorage.clear();
        return Promise.reject(error);
      }

      try {
        refreshPromise =
          refreshPromise ||
          axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, { refresh: refreshToken });
        const { data } = await refreshPromise;
        tokenStorage.set(data.access, null);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        tokenStorage.clear();
        return Promise.reject(refreshError);
      } finally {
        refreshPromise = null;
      }
    }

    return Promise.reject(error);
  }
);

export const authApi = {
  login: (username, password) => api.post("/api/auth/token/", { username, password }),
  me: () => api.get("/api/auth/me/"),
};

export const cameraApi = {
  list: () => api.get("/api/cameras/"),
  create: (data) => api.post("/api/cameras/", data),
  update: (id, data) => api.put(`/api/cameras/${id}/`, data),
  remove: (id) => api.delete(`/api/cameras/${id}/`),
  regenerateApiKey: (id) => api.post(`/api/cameras/${id}/regenerate_api_key/`),
};

export const vehicleApi = {
  list: (params) => api.get("/api/vehicles/", { params }),
  get: (plateNumber) => api.get(`/api/vehicles/${plateNumber}/`),
  trajectory: (plateNumber) => api.get(`/api/vehicles/${plateNumber}/trajectory/`),
};

export const detectionApi = {
  list: (params) => api.get("/api/detections/", { params }),
};

export const alertApi = {
  list: (params) => api.get("/api/alerts/", { params }),
};

export const blacklistApi = {
  list: () => api.get("/api/blacklist/"),
  create: (data) => api.post("/api/blacklist/", data),
  update: (id, data) => api.put(`/api/blacklist/${id}/`, data),
  remove: (id) => api.delete(`/api/blacklist/${id}/`),
};

export const analyticsApi = {
  summary: (params) => api.get("/api/analytics/summary/", { params }),
  routeDensity: (params) => api.get("/api/analytics/route-density/", { params }),
  averageSpeed: (params) => api.get("/api/analytics/average-speed/", { params }),
  heatmap: (params) => api.get("/api/analytics/heatmap/", { params }),
};

export default api;
