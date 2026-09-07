# Interview walkthrough

## 60-second pitch

“这是一个制造业异常调查 Agent。主 Agent 负责意图、实体和风险判断，四个副 Agent 通过受控只读工具并行查询 MES、EAM、QMS、WMS；规则引擎做确定性校验，GraphRAG 负责多跳追溯，最终输出带引用的调查建议。涉及冻结批次、创建 NCR 的写操作不会由模型直接执行，而是生成带幂等键的人工审批草稿。”

## Suggested live demo

1. Start `python app.py` and open `http://127.0.0.1:8000`.
2. Use the first example question to show the complete incident flow.
3. Point out the four tool cards and their trace IDs / latency.
4. Point out that the expired calibration and leakage-rate limit are blocked by explicit rules.
5. Follow the GraphRAG path and source snippets to explain why the recommendation is evidence-based.
6. Click “模拟人工确认” and explain that it records a demo event only; it does not call a production write endpoint.

## Questions this demo answers

- **Why not let the LLM query the database directly?** Narrow tool contracts make permissions, parameters, timeouts and auditability enforceable.
- **Why use GraphRAG?** A graph is useful for deterministic relationships and multi-hop impact analysis; documents are better for SOP text and threshold context.
- **How do you prevent unsafe actions?** Separate read and write capabilities, apply rules before planning, require HITL for high-risk operations, and use idempotency keys.
- **How would you productionize it?** Add identity/RBAC, schema validation, retries/timeouts, data masking, persistent traces, evaluation datasets, and connectors to MES/QMS/EAM/WMS.
