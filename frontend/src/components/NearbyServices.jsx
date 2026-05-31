import { useState, useEffect, useCallback } from 'react';
import { getNearbyServices } from '../api/client';
import ServiceCard from './ServiceCard';
import { useToast } from './Toast';
import { AlertCircle, MapPin } from 'lucide-react';

const TYPES = [
  { key: 'hospital', label: 'Hospital' },
  { key: 'police', label: 'Police' },
  { key: 'ambulance', label: 'Ambulance' },
  { key: 'towing', label: 'Towing' },
  { key: 'puncture', label: 'Puncture' },
];

export default function NearbyServices() {
  const [activeType, setActiveType] = useState('hospital');
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userPos, setUserPos] = useState(null);
  const [error, setError] = useState(null);
  const toast = useToast();

  // Get user location once
  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      pos => setUserPos({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setUserPos({ lat: 13.0827, lng: 80.2707 }), // Chennai fallback
      { timeout: 5000 }
    );
  }, []);

  const fetchServices = useCallback(async (type) => {
    if (!userPos) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getNearbyServices({ lat: userPos.lat, lng: userPos.lng, type });
      setServices(res?.data?.services || []);
    } catch (err) {
      setError(err.message);
      toast('Failed to load services', 'error');
      setServices([]);
    } finally {
      setLoading(false);
    }
  }, [userPos, toast]);

  useEffect(() => {
    if (userPos) fetchServices(activeType);
  }, [activeType, userPos, fetchServices]);

  const handleTypeChange = (type) => {
    setActiveType(type);
  };

  return (
    <div className="stack stack-md">
      {/* Type Tabs */}
      <div className="tabs" id="service-tabs">
        {TYPES.map(t => (
          <button
            key={t.key}
            className={`tab${activeType === t.key ? ' active' : ''}`}
            onClick={() => handleTypeChange(t.key)}
            id={`tab-${t.key}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Services List */}
      {loading ? (
        <div className="stack stack-sm">
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton skeleton-block" style={{ height: 90 }} />
          ))}
        </div>
      ) : error ? (
        <div className="empty-state">
          <div className="empty-icon" style={{ display: 'flex' }}><AlertCircle size={48} /></div>
          <p className="text-secondary">{error}</p>
          <button className="btn btn-outline btn-sm" onClick={() => fetchServices(activeType)}>Retry</button>
        </div>
      ) : services.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon" style={{ display: 'flex' }}><MapPin size={48} /></div>
          <p className="text-secondary">No {activeType} services found nearby</p>
          <p className="text-sm text-muted">Try increasing the search radius or check another type.</p>
        </div>
      ) : (
        <div className="stack stack-sm">
          {services.map((svc, i) => (
            <div key={svc.id || svc.place_id || i} className={`anim-delay-${Math.min(i + 1, 5)}`}>
              <ServiceCard service={svc} userLat={userPos?.lat} userLng={userPos?.lng} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
