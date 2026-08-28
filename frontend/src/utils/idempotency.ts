/**
 * 生成提交幂等键。
 *
 * crypto.randomUUID 在部分旧版手机浏览器以及局域网 HTTP 页面中不可用，
 * 因此先使用 randomUUID，再降级到 getRandomValues，最后使用时间戳随机串。
 * 幂等键只要求单次提交足够唯一，不作为访问凭证使用。
 */
export function createIdempotencyKey(): string {
  const browserCrypto = globalThis.crypto as (Crypto & { randomUUID?: () => string }) | undefined
  if (typeof browserCrypto?.randomUUID === 'function') {
    return browserCrypto.randomUUID()
  }
  if (typeof browserCrypto?.getRandomValues === 'function') {
    const bytes = new Uint8Array(16)
    browserCrypto.getRandomValues(bytes)
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
  }
  return `fallback-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`
}

