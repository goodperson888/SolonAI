# 流式输出实现文档

## 问题描述
之前的实现虽然使用了 SSE，但 AI 回复不是逐字实时输出，而是等待整个回复生成完成后一次性展示。

## 根本原因
后端使用 `workflow.ainvoke()` 阻塞式调用，等待整个 LangGraph 工作流完成后才返回结果，然后再拆分成词发送。这不是真正的流式输出。

## 解决方案

### 1. 后端流式架构 (services/ai-agents/graphs/main_graph.py)

创建新的 `run_agent_stream()` 异步生成器函数，使用 LangGraph 的 `astream_events()` API：

```python
async def run_agent_stream(
    user_input: str,
    wallet_address: str = "",
    session_id: str = "",
    chat_history: list = None,
    thread_id: str = None,
):
    """流式运行 Agent 工作流，实时返回 LLM token"""
    workflow = get_workflow()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}

    initial_state = _build_initial_state(
        user_input, wallet_address, session_id, chat_history
    )

    # 使用 astream_events 捕获所有事件
    async for event in workflow.astream_events(initial_state, config=config, version="v2"):
        kind = event.get("event")

        # 捕获 LLM token 流
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield {"type": "token", "data": {"token": content}}

        # 捕获最终状态
        elif kind == "on_chain_end" and event.get("name") == "LangGraph":
            output = event.get("data", {}).get("output", {})
            yield {"type": "data", "data": output}
```

**关键点**：
- 使用 `astream_events()` 而非 `ainvoke()`
- 监听 `on_chat_model_stream` 事件捕获 LLM 生成的每个 token
- 使用 `yield` 实时返回 token，而非等待完成

### 2. API 层修改 (apps/api/app/api/v1/chat.py)

修改 `/message/stream` 端点使用新的流式函数：

```python
@router.post("/message/stream")
async def chat_message_stream(request: ChatRequest):
    """流式对话接口（SSE）"""
    run_agent_stream = get_run_agent_stream()

    async def event_generator():
        session_id = request.session_id or str(uuid.uuid4())
        yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

        async for event in run_agent_stream(
            user_input=request.message,
            wallet_address=request.wallet_address,
            session_id=session_id,
            chat_history=chat_history,
        ):
            event_type = event.get("type")
            event_data = event.get("data", {})

            if event_type == "token":
                yield f"event: token\ndata: {json.dumps(event_data)}\n\n"
            elif event_type == "data":
                yield f"event: data\ndata: {json.dumps(event_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 3. 前端处理 (apps/web/src/lib/api-client.ts)

前端已有正确的 SSE 处理逻辑：

```typescript
sendMessageStream(
  request: ChatRequest,
  callbacks: {
    onToken?: (token: string) => void
    onSession?: (sessionId: string) => void
    onData?: (data: any) => void
    onError?: (error: string) => void
  }
) {
  const eventSource = new EventSource(
    `${this.baseURL}/chat/message/stream?${params}`
  )

  eventSource.addEventListener('token', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onToken?.(data.token)
  })

  // ... 其他事件处理
}
```

### 4. UI 更新 (apps/web/src/app/ai/page.tsx)

在 `onToken` 回调中逐字追加内容：

```typescript
onToken: (token) => {
  setIsLoading(false)
  setConversations((prev) =>
    prev.map((conv) => {
      if (conv.id !== currentActiveId) return conv
      return {
        ...conv,
        messages: conv.messages.map((msg) =>
          msg.id === aiMessageId
            ? { ...msg, content: msg.content + token }  // 逐字追加
            : msg
        ),
      }
    })
  )
}
```

## 测试验证

使用 curl 测试流式输出：

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","wallet_address":"test123"}'
```

预期输出（逐个 token 实时发送）：
```
event: session
data: {"session_id":"xxx"}

event: token
data: {"token":"嗨"}

event: token
data: {"token":"，"}

event: token
data: {"token":"你好"}

event: token
data: {"token":"！"}

event: data
data: {"intent":"greeting","response":"嗨，你好！"}
```

## 技术要点

1. **LangGraph 流式 API**：`astream_events(version="v2")` 提供细粒度的事件流
2. **事件类型**：
   - `on_chat_model_stream`：LLM 生成的每个 token
   - `on_chain_end`：工作流完成时的最终状态
3. **SSE 协议**：使用 `event: type\ndata: json\n\n` 格式
4. **前端状态管理**：使用 `content + token` 逐字追加，触发 React 重渲染

## 相关文件

- `services/ai-agents/graphs/main_graph.py` - 流式工作流实现
- `apps/api/app/api/v1/chat.py` - SSE 端点
- `apps/web/src/lib/api-client.ts` - SSE 客户端
- `apps/web/src/app/ai/page.tsx` - UI 更新逻辑
- `apps/web/src/components/chat/MessageBubble.tsx` - Markdown 渲染

## 其他改进

1. **Markdown 解析**：使用 `react-markdown` 和 `remark-gfm` 解析 AI 回复
2. **思考状态**：添加 `hasReceivedToken` 状态，只在等待首个 token 时显示"正在思考"
3. **知识库集成**：ExplanationAgent 自动调用 RAG 检索用户上传的文档
