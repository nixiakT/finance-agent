"""（本课程已弃用本地部署）

原计划在 Day5 本地部署 GLM-4-9B 并封装 OpenAI 兼容后端。
现课程方案改为**直接调用 DeepSeek API** 作为 mini-OpenClaw 的大脑，不再本地部署模型。

请使用 backend/client.py 的 DeepSeekBackend。
本文件保留仅作占位，若你想把 API 再包一层（加重试/日志/限流/统一受限解码），可在这里做。
"""
