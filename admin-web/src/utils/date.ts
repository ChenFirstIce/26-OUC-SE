const HAS_TIMEZONE = /(Z|[+-]\d{2}:?\d{2})$/i

export function parseApiDate(value: string | Date): Date {
  if (value instanceof Date) return value
  // SQLite historically returned UTC timestamps without an offset. Treat those
  // values as UTC before converting them to the browser's local timezone.
  return new Date(HAS_TIMEZONE.test(value) ? value : `${value}Z`)
}

export function formatDateTime(value?: string | Date | null): string {
  if (!value) return '—'
  const date = parseApiDate(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('zh-CN', { hour12: false })
}

export function formatDate(value?: string | Date | null): string {
  if (!value) return '—'
  const date = parseApiDate(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('zh-CN')
}
