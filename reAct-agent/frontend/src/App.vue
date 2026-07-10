<template>
  <div id="app">
    <div class="header">
      <h1>ReAct Agent Demo</h1>
      <span class="react-badge">REACT</span>
    </div>

    <div class="main">
      <!-- Chat Area -->
      <div class="chat-area">
        <div class="quick-actions">
          <button class="quick-btn" @click="quickSend('北京今天天气怎么样？')">🌤️ 查天气</button>
          <button class="quick-btn" @click="quickSend('搜索 LangGraph 的核心概念')">🔍 搜索</button>
          <button class="quick-btn" @click="quickSend('计算 sqrt(144) + 2^10')">🧮 计算</button>
          <button class="quick-btn" @click="quickSend('现在几点了？')">🕐 时间</button>
          <button class="quick-btn" @click="quickSend('北京和上海哪个更热？')">📊 对比(多步)</button>
          <button class="quick-btn" @click="quickSend(`统计'LangChain是一个用于开发LLM应用的框架'的字数`)">📝 统计</button>
        </div>

        <div class="chat-container" ref="chatRef">
          <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
            <div class="avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
            <div class="bubble">{{ msg.content }}<span v-if="msg.streaming" class="typing-cursor"></span></div>
          </div>
        </div>

        <div class="input-area">
          <textarea v-model="input" placeholder="输入问题，ReAct Agent 会思考→行动→观察循环..." :disabled="loading" @keydown.enter.exact.prevent="send" />
          <button :disabled="loading || !input.trim()" @click="send">{{ loading ? '推理中' : '发送' }}</button>
        </div>
      </div>

      <!-- ReAct Trace -->
      <div class="trace-area">
        <div class="trace-header">
          <h2>ReAct 循环追踪</h2>

          <!-- Loop Indicator -->
          <div class="react-loop">
            <span :class="['react-phase', 'thought', { active: activePhase === 'thought' }]">Thought</span>
            <span class="react-loop-arrow">→</span>
            <span :class="['react-phase', 'action', { active: activePhase === 'action' }]">Action</span>
            <span class="react-loop-arrow">→</span>
            <span :class="['react-phase', 'observation', { active: activePhase === 'observation' }]">Observation</span>
            <span class="react-loop-arrow">→</span>
            <span :class="['react-phase', 'thought', { active: activePhase === 'answer' }]" style="background:var(--answer)">Answer</span>
          </div>

          <!-- Iteration Dots -->
          <div class="iteration-bar">
            <span>迭代: {{ currentIteration }}/{{ maxIterations }}</span>
            <div class="iteration-dots">
              <div
                v-for="i in maxIterations"
                :key="i"
                :class="['iteration-dot', { active: i <= currentIteration, current: i === currentIteration }]"
              />
            </div>
          </div>
        </div>

        <!-- State Diagram -->
        <div class="state-diagram">
          <svg viewBox="0 0 360 80" xmlns="http://www.w3.org/2000/svg">
            <!-- agent node -->
            <rect x="10" y="20" width="90" height="40" rx="8" :fill="activeNode === 'agent' ? '#c792ea' : '#1a1a3e'" :stroke="activeNode === 'agent' ? '#c792ea' : '#2a2a4e'" stroke-width="2"/>
            <text x="55" y="45" text-anchor="middle" :fill="activeNode === 'agent' ? '#000' : '#999'" font-size="13" font-weight="600">agent</text>

            <!-- conditional arrow -->
            <line x1="100" y1="40" x2="135" y2="40" stroke="#555" stroke-width="1.5" stroke-dasharray="4"/>
            <text x="117" y="35" text-anchor="middle" fill="#999" font-size="9">条件边</text>

            <!-- tools node -->
            <rect x="135" y="20" width="80" height="40" rx="8" :fill="activeNode === 'tools' ? '#f5a623' : '#1a1a3e'" :stroke="activeNode === 'tools' ? '#f5a623' : '#2a2a4e'" stroke-width="2"/>
            <text x="175" y="45" text-anchor="middle" :fill="activeNode === 'tools' ? '#000' : '#999'" font-size="13" font-weight="600">tools</text>

            <!-- loop arrow: tools → agent -->
            <path d="M175 60 Q175 75 55 75 Q10 75 10 60" fill="none" :stroke="activeNode === 'loop' ? '#53d769' : '#333'" stroke-width="1.5" stroke-dasharray="4"/>
            <text x="92" y="78" text-anchor="middle" fill="#555" font-size="9">循环</text>

            <!-- END -->
            <rect x="260" y="20" width="80" height="40" rx="8" :fill="activeNode === 'end' ? '#0099ff' : '#1a1a3e'" :stroke="activeNode === 'end' ? '#0099ff' : '#2a2a4e'" stroke-width="2"/>
            <text x="300" y="45" text-anchor="middle" :fill="activeNode === 'end' ? '#fff' : '#999'" font-size="13" font-weight="600">END</text>

            <!-- agent → END arrow -->
            <line x1="100" y1="30" x2="260" y2="30" stroke="#555" stroke-width="1" stroke-dasharray="4"/>
            <text x="180" y="25" text-anchor="middle" fill="#999" font-size="9">无工具调用</text>
          </svg>
        </div>

        <!-- Trace Steps -->
        <div class="trace-list" ref="traceRef">
          <div v-for="(t, i) in traces" :key="i" :class="['trace-step', t.type]">
            <div class="trace-step-header">
              <span class="trace-step-icon">{{ t.icon }}</span>
              <span class="trace-step-label">{{ t.label }}</span>
              <span v-if="t.iteration" style="font-size:10px;color:#555;">迭代 #{{ t.iteration }}</span>
              <span v-if="t.toolName" class="trace-step-badge">{{ t.toolName }}</span>
            </div>
            <div class="trace-step-body">
              {{ t.content }}
              <div v-if="t.args" class="trace-args">{{ t.args }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';

const API_BASE = '/api';
const chatRef = ref(null);
const traceRef = ref(null);
const input = ref('');
const loading = ref(false);
const messages = ref([]);
const traces = ref([]);
const activePhase = ref('');
const activeNode = ref('');
const currentIteration = ref(0);
const maxIterations = ref(6);
let msgId = 0;

function scrollChat() { nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight; }); }
function scrollTrace() { nextTick(() => { if (traceRef.value) traceRef.value.scrollTop = traceRef.value.scrollHeight; }); }

function addMessage(role, content, streaming = false) {
  messages.value.push({ id: ++msgId, role, content, streaming });
  scrollChat();
}

function addTrace(type, content, iteration = 0, toolName = '', args = '') {
  const config = {
    thought:  { icon: '💭', label: 'THOUGHT' },
    action:   { icon: '🔧', label: 'ACTION' },
    observation: { icon: '👁️', label: 'OBSERVATION' },
    answer:   { icon: '💡', label: 'ANSWER' },
  };
  const c = config[type] || { icon: '•', label: type.toUpperCase() };
  traces.value.push({ type, content, iteration, toolName, args, icon: c.icon, label: c.label });
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
  activePhase.value = 'thought';
  activeNode.value = 'agent';
  currentIteration.value = 0;

  try {
    // SSE处理：不是用传统的 EventSource，而是用 fetch + ReadableStream 的方式
    /**
     * 
      为什么用 fetch 而不是 EventSource？

      ┌───────────────┬──────────────┬───────────────────────────────┐
      │               │ EventSource  │        fetch + reader         │
      ├───────────────┼──────────────┼───────────────────────────────┤
      │ 请求方式      │ 仅支持 GET   │ 支持 POST（可传 JSON body）   │
      ├───────────────┼──────────────┼───────────────────────────────┤
      │ 自定义 header │ ❌ 不支持    │ ✅ 支持 Content-Type 等       │
      ├───────────────┼──────────────┼───────────────────────────────┤
      │ 错误处理      │ 有限         │ 完全可控                      │
      ├───────────────┼──────────────┼───────────────────────────────┤
      │ 连接关闭检测  │ onerror 事件 │ reader.read() 返回 done: true │
      └───────────────┴──────────────┴───────────────────────────────
      后端是 POST /api/chat/stream，需要传 { message, max_iterations } 的 JSON body，
      所以必须用 fetch 方式，EventSource 做不到。
      本质都是解析 data: 前缀的 SSE 流，只是读取方式不同。
     */
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, max_iterations: 6 }),
    });
    // SSE 的手动解析
    const reader = res.body.getReader(); // 获取流式 reader
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
        if (!line.startsWith('data:')) continue; // SSE 格式：跳过非 data 行
        try {
          const data = JSON.parse(line.slice(5).trim()); // 去掉 "data:" 前缀，解析 JSON

          if (data.max_iterations) maxIterations.value = data.max_iterations;

          if (data.type === 'action') {
            activePhase.value = 'action';
            activeNode.value = 'tools';
            currentIteration.value = data.iteration || currentIteration.value;
            addTrace('action', `调用 ${data.action_name}`, data.iteration, data.action_name, JSON.stringify(data.action_args, null, 2));
            bubble.content = `🔧 [迭代#${data.iteration}] 调用 ${data.action_name}...`;
          } else if (data.type === 'observation') {
            activePhase.value = 'observation';
            activeNode.value = 'loop';
            addTrace('observation', data.content, data.iteration, data.action_name);
            bubble.content = `👁️ [迭代#${data.iteration}] 观察结果，继续推理...`;
          } else if (data.type === 'answer') {
            activePhase.value = 'answer';
            activeNode.value = 'end';
            fullAnswer += data.content;
            bubble.content = fullAnswer;
            addTrace('answer', data.content, data.iteration);
          } else if (data.type === 'done') {
            bubble.streaming = false;
            activeNode.value = 'end';
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
}

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/tools`);
    const data = await res.json();
    // 可用 tools 数据
  } catch (e) {}
});
</script>