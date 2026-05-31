import EmergencyContacts from '../components/EmergencyContacts';

export default function ContactsPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Emergency Contacts</h1>
        <p className="page-subtitle">Tap to call — works offline</p>
      </div>
      <EmergencyContacts />
    </div>
  );
}
