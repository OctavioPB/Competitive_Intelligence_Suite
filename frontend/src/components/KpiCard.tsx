// KPI card — left gold accent bar (structural, always gold per design spec).
// Use valueColor prop to signal critical KPIs in red/orange — never change the bar colour.
export default function KpiCard({
  label,
  value,
  sub,
  valueColor,
}: {
  label: string
  value: string
  sub?: string
  valueColor?: string
}) {
  return (
    <div
      style={{
        backgroundColor: 'var(--white)',
        borderRadius: 'var(--radius-md)',
        padding: '28px',
        boxShadow: 'var(--shadow-card)',
        border: '1px solid var(--primary-10)',
        display: 'flex',
        alignItems: 'stretch',
        gap: 16,
      }}
    >
      {/* Structural accent bar — always gold, never a status colour */}
      <div
        style={{
          width: 3,
          backgroundColor: 'var(--gold)',
          borderRadius: 2,
          flexShrink: 0,
        }}
      />
      <div>
        <div
          style={{
            fontFamily: 'var(--fd)',
            fontSize: 30,
            fontWeight: 300,
            color: valueColor ?? 'var(--dark)',
            lineHeight: 1.15,
          }}
        >
          {value}
        </div>
        <div
          style={{
            fontFamily: 'var(--fb)',
            fontSize: 10,
            textTransform: 'uppercase',
            letterSpacing: '3px',
            color: 'var(--mid)',
            marginTop: 5,
          }}
        >
          {label}
        </div>
        {sub && (
          <div
            style={{
              fontFamily: 'var(--fb)',
              fontSize: 11,
              color: 'var(--mid)',
              marginTop: 2,
            }}
          >
            {sub}
          </div>
        )}
      </div>
    </div>
  )
}
