const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  const res = await fetch(url, config);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data?.error?.message || data?.detail || `HTTP ${res.status}`);
  }
  return data;
}

/* --- SOS (F-01, F-02, F-03) --- */

export async function triggerSOS({ type, lat, lng, userId }) {
  return request('/api/sos/trigger', {
    method: 'POST',
    body: JSON.stringify({ type, lat, lng, user_id: userId }),
  });
}

export async function getSOSStatus(sosId) {
  return request(`/api/sos/${sosId}/status`);
}

export async function confirmSOS(sosId, { userId, lat, lng }) {
  return request(`/api/sos/${sosId}/confirm`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, lat, lng }),
  });
}

/* --- Location (F-04) --- */

export async function updateLocation({ userId, sosId, lat, lng, accuracy }) {
  return request('/api/location/update', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, sos_id: sosId, lat, lng, accuracy }),
  });
}

export async function getCachedLocation(userId) {
  return request(`/api/location/cached?user_id=${userId}`);
}

/* --- Services (F-07) --- */

export async function getNearbyServices({ lat, lng, type = 'hospital', radius = 5000 }) {
  return request(`/api/services/nearby?lat=${lat}&lng=${lng}&type=${type}&radius=${radius}`);
}

export async function getServiceTypes() {
  return request('/api/services/types');
}

export async function getServiceDetail(serviceId) {
  return request(`/api/services/${serviceId}`);
}

export async function getOfflinePack({ lat, lng }) {
  return request(`/api/services/offline-pack?lat=${lat}&lng=${lng}`);
}

/* --- Cache (F-08) --- */

export async function getEmergencyContacts() {
  return request('/api/cache/emergency-contacts');
}
