import { Navigation, Star } from 'lucide-react';

export default function ServiceCard({ service, userLat, userLng }) {
  const phone = service.phone || service.contact;
  const hasPhone = phone && phone.length > 1;
  const dirUrl = userLat && userLng
    ? `https://www.google.com/maps/dir/${userLat},${userLng}/${service.lat},${service.lng}`
    : `https://www.google.com/maps/search/?api=1&query=${service.lat},${service.lng}`;

  return (
    <div className="service-card anim-slide-up">
      <div className="service-info">
        <div className="service-name">{service.name}</div>
        {service.address && <div className="service-address">{service.address}</div>}
        <div className="service-meta">
          {service.distance_km != null && (
            <span><Navigation size={14} /> {service.distance_km} km</span>
          )}
          {service.rating && <span><Star size={14} /> {service.rating}</span>}
          {service.type && (
            <span style={{ textTransform: 'capitalize' }}>{service.type}</span>
          )}
        </div>
      </div>
      <div className="service-actions">
        {hasPhone && (
          <a href={`tel:${phone}`} className="service-call" aria-label={`Call ${service.name}`}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z" />
            </svg>
          </a>
        )}
        <a href={dirUrl} target="_blank" rel="noopener noreferrer" className="service-dir" aria-label={`Directions to ${service.name}`}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="3 11 22 2 13 21 11 13 3 11" />
          </svg>
        </a>
      </div>
    </div>
  );
}
