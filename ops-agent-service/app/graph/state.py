from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    # 用户原始问题文本
    question: str
    # 当前诊断线程 ID，用于串联同一条分析链路
    thread_id: str
    # 解析后的时间范围，包含 start / end / step
    time_range: dict
    # 显式传入或从问题中提取出的设备 ID
    device_id: str | None
    # 显式传入或从问题中提取出的 topic ID
    topic_id: str | None
    # 标准化后的查询上下文，例如 metric_query / log_query
    normalized_query: dict
    # Prometheus 返回并整理后的指标证据
    metrics_evidence: dict
    # Loki 返回并整理后的日志证据
    log_evidence: dict
    # 网关运维接口返回的设备状态和事件证据
    gateway_evidence: dict
    # 基于规则层计算出的异常评估结果
    anomaly_assessment: dict
    # 最终返回给用户的结构化诊断结论
    final_answer: dict
