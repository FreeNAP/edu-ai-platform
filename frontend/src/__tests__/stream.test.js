import { describe, it, expect, vi, beforeEach } from 'vitest'
import { postStream } from '../api/stream'

function sseResponse(chunks, status = 200) {
  const enc = new TextEncoder()
  let i = 0
  return {
    ok: status < 400,
    status,
    json: async () => ({ detail: '今天的 AI 使用次数已用完' }),
    body: { getReader: () => ({ read: async () => (i < chunks.length ? { value: enc.encode(chunks[i++]), done: false } : { done: true }) }) }
  }
}

describe('postStream', () => {
  beforeEach(() => localStorage.setItem('token', 't'))

  it('parses events split across chunks', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(sseResponse([
      'event: meta\ndata: {"session_id": 9}\n\nevent: del',
      'ta\ndata: {"text": "你好"}\n\nevent: done\ndata: {}\n\n'
    ]))
    const events = []
    await postStream('/ai/chat/stream', { message: 'hi' }, (e, d) => events.push([e, d]))
    expect(events).toEqual([['meta', { session_id: 9 }], ['delta', { text: '你好' }], ['done', {}]])
  })

  it('throws the server message on errors', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(sseResponse([], 429))
    await expect(postStream('/ai/chat/stream', {}, () => {})).rejects.toThrow('今天的 AI 使用次数已用完')
  })
})
