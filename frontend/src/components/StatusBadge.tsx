// Pill-shaped status badge with 5px dot + label.
// Use semantic status colour tokens — never gold or navy here.
export default function StatusBadge({
  label,
  color,
  bg,
}: {
  label: string
  color: string
  bg: string
}) {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        backgroundColor: bg,
        borderRadius: 'var(--radius-pill)',
        padding: '2px 8px',
      }}
    >
      <div
        style={{
          width: 5,
          height: 5,
          borderRadius: '50%',
          backgroundColor: color,
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontFamily: 'var(--fb)',
          fontSize: 10,
          fontWeight: 600,
          textTransform: 'capitalize',
          letterSpacing: '1px',
          color,
        }}
      >
        {label}
      </span>
    </div>
  )
}
