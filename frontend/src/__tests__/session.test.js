import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { refreshSession } from '../api/index'
import { getToken, saveSession, clearSession } from '../api/session'

describe('refreshSession', () => {
  beforeEach(() => clearSession())

  it('shares one refresh request between concurrent callers', async () => {
    saveSession({ token: 'old', refresh_token: 'r1' })
    const spy = vi.spyOn(axios, 'post').mockResolvedValue({ data: { code: 0, data: { token: 'new', refresh_token: 'r2', user: { id: 1 } } } })
    const [a, b] = await Promise.all([refreshSession(), refreshSession()])
    expect(a).toBe('new')
    expect(b).toBe('new')
    expect(spy).toHaveBeenCalledTimes(1)
    expect(getToken()).toBe('new')
    spy.mockRestore()
  })

  it('rejects when there is no refresh token', async () => {
    await expect(refreshSession()).rejects.toThrow()
  })
})
