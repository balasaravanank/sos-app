import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { triggerSOS } from '../api/client';
import { useToast } from './Toast';

const MODES = [
  { key: 'emergency', label: 'Emergency', icon: '🚨', cls: 'emergency' },
  { key: 'injury', label: 'Injury', icon: '🩹', cls: 'injury' },
  { key: 'safety', label: 'Safety', icon: '🛡️', cls: 'safety' },
];

export default function SOSTrigger() {
  const [mode, setMode] = useState('emergency');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  const handleTrigger = useCallback(async () => {
    if (loading) return;
    setLoading(true);

    try {
      const position = await new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('Geolocation not supported'));
          return;
        }
        navigator.geolocation.getCurrentPosition(
          pos => resolve(pos),
          err => reject(err),
          { enableHighAccuracy: true, timeout: 10000 }
        );
      });

      const { latitude: lat, longitude: lng } = position.coords;
      const result = await triggerSOS({ type: mode, lat, lng });
      const sosId = result?.data?.sos_id;

      if (sosId) {
        localStorage.setItem('active_sos', JSON.stringify({
          sosId, type: mode, lat, lng, triggeredAt: new Date().toISOString(),
          data: result.data,
        }));
        toast('SOS triggered — help is on the way', 'success');
        navigate('/status');
      }
    } catch (err) {
      toast(err.message || 'Failed to trigger SOS', 'error');
    } finally {
      setLoading(false);
    }
  }, [mode, loading, navigate, toast]);

  return (
    <div className="stack stack-xl" style={{ alignItems: 'center' }}>
      {/* SOS Button */}
      <div className={`sos-ring type-${mode}`} onClick={handleTrigger} id="sos-trigger-ring">
        <button
          className={`sos-btn type-${mode}${loading ? ' loading' : ''}`}
          disabled={loading}
          id="sos-trigger-btn"
          aria-label={`Trigger ${mode} SOS`}
        >
          {loading ? (
            <>
              <span style={{ fontSize: '1.5rem' }}>⏳</span>
              <span className="sos-btn-label">LOCATING</span>
            </>
          ) : (
            <>
              SOS
              <span className="sos-btn-label">TAP TO TRIGGER</span>
            </>
          )}
        </button>
      </div>

      {/* Mode Selector */}
      <div className="mode-selector" id="mode-selector">
        {MODES.map(m => (
          <button
            key={m.key}
            className={`mode-btn ${m.cls}${mode === m.key ? ' active' : ''}`}
            onClick={() => setMode(m.key)}
            id={`mode-${m.key}`}
          >
            <span className="mode-icon">{m.icon}</span>
            {m.label}
          </button>
        ))}
      </div>

      {/* Instructions */}
      <div className="text-center anim-fade-in" style={{ maxWidth: 280 }}>
        <p className="text-sm text-secondary" style={{ lineHeight: 1.6 }}>
          {mode === 'emergency' && 'Dispatches nearest ambulance. ETA displayed after trigger.'}
          {mode === 'injury' && 'Locates nearest trauma center with directions.'}
          {mode === 'safety' && 'Alerts nearest police station silently.'}
        </p>
      </div>
    </div>
  );
}
