const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ========== Conversations ==========
export interface ConversationListItem {
  id: number
  title: string
  group_tag: string
  first_message?: string
  message_count: number
  updated_at?: string
}

export interface Conversation {
  id: number
  title: string
  group_tag: string
  model_config_id?: number | null
  project_path: string
  file_paths: string
  created_at?: string
  updated_at?: string
}

export const convApi = {
  list: (tag?: string) =>
    request<ConversationListItem[]>(`/conversations${tag ? `?tag=${encodeURIComponent(tag)}` : ''}`),
  create: (data?: Partial<Conversation>) =>
    request<Conversation>('/conversations', { method: 'POST', body: JSON.stringify(data || {}) }),
  get: (id: number) => request<Conversation>(`/conversations/${id}`),
  update: (id: number, data: Partial<Conversation>) =>
    request<Conversation>(`/conversations/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<{ ok: boolean }>(`/conversations/${id}`, { method: 'DELETE' }),
}

// ========== Messages ==========
export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
}

export const msgApi = {
  list: (convId: number) => request<Message[]>(`/conversations/${convId}/messages`),
}

// ========== Chat (SSE via POST + ReadableStream) ==========
export interface SSEEvent {
  event?: string
  content?: string
  message_id?: number
  session_id?: string
  error?: string
}

export function sendMessageStream(
  convId: number,
  content: string,
): { abort: () => void; stream: AsyncIterable<SSEEvent> } {
  const abortController = new AbortController()

  const body: Record<string, unknown> = { content }

  const stream = {
    [Symbol.asyncIterator]() {
      let reader: ReadableStreamDefaultReader<Uint8Array> | null = null
      let started = false

      return {
        async next(): Promise<IteratorResult<SSEEvent>> {
          if (!started) {
            started = true
            const res = await fetch(`${BASE}/chat/${convId}/send`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(body),
              signal: abortController.signal,
            })

            if (!res.ok) {
              const err = await res.json().catch(() => ({ detail: 'Request failed' }))
              throw new Error(err.detail || `HTTP ${res.status}`)
            }

            reader = res.body!.getReader()
          }

          if (!reader) return { done: true, value: undefined }

          const decoder = new TextDecoder()
          let buffer = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) return { done: true, value: undefined }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const dataStr = line.slice(6)
                try {
                  const data = JSON.parse(dataStr)
                  return { done: false, value: data }
                } catch { /* skip */ }
              }
            }
          }
        },
      }
    },
  }

  return { abort: () => abortController.abort(), stream }
}

// ========== Context ==========
export const contextApi = {
  readFiles: (paths: string[]) =>
    request<Record<string, string>>('/context/read-files', {
      method: 'POST', body: JSON.stringify({ paths }),
    }),
  scanDir: (path: string, maxDepth = 3) =>
    request<{ tree: string }>('/context/scan-dir', {
      method: 'POST', body: JSON.stringify({ path, max_depth: maxDepth }),
    }),
}
