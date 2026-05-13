import { describe, expect, it } from 'vitest'
import { joinApiPath } from './api'
import { normalizePhoneDigits } from './phone'

describe('normalizePhoneDigits', () => {
  it('strips non-digits', () => {
    expect(normalizePhoneDigits('+7 (771) 677-41-85')).toBe('77716774185')
  })
})

describe('joinApiPath', () => {
  it('returns root-relative path when origin empty', () => {
    expect(joinApiPath('', '/api/foo')).toBe('/api/foo')
    expect(joinApiPath(undefined, 'api/foo')).toBe('/api/foo')
  })

  it('strips trailing slash on origin', () => {
    expect(joinApiPath('http://localhost:8000/', '/api/v1')).toBe('http://localhost:8000/api/v1')
  })
})
