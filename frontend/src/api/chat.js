import request from '@/utils/request'
import { getToken, logout } from '@/utils/auth'

/**
 * 非流式聊天，保留用于调试和降级
 */
export function sendChatApi(messages) {
  return request({
    url: '/api/chat',
    method: 'post',
    data: { messages }
  })
}

/**
 * SSE 流式聊天
 * onEvent(event, data) 会收到 status/tool_start/tool_end/token/done/error
 */
export async function streamChatApi(messages, onEvent) {
  const token = getToken()
  const baseURL = import.meta.env.VITE_API_BASE_URL || ''

  const response = await fetch(`${baseURL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ messages })
  })

  if (response.status === 401) {
    logout()
    window.location.href = '/login'
    throw new Error('登录已失效')
  }

  if (!response.ok || !response.body) {
    let message = '请求失败'
    try {
      const data = await response.json()
      message = data.message || message
    } catch {
      // 忽略非 JSON 错误响应
    }
    throw new Error(message)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''

    for (const block of blocks) {
      const lines = block.split('\n')
      const eventLine = lines.find((line) => line.startsWith('event:'))
      const dataLine = lines.find((line) => line.startsWith('data:'))
      if (!eventLine || !dataLine) continue

      const event = eventLine.slice(6).trim()
      const payload = JSON.parse(dataLine.slice(5).trim())
      onEvent(event, payload)
    }
  }
}
