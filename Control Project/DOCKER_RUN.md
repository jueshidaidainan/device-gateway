# Docker 使用说明

## 1. 构建镜像

```bash
docker build -t control-project:1.0 .
```

## 2. 运行容器（docker run）

```bash
docker run -d \
  --name control-project \
  -p 3001:3001 \
  -p 3002:3002 \
  -p 3003:3003 \
  -p 3004:3004 \
  control-project:1.0
```

## 3. 查看日志

```bash
docker logs -f control-project
```

## 4. 停止并删除容器

```bash
docker stop control-project
docker rm control-project
```

## 5. Docker Compose 方式

### 启动

```bash
docker compose up -d --build
```

### 查看日志

```bash
docker compose logs -f
```

### 停止

```bash
docker compose down
```
<!-- 两阶段构建（multi-stage）的原因：

第一阶段用 Maven 镜像编译打包（需要 JDK + Maven）。
第二阶段只放运行所需的 JRE + jar。
好处：

镜像更小
攻击面更低
启动更快、传输更快
不把源码和构建工具带进生产镜像 -->
