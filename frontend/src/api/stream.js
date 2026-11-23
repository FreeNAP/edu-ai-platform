import { getToken } from './session'
import { pickMessage, refreshSession } from './index'

// POST 一个 SSE 接口，逐段回调 onEvent(event, data)；401 时刷新令牌后重试一次
export async function postStream(url, body, onEvent, { signal } = {}) {
  const send = () =>
    fetch(`/api${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify(body),
      signal
    })
  let res = await send()
  if (res.status === 401) {
    await refreshSession()
    res = await send()
  }
  if (!res.ok) {
    let data = null
    try {
      data = await res.json()
    } catch {
      /* 非 JSON */
    }
    const err = new Error(pickMessage(data, `请求失败（${res.status}）`))
    err.status = res.status
    throw err
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      let event = 'message'
      let data = ''
      for (const line of raw.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      onEvent(event, data ? JSON.parse(data) : {})
    }
  }
}
