# Docker 使用说明

## 1. 构建镜像
```bash
docker build -t exporter-project:latest .
```

## 2. 运行容器
```bash
docker run -d \
  --name exporter-project \
  -p 12345:12345 \
  -p 12346:12346 \
  exporter-project:latest
```

说明：
- `12345` 是 TCP 流量接入端口
- `12346` 是 Spring Boot/Prometheus 指标端口（`/actuator/prometheus`）

## 3. 查看日志
```bash
docker logs -f exporter-project
```

## 4. 验证指标端点
```bash
curl http://localhost:12346/actuator/prometheus
```

## 5. 停止并删除容器
```bash
docker stop exporter-project
docker rm exporter-project
```
