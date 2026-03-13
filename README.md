# DeviceGateway

一个包含两个模块的设备通信与指标导出仓库：

## 1. Control Project
- TCP(3001/3002) 与 WebSocket(3003/3004) 的桥接网关
- 支持按 `device_name` 定向控制下发与实时广播推送
- STX/ETX 协议分包与异常帧保护
- 配置分层（AppConfig/AppProperties）+ Docker/Compose 部署

目录：`Control Project/`

## 2. Exporter project
- TCP 数据采集与批处理消费（`take + drainTo`）
- Micrometer 动态指标注册，输出 Prometheus 监控指标
- 长度字段协议解码与分片拼接
- Docker 镜像与运行文档

目录：`Exporter project/`

---

如需快速启动：
- `Control Project/DOCKER_RUN.md`
- `Exporter project/DOCKER.md`
