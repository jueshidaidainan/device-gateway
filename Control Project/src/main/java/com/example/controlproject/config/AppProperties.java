package com.example.controlproject.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 应用配置属性。
 * 作用：承载网桥服务的端口、分包长度、WebSocket 路径等可配置参数。
 */
@ConfigurationProperties(prefix = "app.bridge")
public class AppProperties {
    private int biTcpPort = 3001;
    private int uniTcpPort = 3002;
    private int biWebSocketPort = 3003;
    private int uniWebSocketPort = 3004;
    private int maxFrameLength = 1024 * 2 * 64;
    private String webSocketPath = "/";

    public int getBiTcpPort() {
        return biTcpPort;
    }

    public void setBiTcpPort(int biTcpPort) {
        this.biTcpPort = biTcpPort;
    }

    public int getUniTcpPort() {
        return uniTcpPort;
    }

    public void setUniTcpPort(int uniTcpPort) {
        this.uniTcpPort = uniTcpPort;
    }

    public int getBiWebSocketPort() {
        return biWebSocketPort;
    }

    public void setBiWebSocketPort(int biWebSocketPort) {
        this.biWebSocketPort = biWebSocketPort;
    }

    public int getUniWebSocketPort() {
        return uniWebSocketPort;
    }

    public void setUniWebSocketPort(int uniWebSocketPort) {
        this.uniWebSocketPort = uniWebSocketPort;
    }

    public int getMaxFrameLength() {
        return maxFrameLength;
    }

    public void setMaxFrameLength(int maxFrameLength) {
        this.maxFrameLength = maxFrameLength;
    }

    public String getWebSocketPath() {
        return webSocketPath;
    }

    public void setWebSocketPath(String webSocketPath) {
        this.webSocketPath = webSocketPath;
    }
}
