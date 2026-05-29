export default function Spinner() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        fontFamily: 'var(--fb)',
        fontSize: 12,
        color: 'var(--mid)',
        padding: '40px 0',
      }}
    >
      <div
        style={{
          width: 16,
          height: 16,
          borderRadius: '50%',
          border: '2px solid var(--primary-10)',
          borderTopColor: 'var(--gold)',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      Loading…
    </div>
  )
}
