export default function Toast({
  message,
  type,
}: {
  message: string
  type: 'success' | 'error' | 'warning'
}) {
  const palette = {
    success: {
      text:   'var(--status-green)',
      bg:     'var(--status-green-bg)',
      border: 'rgba(39,185,124,0.25)',
    },
    error: {
      text:   'var(--status-red)',
      bg:     'var(--status-red-bg)',
      border: 'rgba(224,52,72,0.25)',
    },
    warning: {
      text:   'var(--status-orange)',
      bg:     'var(--status-orange-bg)',
      border: 'rgba(240,112,32,0.25)',
    },
  }[type]

  return (
    <div
      style={{
        fontFamily: 'var(--fb)',
        fontSize: 12,
        color: palette.text,
        backgroundColor: palette.bg,
        border: `1px solid ${palette.border}`,
        borderRadius: 8,
        padding: '10px 16px',
        marginTop: 16,
      }}
    >
      {message}
    </div>
  )
}
