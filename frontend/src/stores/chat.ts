import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { convApi, msgApi, sendMessageStream, type Conversation, type Message, type ConversationListItem } from '@/api'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<ConversationListItem[]>([])
  const currentConvId = ref<number | null>(null)
  const currentConv = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const error = ref<string | null>(null)
  const activeTag = ref('')

  const currentTitle = computed(() => currentConv.value?.title || '新对话')

  async function loadConversations(tag?: string) {
    conversations.value = await convApi.list(tag)
  }

  async function createConversation() {
    const conv = await convApi.create()
    await loadConversations()
    await selectConversation(conv.id)
    return conv
  }

  async function selectConversation(id: number) {
    currentConvId.value = id
    currentConv.value = await convApi.get(id)
    messages.value = await msgApi.list(id)
    streamingContent.value = ''
    error.value = null
  }

  async function deleteConversation(id: number) {
    await convApi.delete(id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      currentConv.value = null
      messages.value = []
    }
    await loadConversations()
  }

  async function sendUserMessage(content: string) {
    if (!currentConvId.value) return
    error.value = null
    isStreaming.value = true
    streamingContent.value = ''

    messages.value.push({
      id: Date.now(),
      conversation_id: currentConvId.value,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    })

    try {
      const { stream } = sendMessageStream(currentConvId.value, content)
      let fullContent = ''

      for await (const event of stream) {
        if (event.content) {
          fullContent += event.content
          streamingContent.value = fullContent
        } else if (event.message_id || event.session_id) {
          break
        } else if (event.error) {
          throw new Error(event.error)
        }
      }

      // 流结束，添加完整回复
      if (fullContent) {
        messages.value.push({
          id: Date.now() + 1,
          conversation_id: currentConvId.value,
          role: 'assistant',
          content: fullContent,
          created_at: new Date().toISOString(),
        })
      }

      // 刷新会话列表以更新标题和时间
      await loadConversations(activeTag.value || undefined)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '请求失败'
      error.value = msg
    } finally {
      isStreaming.value = false
      streamingContent.value = ''
    }
  }

  async function updateConversation(data: Partial<Conversation>) {
    if (!currentConvId.value) return
    currentConv.value = await convApi.update(currentConvId.value, data)
    await loadConversations(activeTag.value || undefined)
  }

  function setActiveTag(tag: string) {
    activeTag.value = tag
  }

  return {
    conversations,
    currentConvId,
    currentConv,
    messages,
    isStreaming,
    streamingContent,
    error,
    activeTag,
    currentTitle,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    sendUserMessage,
    updateConversation,
    setActiveTag,
  }
})
