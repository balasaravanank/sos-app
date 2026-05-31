import { useState, useEffect, useCallback } from 'react';
import { getSOSStatus, confirmSOS } from '../api/client';
import { useToast } from './Toast';
import StatusBadge from './StatusBadge';
import { Radio, ExternalLink, Check } from 'lucide-react';

export default function SOSStatus({ sosData }) {
  const [status, setStatus] = useState(sosData || null);
  const [confirming, setConfirming] = useState(false);
  const toast = useToast();

  const sosId = sosData?.sosId;
  const data = sosData?.data || {};

  // Poll status every 5 seconds
  useEffect(() => {
    if (!sosId) return;
    let active = true;

    const poll = async () => {
      try {
        const res = await getSOSStatus(sosId);
        if (active && res?.data) setStatus(prev => ({ ...prev, ...res.data }));
      } catch { /* silent */ }
    };

    poll();
    const interval = setInterval(poll, 5000);
    return () => { active = false; clearInterval(interval); };
  }, [sosId]);

  const handleConfirm = useCallback(async () => {
    if (confirming || !sosId) return;
    setConfirming(true);
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
      });
      await confirmSOS(sosId, {
        userId: 'bystander-' + Date.now(),
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      });
      toast('Confirmation sent — thank you', 'success');
    } catch (err) {
      toast(err.message || 'Failed to confirm', 'error');
    } finally {
      setConfirming(false);
    }
  }, [sosId, confirming, toast]);

  const handleClear = () => {
    localStorage.removeItem('active_sos');
    window.location.reload();
  };

  if (!sosData) {
    return (
      <div className="empty-state anim-fade-in">
        <div className="empty-icon" style={{ display: 'flex' }}><Radio size={48} /></div>
        <p className="text-secondary">No active SOS</p>
        <p className="text-sm text-muted">Trigger an SOS from the home screen to see status here.</p>
      </div>
    );
  }

  const statusText = status?.status || sosData?.type || 'active';
  const ambulance = data.nearest_ambulance;
  const trauma = data.nearest_trauma_center;
  const station = data.nearest_station;
  const etaMsg = data.eta_message;
  const directions = data.directions_url;

  return (
    <div className="stack stack-lg anim-slide-up">
      {/* Hero Status */}
      <div className="status-hero">
        <div className="status-id">ID: {sosId?.slice(0, 12)}</div>
        <div className={`status-type text-${sosData.type === 'emergency' ? 'red' : sosData.type === 'injury' ? 'amber' : 'green'}`}>
          {sosData.type?.toUpperCase()} SOS
        </div>
        <StatusBadge status={statusText} />

        {ambulance && (
          <div style={{ marginTop: 24 }}>
            <div className="status-eta">{ambulance.eta_mins}<span style={{ fontSize: '1.25rem' }}>min</span></div>
            <div className="status-eta-label">Estimated Arrival</div>
          </div>
        )}

        {etaMsg && !ambulance && (
          <p className="text-sm text-secondary" style={{ marginTop: 16 }}>{etaMsg}</p>
        )}
      </div>

      {/* Dispatch Info */}
      <div className="card">
        <div className="text-xs text-uppercase text-muted" style={{ marginBottom: 12 }}>Dispatch Info</div>

        {ambulance && (
          <>
            <div className="info-row">
              <span className="info-label">Unit ID</span>
              <span className="info-value text-mono">{ambulance.unit_id?.slice(0, 8)}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Contact</span>
              <a href={`tel:${ambulance.contact}`} className="info-value text-green">{ambulance.contact}</a>
            </div>
            <div className="info-row">
              <span className="info-label">Zone</span>
              <span className="info-value">{ambulance.zone}</span>
            </div>
          </>
        )}

        {trauma && (
          <>
            <div className="info-row">
              <span className="info-label">Hospital</span>
              <span className="info-value">{trauma.name}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Distance</span>
              <span className="info-value">{trauma.distance_km} km</span>
            </div>
            <div className="info-row">
              <span className="info-label">Phone</span>
              <a href={`tel:${trauma.phone}`} className="info-value text-green">{trauma.phone}</a>
            </div>
          </>
        )}

        {station && (
          <>
            <div className="info-row">
              <span className="info-label">Station</span>
              <span className="info-value">{station.name}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Contact</span>
              <a href={`tel:${station.contact}`} className="info-value text-green">{station.contact}</a>
            </div>
            {station.eta_mins && (
              <div className="info-row">
                <span className="info-label">ETA</span>
                <span className="info-value">{station.eta_mins} min</span>
              </div>
            )}
          </>
        )}

        {!ambulance && !trauma && !station && (
          <p className="text-sm text-muted">Dispatch details will appear shortly.</p>
        )}
      </div>

      {/* Location */}
      {sosData.lat && (
        <div className="card">
          <div className="text-xs text-uppercase text-muted" style={{ marginBottom: 12 }}>Your Location</div>
          <div className="info-row">
            <span className="info-label">Latitude</span>
            <span className="info-value text-mono">{sosData.lat?.toFixed(6)}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Longitude</span>
            <span className="info-value text-mono">{sosData.lng?.toFixed(6)}</span>
          </div>
          <div className="info-row" style={{ borderBottom: 'none' }}>
            <span className="info-label">Triggered</span>
            <span className="info-value text-mono text-sm">
              {new Date(sosData.triggeredAt).toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}

      {/* Directions */}
      {directions && (
        <a href={directions} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-block" id="btn-directions">
          <ExternalLink size={18} /> OPEN DIRECTIONS
        </a>
      )}

      {/* Confirm (bystander) */}
      <button className="btn btn-outline btn-block" onClick={handleConfirm} disabled={confirming} id="btn-confirm">
        {confirming ? 'CONFIRMING...' : <><Check size={18} /> CONFIRM THIS EMERGENCY</>}
      </button>

      {/* Clear */}
      <button className="btn btn-ghost btn-block text-muted" onClick={handleClear} id="btn-clear">
        CLEAR SOS
      </button>
    </div>
  );
}
