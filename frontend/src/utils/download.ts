/** Trigger a browser download of in-memory text content. */
export function downloadTextFile(filename: string, content: string, mimeType: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: mimeType }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/** Trigger a browser download of a Blob (e.g. a server-generated PDF). */
export function downloadBlob(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Open the browser's print dialog for an HTML document ("Save as PDF").
 * Uses a hidden iframe, so no pop-up blocker gets in the way.
 */
export function printHtml(html: string): void {
  const frame = document.createElement('iframe')
  frame.setAttribute('aria-hidden', 'true')
  frame.style.cssText = 'position:fixed;width:0;height:0;border:0;right:0;bottom:0'
  frame.srcdoc = html
  frame.onload = () => {
    const win = frame.contentWindow
    if (!win) return
    // Give web fonts a moment so the printout matches the on-screen design.
    const ready = frame.contentDocument?.fonts?.ready ?? Promise.resolve()
    ready.then(() => {
      win.addEventListener('afterprint', () => frame.remove(), { once: true })
      win.focus()
      win.print()
    })
    // Fallback cleanup if afterprint never fires.
    window.setTimeout(() => frame.remove(), 120_000)
  }
  document.body.appendChild(frame)
}

/** Quote a CSV field; neutralise leading = + - @ so spreadsheets never run it as a formula. */
export function csvCell(value: string | number): string {
  const text = String(value)
  const safe = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text
  return `"${safe.replace(/"/g, '""')}"`
}
