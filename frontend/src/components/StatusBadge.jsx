export default function StatusBadge({ status }) {
  const map = {
    active: { cls: 'badge-red', label: 'Active', dot: true },
    verified: { cls: 'badge-green', label: 'Verified', dot: false },
    resolved: { cls: 'badge-green', label: 'Resolved', dot: false },
    pending: { cls: 'badge-amber', label: 'Pending', dot: true },
  };
  const config = map[status] || map.pending;

  return (
    <span className={`badge ${config.cls}`} id="status-badge">
      {config.dot && <span className={`pulse-dot${status === 'active' ? '' : ' pulse-dot-green'}`} />}
      {config.label}
    </span>
  );
}
