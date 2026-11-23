import { describe, it, expect } from 'vitest'
import { courseCode, domainKey, builtinIndex, isUrlAvatar, normalizePage, fmtMinutes } from '../utils'

describe('utils', () => {
  it('maps tech domain to a stable key and course code', () => {
    expect(domainKey('AI')).toBe('ai')
    expect(domainKey('未知方向')).toBe('other')
    expect(courseCode({ id: 7, tech_domain: 'AI' })).toBe('AI-107')
  })

  it('recognises avatar values', () => {
    expect(builtinIndex('builtin:3')).toBe(3)
    expect(builtinIndex('builtin:99')).toBe(0)
    expect(isUrlAvatar('https://a.com/x.png')).toBe(true)
    expect(isUrlAvatar('javascript:alert(1)')).toBe(false)
  })

  it('normalizes paginated and plain responses', () => {
    expect(normalizePage([1, 2]).items).toEqual([1, 2])
    expect(normalizePage({ total: 5, page: 2, size: 2, items: [1] }).total).toBe(5)
    expect(normalizePage(null).items).toEqual([])
  })

  it('formats minutes', () => {
    expect(fmtMinutes(0)).toBeTruthy()
    expect(fmtMinutes(125)).toContain('2')
  })
})
