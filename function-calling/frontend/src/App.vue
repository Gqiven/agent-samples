<template>
  <div id="app">
    <div class="header">
      <h1>Function Calling Agent Demo</h1>
    </div>

    <!-- Tools Bar -->
    <div class="tools-bar">
      <div
        v-for="t in tools"
        :key="t.name"
        class="tool-badge"
        :style="{ borderColor: t.color + '40' }"
      >
        <span class="icon">{{ t.icon }}</span>
        <span class="name" :style="{ color: t.color }">{{ t.name }}</span>
        <span class="desc">{{ t.description?.slice(0, 40) }}...</span>
      </div>
    </div>

    <div class="main">
      <!-- Chat Area -->
      <div class="chat-area">
        <div class="quick-actions">
          <button class="quick-btn" @click="quickSend('北京今天天气怎么样？')"><span class="tag">🌤️</span>查天气</button>
          <button class="quick-btn" @click="quickSend('搜索 LangChain 的最新信息')"><span class="tag">🔍</span>搜网络</button>
          <button class="quick-btn" @click="quickSend('计算 (2^10 + 100) / 3')"><span class="tag">🧮</span>算数学</button>
          <button class="quick-btn" @click="quickSend(`把'你好'翻译成英文`)"><span class="tag">🌐</span>翻译</button>
          <button class="quick-btn" @click="quickSend('北京天气如何？再把结果翻译成英文')"><span class="tag">🔗</span>组合调用</button>
          <button class="quick-btn" @click="quickSend('上海和深圳哪个城市更热？')"><span class="tag">📊</span>对比分析</button>
        </div>

        <div class="chat-container" ref="chatRef">
          <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
            <div class="avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
            <div class="bubble">{{ msg.content }}<span v-if="msg.streaming" class="typing-cursor"></span></div>
          </div>
        </div>

        <div class="input-area">
          <textarea
            v-model="input"
            placeholder="输入问题，Agent 会自动选择工具..."
            :disabled="loading"
            @keydown.enter.exact.prevent="send"
          />
          <button :disabled="loading || !input.trim()" @click="send">
            {{ loading ? '执行中' : '发送' }}
          </button>
        </div>
      </div>

      <!-- Trace Panel -->
      <div class="trace-area">
        <h2>Agent 执行追踪</h2>

        <!-- ReAct Flow -->
        <div class="flow-diagram">
          <template v-for="(step, i) in flowSteps" :key="i">
            <span :class="['flow-step', { 'flow-active': step.active }]">
              <span class="flow-node">{{ step.label }}</span>
            </span>
            <span v-if="i < flowSteps.length - 1" class="flow-arrow">→</span>
          </template>
        </div>

        <div class="trace-list" ref="traceRef">
          <div v-for="(t, i) in traces" :key="i" :class="['trace-step', t.type]">
            <div class="trace-header">
              <span class="trace-icon">{{ t.icon }}</span>
              <span class="trace-label">{{ t.label }}</span>
              <span v-if="t.toolName" class="trace-tool-name" :style="{ background: t.color + '30', color: t.color }">
                {{ t.toolName }}
              </span>
            </div>
            <div class="trace-content">{{ t.content }}</div>
            <div v-if="t.args" class="trace-args">{{ t.args }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue';

const API_BASE = '/api';
const chatRef = ref(null);
const traceRef = ref(null);
const input = ref('');
const loading = ref(false);
const messages = ref([]);
const traces = ref([]);
const tools = ref([]);
let msgId = 0;

const flowSteps = reactive([
  { label: 'Think', active: false },
  { label: 'Act', active: false },
  { label: 'Observe', active: false },
  { label: 'Answer', active: false },
]);

function resetFlow() {
  flowSteps.forEach(s => s.active = false);
}

function activateFlow(index) {
  flowSteps.forEach((s, i) => s.active = i <= index);
}

function scrollChat() {
  nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight; });
}
function scrollTrace() {
  nextTick(() => { if (traceRef.value) traceRef.value.scrollTop = traceRef.value.scrollHeight; });
}

function addMessage(role, content, streaming = false) {
  messages.value.push({ id: ++msgId, role, content, streaming });
  scrollChat();
}

function addTrace(type, content, toolName = '', args = '') {
  const icons = { tool_call: '🔧', tool_result: '📋', answer: '💡' };
  const labels = { tool_call: '工具调用', tool_result: '执行结果', answer: '最终回答' };
  const colors = { tool_call: '#f5a623', tool_result: '#53d769', answer: '#0099ff' };
  traces.value.push({
    type, content, toolName, args,
    icon: icons[type] || '•',
    label: labels[type] || type,
    color: colors[type] || '#999',
  });
  scrollTrace();
}

async function send() {
  const text = input.value.trim();
  if (!text || loading.value) return;
  input.value = '';
  quickSend(text);
}

async function quickSend(text) {
  if (loading.value) return;
  addMessage('user', text);
  const bubble = { id: ++msgId, role: 'assistant', content: '', streaming: true };
  messages.value.push(bubble);
  loading.value = true;
  traces.value = [];
  resetFlow();
  activateFlow(0);

  try {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let fullAnswer = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        try {
          const data = JSON.parse(line.slice(5).trim());
          if (data.type === 'tool_call') {
            activateFlow(1);
            addTrace('tool_call', `调用 ${data.tool_name}`, data.tool_name, JSON.stringify(data.tool_args, null, 2));
            bubble.content = `🔧 正在调用 ${data.tool_name}...`;
          } else if (data.type === 'tool_result') {
            activateFlow(2);
            addTrace('tool_result', data.content, data.tool_name);
            bubble.content = '📋 获取结果，继续推理...';
          } else if (data.type === 'answer') {
            activateFlow(3);
            fullAnswer += data.content;
            bubble.content = fullAnswer;
            addTrace('answer', data.content);
          } else if (data.type === 'done') {
            bubble.streaming = false;
          }
        } catch (e) {}
      }
      scrollChat();
    }
  } catch (err) {
    bubble.content = `错误: ${err.message}`;
    bubble.streaming = false;
  }
  loading.value = false;
  resetFlow();
}

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/tools`);
    const data = await res.json();
    tools.value = data.tools;
  } catch (e) {}
});
</script>