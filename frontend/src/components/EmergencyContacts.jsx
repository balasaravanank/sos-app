import { useState, useEffect } from 'react';
import { getEmergencyContacts } from '../api/client';

const FALLBACK_CONTACTS = [
  { name: '108 Ambulance', phone: '108' },
  { name: '100 Police', phone: '100' },
  { name: '112 Emergency', phone: '112' },
  { name: '101 Fire Service', phone: '101' },
];

const CACHE_KEY = 'sos_emergency_contacts';

export default function EmergencyContacts() {
  const [contacts, setContacts] = useState([]);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    const loadContacts = async () => {
      // Try cache first
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        try { setContacts(JSON.parse(cached)); } catch { /* ignore */ }
      }

      // Try API
      try {
        const res = await getEmergencyContacts();
        const data = res?.data?.contacts || FALLBACK_CONTACTS;
        setContacts(data);
        localStorage.setItem(CACHE_KEY, JSON.stringify(data));
      } catch {
        // Use cached or fallback
        if (!cached) setContacts(FALLBACK_CONTACTS);
      }
    };
    loadContacts();
  }, []);

  return (
    <div className="stack stack-md">
      {/* Offline indicator */}
      {isOffline && (
        <div className="card anim-slide-up" style={{ borderColor: 'var(--accent-amber)', padding: 12 }}>
          <div className="row gap-sm">
            <span>⚡</span>
            <span className="text-sm text-amber">Offline — showing cached contacts</span>
          </div>
        </div>
      )}

      {/* Contact List */}
      <div className="stack stack-sm">
        {contacts.map((c, i) => (
          <a
            key={c.phone}
            href={`tel:${c.phone}`}
            className={`contact-card anim-slide-up anim-delay-${Math.min(i + 1, 5)}`}
            id={`contact-${c.phone}`}
          >
            <div className="contact-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z" />
              </svg>
            </div>
            <div className="contact-info">
              <div className="contact-name">{c.name}</div>
              <div className="contact-phone">{c.phone}</div>
            </div>
            <div className="contact-action">TAP TO CALL</div>
          </a>
        ))}
      </div>

      {/* Info */}
      <div className="text-center" style={{ padding: '16px 0' }}>
        <p className="text-xs text-muted">
          These contacts are cached locally and work without internet connection.
        </p>
      </div>
    </div>
  );
}
