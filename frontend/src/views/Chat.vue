<template>
  <div>
    <el-card class="chat-card">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div>
            <div style="font-size: 16px; font-weight: bold">课程助手</div>
            <div style="margin-top: 4px; color: #909399; font-size: 12px">
              可以问我课表安排，我会调用真实课表数据
            </div>
          </div>
          <el-button text @click="clearChat">清空对话</el-button>
        </div>
      </template>

      <div ref="scrollRef" class="chat-body">
        <el-empty
          v-if="!messages.length"
          description="试试问我：我有什么课？"
        >
          <div class="quick-asks">
            <el-button size="small" @click="quickAsk('我有什么课？')">
              我有什么课？
            </el-button>
            <el-button size="small" @click="quickAsk('帮我看看这周的课表')">
              这周的课表
            </el-button>
            <el-button
              size="small"
              @click="quickAsk('帮我制定一份期末复习计划，重点复习数据结构和计算机网络，并保存')"
            >
              生成并保存计划
            </el-button>
          </div>
        </el-empty>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-row"
          :class="msg.role"
        >
          <div class="bubble">
            <div v-if="msg.role === 'user'">{{ msg.content }}</div>
            <div v-else>
              <div v-if="msg.status && !msg.content" class="thinking">
                {{ msg.status }}
              </div>
              <div v-else v-html="renderMarkdown(msg.content)"></div>

              <div v-if="msg.steps?.length" class="steps">
                <el-tag
                  v-for="(step, stepIndex) in msg.steps"
                  :key="stepIndex"
                  type="info"
                  size="small"
                >
                  {{ step.label }} · {{ step.summary }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="请输入问题，Enter 发送，Shift + Enter 换行"
          @keydown.enter.exact.prevent="send"
        />
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!input.trim()"
          @click="send"
        >
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'Chat' })

import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { streamChatApi } from '@/api/chat'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const scrollRef = ref()

// 模型输出必须经过 DOMPurify，避免 Markdown 里的 HTML 造成 XSS
const renderMarkdown = (text) => {
  return DOMPurify.sanitize(marked.parse(text || ''))
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  }
}

const send = async () => {
  const content = input.value.trim()
  if (!content || loading.value) return

  messages.value.push({ role: 'user', content })

  // 只带最近 20 条文字消息，工具过程不参与历史
  const history = messages.value
    .slice(-20)
    .map(({ role, content: text }) => ({ role, content: text }))

  // 先插入助手占位消息，后续 token 直接往这里追加
  const assistantIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    steps: [],
    status: '正在思考...'
  })

  input.value = ''
  loading.value = true
  await scrollToBottom()

  const updateAssistant = (fn) => {
    const msg = messages.value[assistantIndex]
    if (msg) fn(msg)
  }

  try {
    await streamChatApi(history, (event, data) => {
      if (event === 'status') {
        updateAssistant((msg) => {
          msg.status = data.message || ''
        })
      } else if (event === 'tool_start') {
        updateAssistant((msg) => {
          msg.status = `正在${data.label || '执行工具'}...`
          msg.steps.push({
            tool: data.tool,
            label: data.label,
            summary: '正在执行...'
          })
        })
      } else if (event === 'tool_end') {
        updateAssistant((msg) => {
          const step = [...msg.steps]
            .reverse()
            .find((item) => item.tool === data.tool)
          if (step) {
            step.summary = data.summary || '执行完成'
          } else {
            msg.steps.push({
              tool: data.tool,
              label: data.label,
              summary: data.summary || '执行完成'
            })
          }
          msg.status = '正在整理回答...'
        })
      } else if (event === 'token') {
        updateAssistant((msg) => {
          msg.status = ''
          msg.content += data.text || ''
        })
        scrollToBottom()
      } else if (event === 'done') {
        updateAssistant((msg) => {
          msg.status = ''
          if (!msg.content && data.reply) {
            msg.content = data.reply
          }
        })
        loading.value = false
        scrollToBottom()
      } else if (event === 'error') {
        updateAssistant((msg) => {
          msg.status = ''
          msg.content = data.message || 'AI 服务暂时不可用'
        })
        ElMessage.error(data.message || 'AI 服务暂时不可用')
        loading.value = false
      }
    })
  } catch (err) {
    updateAssistant((msg) => {
      msg.status = ''
      msg.content = err.message || '网络异常，请稍后重试'
    })
    ElMessage.error(err.message || '网络异常，请稍后重试')
  } finally {
    loading.value = false
    updateAssistant((msg) => {
      if (msg.status) msg.status = ''
      if (!msg.content) msg.content = '连接中断，请稍后重试'
    })
  }
}

const quickAsk = (text) => {
  input.value = text
  send()
}

const clearChat = () => {
  if (loading.value) return
  messages.value = []
  input.value = ''
}
</script>

<style scoped>
.chat-card {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}
.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 4px;
}
.message-row {
  display: flex;
  margin-bottom: 14px;
}
.message-row.user {
  justify-content: flex-end;
}
.message-row.assistant {
  justify-content: flex-start;
}
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 10px;
  line-height: 1.75;
  word-break: break-word;
}
.user .bubble {
  background: #409eff;
  color: #fff;
}
.assistant .bubble {
  background: #f4f4f5;
  color: #303133;
}
.thinking {
  color: #909399;
}
.steps {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.chat-input {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}
.chat-input .el-button {
  height: auto;
}
.quick-asks {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
