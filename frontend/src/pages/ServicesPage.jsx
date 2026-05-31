import NearbyServices from '../components/NearbyServices';

export default function ServicesPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Nearby Services</h1>
        <p className="page-subtitle">Hospitals, police & emergency services near you</p>
      </div>
      <NearbyServices />
    </div>
  );
}
