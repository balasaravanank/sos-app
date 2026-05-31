import SOSTrigger from '../components/SOSTrigger';

export default function HomePage() {
  return (
    <div className="page-center">
      <div style={{ position: 'absolute', top: 32, left: 0, right: 0, textAlign: 'center' }}>
        <h1 className="text-xs text-uppercase text-muted" style={{ letterSpacing: '0.3em' }}>
          EMERGENCY SOS
        </h1>
      </div>
      <SOSTrigger />
    </div>
  );
}
