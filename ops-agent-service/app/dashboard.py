from __future__ import annotations


def build_dashboard_html(*, app_name: str) -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="light dark" />
  <title>__APP_NAME__</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f3efe6;
      --bg-top: #faf7f1;
      --bg-orb-left: rgba(15, 118, 110, 0.10);
      --bg-orb-right: rgba(210, 141, 30, 0.14);
      --panel: rgba(255, 251, 245, 0.88);
      --panel-strong: #fffaf2;
      --surface: rgba(255, 255, 255, 0.60);
      --surface-strong: rgba(255, 255, 255, 0.86);
      --text: #1d2a2f;
      --text-soft: #385055;
      --muted: #667b80;
      --line: rgba(43, 67, 72, 0.14);
      --accent: #0f766e;
      --accent-soft: rgba(15, 118, 110, 0.14);
      --danger: #b5473c;
      --warning: #d28d1e;
      --ok: #2d7b48;
      --eyebrow-bg: rgba(29, 42, 47, 0.06);
      --ghost-bg: rgba(29, 42, 47, 0.06);
      --input-bg: rgba(255, 255, 255, 0.86);
      --button-shadow: 0 10px 24px rgba(15, 118, 110, 0.26);
      --note-bg: rgba(210, 141, 30, 0.10);
      --note-text: #87570d;
      --warn-badge-bg: rgba(210, 141, 30, 0.10);
      --warn-badge-text: #9c6811;
      --chart-grid: rgba(43, 67, 72, 0.10);
      --chart-fill-start: rgba(15, 118, 110, 0.24);
      --chart-fill-end: rgba(15, 118, 110, 0.02);
      --chart-current: #0f766e;
      --chart-baseline: #d28d1e;
      --shadow: 0 20px 60px rgba(27, 44, 54, 0.10);
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #091218;
        --bg-top: #0f1b23;
        --bg-orb-left: rgba(14, 165, 155, 0.18);
        --bg-orb-right: rgba(245, 158, 11, 0.12);
        --panel: rgba(13, 25, 33, 0.82);
        --panel-strong: rgba(16, 30, 40, 0.92);
        --surface: rgba(20, 36, 47, 0.86);
        --surface-strong: rgba(15, 28, 38, 0.96);
        --text: #e8f1f3;
        --text-soft: #bfd1d6;
        --muted: #96adb4;
        --line: rgba(163, 191, 198, 0.14);
        --accent: #31c5b7;
        --accent-soft: rgba(49, 197, 183, 0.16);
        --danger: #ff7b72;
        --warning: #f3b348;
        --ok: #54c677;
        --eyebrow-bg: rgba(232, 241, 243, 0.08);
        --ghost-bg: rgba(232, 241, 243, 0.08);
        --input-bg: rgba(8, 18, 25, 0.72);
        --button-shadow: 0 14px 34px rgba(3, 14, 19, 0.42);
        --note-bg: rgba(243, 179, 72, 0.14);
        --note-text: #ffd693;
        --warn-badge-bg: rgba(243, 179, 72, 0.14);
        --warn-badge-text: #ffd693;
        --chart-grid: rgba(150, 173, 180, 0.18);
        --chart-fill-start: rgba(49, 197, 183, 0.30);
        --chart-fill-end: rgba(49, 197, 183, 0.04);
        --chart-current: #31c5b7;
        --chart-baseline: #f3b348;
        --shadow: 0 24px 60px rgba(0, 0, 0, 0.34);
      }
    }

    * { box-sizing: border-box; }

    html {
      color-scheme: light dark;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, var(--bg-orb-left), transparent 26%),
        radial-gradient(circle at top right, var(--bg-orb-right), transparent 22%),
        linear-gradient(180deg, var(--bg-top) 0%, var(--bg) 100%);
    }

    a { color: inherit; }

    .shell {
      width: min(1720px, calc(100vw - 32px));
      max-width: none;
      margin: 0 auto;
      padding: 20px 0 40px;
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(360px, 0.95fr);
      gap: 24px;
      align-items: stretch;
      margin-bottom: 24px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .hero-card {
      padding: 28px;
      position: relative;
      overflow: hidden;
    }

    .hero-card::after {
      content: "";
      position: absolute;
      inset: auto -80px -120px auto;
      width: 220px;
      height: 220px;
      background: radial-gradient(circle, var(--accent-soft), transparent 70%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--eyebrow-bg);
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0.04em;
    }

    h1 {
      margin: 16px 0 12px;
      font-size: clamp(30px, 5vw, 52px);
      line-height: 1.02;
      letter-spacing: -0.04em;
    }

    .hero-copy {
      max-width: 720px;
      font-size: 16px;
      line-height: 1.7;
      color: var(--text-soft);
      margin-bottom: 20px;
    }

    .hero-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .metric-chip {
      border-radius: 18px;
      padding: 14px 16px;
      background: var(--surface);
      border: 1px solid var(--line);
    }

    .metric-chip strong {
      display: block;
      font-size: 24px;
      margin-top: 6px;
    }

    .hero-side {
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      justify-content: space-between;
      background:
        linear-gradient(145deg, var(--accent-soft), transparent 52%),
        var(--panel-strong);
    }

    .mini-title {
      margin: 0 0 10px;
      font-size: 15px;
      color: var(--muted);
    }

    .topology {
      display: grid;
      gap: 10px;
    }

    .node {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 12px 14px;
      border-radius: 16px;
      background: var(--surface);
      border: 1px solid var(--line);
    }

    .dot {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: var(--warning);
      box-shadow: 0 0 0 6px rgba(210, 141, 30, 0.14);
    }

    .dot.ok {
      background: var(--ok);
      box-shadow: 0 0 0 6px rgba(45, 123, 72, 0.14);
    }

    .dot.bad {
      background: var(--danger);
      box-shadow: 0 0 0 6px rgba(181, 71, 60, 0.14);
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(420px, 500px) minmax(0, 1fr);
      gap: 24px;
      align-items: start;
    }

    .stack {
      display: grid;
      gap: 24px;
      align-content: start;
    }

    .section {
      padding: 22px;
    }

    .section h2 {
      margin: 0 0 14px;
      font-size: 18px;
    }

    .help {
      margin: 0 0 16px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
    }

    .field-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .field {
      display: grid;
      gap: 8px;
    }

    .field.full {
      grid-column: 1 / -1;
    }

    label {
      font-size: 13px;
      color: var(--muted);
    }

    input, textarea, select {
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: var(--input-bg);
      padding: 13px 14px;
      font: inherit;
      color: inherit;
    }

    input::placeholder,
    textarea::placeholder {
      color: var(--muted);
    }

    textarea {
      min-height: 112px;
      resize: vertical;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }

    button {
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease, box-shadow 120ms ease;
    }

    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.6; cursor: progress; }

    .primary {
      background: var(--accent);
      color: white;
      box-shadow: var(--button-shadow);
    }

    .secondary {
      background: var(--accent-soft);
      color: var(--accent);
    }

    .ghost {
      background: var(--ghost-bg);
      color: var(--text);
    }

    .status-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .status-card {
      padding: 14px;
      border-radius: 16px;
      background: var(--surface);
      border: 1px solid var(--line);
    }

    .status-card p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }

    .status-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-weight: 600;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      background: var(--warn-badge-bg);
      color: var(--warn-badge-text);
    }

    .badge.ok {
      background: rgba(45, 123, 72, 0.10);
      color: var(--ok);
    }

    .badge.bad {
      background: rgba(181, 71, 60, 0.10);
      color: var(--danger);
    }

    .result-shell {
      display: grid;
      gap: 24px;
      align-items: start;
    }

    .summary-card {
      grid-column: 1 / -1;
      padding: 24px;
      background:
        linear-gradient(145deg, rgba(255,255,255,0.04), transparent),
        var(--panel);
    }

    .summary-top {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 220px;
      align-items: start;
      gap: 24px;
      margin-bottom: 16px;
    }

    .summary-title {
      font-size: 27px;
      margin: 4px 0 8px;
      letter-spacing: -0.03em;
    }

    .confidence {
      min-width: 0;
      padding: 14px 16px;
      border-radius: 18px;
      background: var(--surface);
      border: 1px solid var(--line);
      align-self: stretch;
    }

    .confidence strong {
      display: block;
      font-size: 32px;
      margin-top: 6px;
    }

    .bar {
      height: 12px;
      background: var(--ghost-bg);
      border-radius: 999px;
      overflow: hidden;
      margin-top: 12px;
    }

    .bar > span {
      display: block;
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--chart-baseline), var(--chart-current));
      border-radius: 999px;
    }

    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    .pill {
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
    }

    .data-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
      gap: 24px;
      align-items: stretch;
    }

    .chart-wrap {
      padding: 20px;
      border-radius: 20px;
      background: var(--surface);
      border: 1px solid var(--line);
      min-height: 440px;
    }

    .chart-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 13px;
    }

    svg {
      width: 100%;
      height: 320px;
      overflow: visible;
    }

    .legend {
      display: flex;
      gap: 16px;
      margin-top: 10px;
      font-size: 13px;
      color: var(--muted);
    }

    .legend span::before {
      content: "";
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 999px;
      margin-right: 8px;
      vertical-align: -1px;
    }

    .legend .current::before { background: var(--chart-current); }
    .legend .baseline::before { background: var(--chart-baseline); }

    .list-card {
      padding: 20px;
      border-radius: 20px;
      background: var(--surface);
      border: 1px solid var(--line);
    }

    .evidence-card {
      min-height: 440px;
      display: flex;
      flex-direction: column;
    }

    .evidence-card h2 {
      margin-bottom: 18px;
    }

    #nextSteps {
      flex: 1 1 auto;
      align-content: start;
    }

    .evidence-card .inline-note {
      margin-top: auto;
    }

    .list-card ul {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
      line-height: 1.55;
    }

    .list-card pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.5;
    }

    .inline-note {
      margin-top: 14px;
      padding: 12px 14px;
      border-radius: 14px;
      background: var(--note-bg);
      color: var(--note-text);
      font-size: 13px;
      line-height: 1.6;
    }

    .footer-note {
      margin-top: 16px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .mono {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }

    @media (max-width: 1380px) {
      .layout {
        grid-template-columns: minmax(380px, 460px) minmax(0, 1fr);
      }

      .result-shell {
        grid-template-columns: 1fr;
      }

      .data-grid,
      .summary-card {
        grid-column: auto;
        grid-row: auto;
      }
    }

    @media (max-width: 980px) {
      .shell {
        width: calc(100vw - 20px);
      }

      .hero, .layout, .data-grid, .result-shell { grid-template-columns: 1fr; }
      .hero-grid, .status-grid, .field-grid { grid-template-columns: 1fr; }
      .summary-top { grid-template-columns: 1fr; }
      .confidence { width: 100%; }
      svg { height: 260px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel hero-card">
        <div class="eyebrow">Device Gateway · LangGraph Agent · Demo Console</div>
        <h1>设备网关运维诊断台</h1>
        <p class="hero-copy">
          这个页面是给当前项目定制的演示首页，不再直接暴露通用 Swagger 作为第一视觉。
          你可以在这里发起一次流量异常分析、模拟告警解释，并把结果以更接近面试展示的方式看到。
        </p>
        <div class="hero-grid">
          <div class="metric-chip">
            当前定位
            <strong>Ops Agent</strong>
          </div>
          <div class="metric-chip">
            主要职责
            <strong>诊断流量异常</strong>
          </div>
          <div class="metric-chip">
            演示入口
            <strong>/ 与 /api/docs</strong>
          </div>
        </div>
      </div>
      <aside class="panel hero-side">
        <div>
          <p class="mini-title">项目链路</p>
          <div class="topology">
            <div class="node"><span class="dot ok"></span><strong>Control Project</strong><span>网关控制面</span></div>
            <div class="node"><span class="dot ok"></span><strong>Exporter Project</strong><span>指标采集与转发</span></div>
            <div class="node"><span class="dot" id="agent-status-dot"></span><strong>Ops Agent Service</strong><span id="agent-status-text">等待健康检查</span></div>
          </div>
        </div>
        <div class="inline-note">
          如果现在没有 Prometheus、Loki 或 Java 网关服务，这个页面依然可以演示 Agent 的接口流程。
          页面中的趋势图会展示本地 mock 可视化，接口结论则来自真实的 FastAPI 返回。
        </div>
      </aside>
    </section>

    <section class="layout">
      <div class="stack">
        <div class="panel section">
          <h2>发起一次诊断</h2>
          <p class="help">
            这部分对应 Agent 的两个核心入口：流量分析和告警解释。
            你可以直接改输入参数，然后点击按钮看项目定制后的结果展示。
          </p>
          <div class="field-grid">
            <div class="field full">
              <label for="question">问题描述</label>
              <textarea id="question">帮我看看 device-101 最近 1 小时 topic-7 的流量是不是异常，顺便解释一下可能原因。</textarea>
            </div>
            <div class="field">
              <label for="deviceId">设备 ID</label>
              <input id="deviceId" value="device-101" />
            </div>
            <div class="field">
              <label for="topicId">Topic ID</label>
              <input id="topicId" value="topic-7" />
            </div>
            <div class="field">
              <label for="lookback">回看分钟数</label>
              <input id="lookback" type="number" min="1" max="1440" value="60" />
            </div>
            <div class="field">
              <label for="alertSummary">告警摘要</label>
              <input id="alertSummary" value="Traffic dropped below expected threshold for the last hour" />
            </div>
          </div>
          <div class="actions">
            <button id="analyzeBtn" class="primary">运行流量分析</button>
            <button id="alertBtn" class="secondary">模拟告警解释</button>
            <button id="demoBtn" class="ghost">载入演示场景</button>
          </div>
          <p class="footer-note">
            原始接口文档仍然保留在 <a href="/api/docs" target="_blank" rel="noreferrer">/api/docs</a>，
            适合开发联调时查看请求结构和 schema。
          </p>
        </div>

        <div class="panel section">
          <h2>依赖状态</h2>
          <p class="help">
            这里直接读取 <span class="mono">GET /agent/health</span> 的结果。
            如果后端观测系统没启动，你会看到服务处于可演示但数据源缺失的降级状态。
          </p>
          <div class="status-grid" id="healthGrid"></div>
        </div>
      </div>

      <div class="result-shell">
        <div class="panel summary-card">
          <div class="summary-top">
            <div>
              <div class="eyebrow" id="modeBadge">等待请求</div>
              <div class="summary-title" id="summaryTitle">还没有运行诊断</div>
              <div id="summaryText" class="help" style="font-size:15px; margin:0;">
                点击左侧按钮后，这里会展示面向项目演示的总结，而不是直接暴露原始 JSON。
              </div>
              <div class="pill-row" id="reasonPills"></div>
            </div>
            <div class="confidence">
              诊断置信度
              <strong id="confidenceValue">0%</strong>
              <div class="bar"><span id="confidenceBar"></span></div>
            </div>
          </div>
          <div class="inline-note" id="degradedNote" style="display:none;"></div>
        </div>

        <div class="data-grid">
          <div class="panel chart-wrap">
            <div class="chart-meta">
              <span id="chartDevice">设备: -</span>
              <span id="chartTopic">Topic: -</span>
              <span id="chartWindow">窗口: -</span>
            </div>
            <svg id="trafficChart" viewBox="0 0 620 260" preserveAspectRatio="none" aria-label="Traffic chart"></svg>
            <div class="legend">
              <span class="current">当前窗口</span>
              <span class="baseline">前一天基线</span>
            </div>
            <div class="footer-note">
              曲线是本地演示可视化，用来把 Agent 的结论讲清楚。
              当真实 Prometheus 接入后，这里可以替换成真实时序数据。
            </div>
          </div>

          <div class="panel list-card evidence-card">
            <h2 style="margin-top:0;">建议与证据</h2>
            <ul id="nextSteps">
              <li>等待一次分析结果。</li>
            </ul>
            <div class="inline-note" style="margin-top:16px;">
              <strong>证据摘要</strong>
              <pre id="evidenceBlock">尚未生成。</pre>
            </div>
          </div>
        </div>

      </div>
    </section>
  </div>

  <script>
    const state = {
      latestResponse: null,
      chartConfig: null,
    };

    const healthGrid = document.getElementById("healthGrid");
    const modeBadge = document.getElementById("modeBadge");
    const summaryTitle = document.getElementById("summaryTitle");
    const summaryText = document.getElementById("summaryText");
    const reasonPills = document.getElementById("reasonPills");
    const confidenceValue = document.getElementById("confidenceValue");
    const confidenceBar = document.getElementById("confidenceBar");
    const degradedNote = document.getElementById("degradedNote");
    const nextSteps = document.getElementById("nextSteps");
    const evidenceBlock = document.getElementById("evidenceBlock");
    const agentStatusDot = document.getElementById("agent-status-dot");
    const agentStatusText = document.getElementById("agent-status-text");

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function setBusy(button, busyText) {
      button.dataset.originalText = button.textContent;
      button.textContent = busyText;
      button.disabled = true;
    }

    function clearBusy(button) {
      button.textContent = button.dataset.originalText;
      button.disabled = false;
    }

    function cssVar(name, fallback) {
      const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return value || fallback;
    }

    function setDemoScenario() {
      document.getElementById("question").value = "请分析 device-204 最近 2 小时 topic-22 的流量异常，并结合网关状态给出解释。";
      document.getElementById("deviceId").value = "device-204";
      document.getElementById("topicId").value = "topic-22";
      document.getElementById("lookback").value = "120";
      document.getElementById("alertSummary").value = "Device throughput dropped abruptly after repeated disconnect warnings";
      renderChart({
        deviceId: "device-204",
        topicId: "topic-22",
        minutes: 120,
        anomalous: true,
      });
    }

    function seedFromText(text) {
      let hash = 0;
      for (const char of text) {
        hash = ((hash << 5) - hash + char.charCodeAt(0)) | 0;
      }
      return Math.abs(hash) + 1;
    }

    function buildSeries(seed, count, base, variance, dropIndex, dropScale) {
      const points = [];
      for (let i = 0; i < count; i += 1) {
        const wave = Math.sin((i + seed) / 2.8) * variance;
        const trend = Math.cos((i + seed) / 5.4) * variance * 0.45;
        let value = base + wave + trend;
        if (dropIndex >= 0 && i >= dropIndex) {
          value *= dropScale;
        }
        points.push(Math.max(2, Math.round(value * 10) / 10));
      }
      return points;
    }

    function linePath(points, width, height, min, max) {
      return points.map((point, index) => {
        const x = (index / (points.length - 1)) * width;
        const y = height - ((point - min) / (max - min || 1)) * height;
        return (index === 0 ? "M" : "L") + x.toFixed(2) + "," + y.toFixed(2);
      }).join(" ");
    }

    function renderChart({ deviceId, topicId, minutes, anomalous }) {
      state.chartConfig = { deviceId, topicId, minutes, anomalous };
      const svg = document.getElementById("trafficChart");
      const width = 620;
      const height = 220;
      const seed = seedFromText(deviceId + topicId + minutes);
      const points = 16;
      const baseline = buildSeries(seed, points, anomalous ? 84 : 62, anomalous ? 6 : 4, -1, 1);
      const current = buildSeries(seed + 19, points, anomalous ? 80 : 60, anomalous ? 9 : 5, anomalous ? 10 : -1, anomalous ? 0.38 : 1);
      const max = Math.max(...baseline, ...current) + 10;
      const min = Math.min(...baseline, ...current) - 8;
      const currentPath = linePath(current, width, height, min, max);
      const baselinePath = linePath(baseline, width, height, min, max);
      const chartGrid = cssVar("--chart-grid", "rgba(43,67,72,0.10)");
      const chartFillStart = cssVar("--chart-fill-start", "rgba(15,118,110,0.24)");
      const chartFillEnd = cssVar("--chart-fill-end", "rgba(15,118,110,0.02)");
      const chartCurrent = cssVar("--chart-current", "#0f766e");
      const chartBaseline = cssVar("--chart-baseline", "#d28d1e");
      const chartText = cssVar("--muted", "#667b80");

      const gridLines = [0, 0.25, 0.5, 0.75, 1].map((tick) => {
        const y = 220 - 220 * tick;
        return '<line x1="0" y1="' + y + '" x2="620" y2="' + y + '" stroke="' + chartGrid + '" stroke-dasharray="4 6" />';
      }).join("");

      svg.innerHTML = ''
        + '<defs>'
        + '  <linearGradient id="fillCurrent" x1="0" y1="0" x2="0" y2="1">'
        + '    <stop offset="0%" stop-color="' + chartFillStart + '" />'
        + '    <stop offset="100%" stop-color="' + chartFillEnd + '" />'
        + '  </linearGradient>'
        + '</defs>'
        + gridLines
        + '<path d="' + baselinePath + '" fill="none" stroke="' + chartBaseline + '" stroke-width="3" stroke-linecap="round" />'
        + '<path d="' + currentPath + ' L620,220 L0,220 Z" fill="url(#fillCurrent)" stroke="none" />'
        + '<path d="' + currentPath + '" fill="none" stroke="' + chartCurrent + '" stroke-width="4" stroke-linecap="round" />'
        + '<text x="0" y="248" fill="' + chartText + '" font-size="12">窗口起点</text>'
        + '<text x="560" y="248" fill="' + chartText + '" font-size="12">当前时刻</text>';

      document.getElementById("chartDevice").textContent = "设备: " + (deviceId || "-");
      document.getElementById("chartTopic").textContent = "Topic: " + (topicId || "-");
      document.getElementById("chartWindow").textContent = "窗口: 最近 " + minutes + " 分钟";
    }

    function renderHealth(health) {
      const overallOk = Boolean(health.ok);
      agentStatusDot.className = "dot " + (overallOk ? "ok" : "bad");
      agentStatusText.textContent = overallOk ? "实时依赖可用" : "Agent 可运行，但部分依赖缺失";

      healthGrid.innerHTML = health.components.map((component) => {
        const klass = component.ok ? "ok" : "bad";
        const label = component.ok ? "已连接" : "未就绪";
        const message = escapeHtml(component.message || "");
        return ''
          + '<article class="status-card">'
          + '  <div class="status-head">'
          + '    <span>' + escapeHtml(component.name) + '</span>'
          + '    <span class="badge ' + klass + '">' + label + '</span>'
          + '  </div>'
          + '  <p>' + message + '</p>'
          + '</article>';
      }).join("");
    }

    function renderResponse(mode, data) {
      state.latestResponse = data;
      const confidence = Math.round((data.confidence || 0) * 100);
      const anomalous = Boolean(data.is_anomalous);
      const summary = data.summary || "未返回摘要";
      const reasons = data.suspected_causes && data.suspected_causes.length
        ? data.suspected_causes
        : (data.assessment && data.assessment.reasons && data.assessment.reasons.length ? data.assessment.reasons : ["当前没有明确的异常证据"]);

      modeBadge.textContent = mode === "alert" ? "模拟告警解释" : "流量分析结果";
      summaryTitle.textContent = anomalous ? "检测到需要关注的异常信号" : "当前窗口未确认明显异常";
      summaryText.textContent = summary;
      confidenceValue.textContent = confidence + "%";
      confidenceBar.style.width = confidence + "%";

      reasonPills.innerHTML = reasons.map((reason) => '<span class="pill">' + escapeHtml(reason) + '</span>').join("");

      const degradedReasons = (data.assessment && data.assessment.degraded_reasons) || [];
      if (degradedReasons.length) {
        degradedNote.style.display = "block";
        degradedNote.textContent = "当前是降级演示模式，缺失的数据源: " + degradedReasons.join(" / ");
      } else {
        degradedNote.style.display = "none";
      }

      nextSteps.innerHTML = (data.next_steps || ["暂无建议"]).map((step) => '<li>' + escapeHtml(step) + '</li>').join("");
      evidenceBlock.textContent = (data.evidence || [])
        .map((item) => '[' + item.source + '] ' + item.title + ': ' + item.detail)
        .join("\\n\\n") || "暂无证据。";

      if (data.normalized_query) {
        const query = data.normalized_query;
        renderChart({
          deviceId: query.device_id || document.getElementById("deviceId").value,
          topicId: query.topic_id || document.getElementById("topicId").value,
          minutes: Number(document.getElementById("lookback").value || 60),
          anomalous,
        });
      }
    }

    async function loadHealth() {
      const response = await fetch("/agent/health");
      if (!response.ok) {
        throw new Error("health request failed");
      }
      const data = await response.json();
      renderHealth(data);
      return data;
    }

    function analyzePayload() {
      return {
        question: document.getElementById("question").value,
        device_id: document.getElementById("deviceId").value || null,
        topic_id: document.getElementById("topicId").value || null,
        time_range: {
          lookback_minutes: Number(document.getElementById("lookback").value || 60),
        },
      };
    }

    async function postJson(url, payload) {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "request failed");
      }
      return response.json();
    }

    document.getElementById("analyzeBtn").addEventListener("click", async (event) => {
      const button = event.currentTarget;
      setBusy(button, "分析中...");
      try {
        const data = await postJson("/agent/analyze", analyzePayload());
        renderResponse("analyze", data);
      } catch (error) {
        summaryTitle.textContent = "分析失败";
        summaryText.textContent = String(error.message || error);
      } finally {
        clearBusy(button);
      }
    });

    document.getElementById("alertBtn").addEventListener("click", async (event) => {
      const button = event.currentTarget;
      setBusy(button, "解释中...");
      try {
        const payload = {
          labels: {
            alertname: "GatewayTrafficDrop",
            device_id: document.getElementById("deviceId").value || "device-101",
            topic_id: document.getElementById("topicId").value || "topic-7",
          },
          annotations: {
            summary: document.getElementById("alertSummary").value,
          },
          time_range: {
            lookback_minutes: Number(document.getElementById("lookback").value || 60),
          },
        };
        const data = await postJson("/agent/explain-alert", payload);
        renderResponse("alert", data);
      } catch (error) {
        summaryTitle.textContent = "告警解释失败";
        summaryText.textContent = String(error.message || error);
      } finally {
        clearBusy(button);
      }
    });

    document.getElementById("demoBtn").addEventListener("click", setDemoScenario);

    setDemoScenario();
    if (window.matchMedia) {
      const colorSchemeMedia = window.matchMedia("(prefers-color-scheme: dark)");
      const rerenderChart = () => {
        if (state.chartConfig) {
          renderChart(state.chartConfig);
        }
      };
      if (typeof colorSchemeMedia.addEventListener === "function") {
        colorSchemeMedia.addEventListener("change", rerenderChart);
      } else if (typeof colorSchemeMedia.addListener === "function") {
        colorSchemeMedia.addListener(rerenderChart);
      }
    }
    loadHealth().catch((error) => {
      healthGrid.innerHTML = '<article class="status-card"><div class="status-head"><span>health</span><span class="badge bad">失败</span></div><p>' + escapeHtml(String(error.message || error)) + '</p></article>';
    });
  </script>
</body>
</html>
""".replace("__APP_NAME__", app_name)
