import { useState, useEffect } from 'react';
import SOSStatus from '../components/SOSStatus';

export default function StatusPage() {
  const [sosData, setSosData] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('active_sos');
    if (stored) {
      try { setSosData(JSON.parse(stored)); } catch { /* ignore */ }
    }
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Status</h1>
        <p className="page-subtitle">Active emergency tracking</p>
      </div>
      <SOSStatus sosData={sosData} />
    </div>
  );
}
