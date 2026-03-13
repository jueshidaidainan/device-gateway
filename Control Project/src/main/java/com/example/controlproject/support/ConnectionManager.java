package com.example.controlproject.support;

import com.fasterxml.jackson.databind.JsonNode;
import io.netty.channel.Channel;
import io.netty.handler.codec.http.websocketx.TextWebSocketFrame;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * 连接管理器。
 * 作用：维护设备 TCP 连接映射、双向 WebSocket 集合、单向 WebSocket 集合，
 * 并提供点对点发送与广播转发能力。
 */
public final class ConnectionManager {
    private final Map<String, Channel> biSocketMap = new ConcurrentHashMap<>();
    private final CopyOnWriteArraySet<Channel> biWebSockets = new CopyOnWriteArraySet<>();
    private final CopyOnWriteArraySet<Channel> uniWebSockets = new CopyOnWriteArraySet<>();

    public void registerBiWebSocket(Channel ch) {
        biWebSockets.add(ch);
    }

    public void removeBiWebSocket(Channel ch) {
        biWebSockets.remove(ch);
    }

    public void registerUniWebSocket(Channel ch) {
        uniWebSockets.add(ch);
    }

    public void removeUniWebSocket(Channel ch) {
        uniWebSockets.remove(ch);
    }

    public int biWebSocketCount() {
        return biWebSockets.size();
    }

    public String biWebSocketSnapshot() {
        return biWebSockets.toString();
    }

    // 广播设备上行数据到所有双向 WebSocket 客户端。
    public void broadcastToBiWebSocket(String data) {
        for (Channel ws : biWebSockets) {
            if (ws.isActive()) {
                ws.writeAndFlush(new TextWebSocketFrame(data));
            }
        }
    }

    // 广播推送数据到所有单向 WebSocket 客户端。
    public void broadcastToUniWebSocket(String data) {
        for (Channel ws : uniWebSockets) {
            if (ws.isActive()) {
                ws.writeAndFlush(new TextWebSocketFrame(data));
            }
        }
    }

    // 根据设备名找到 TCP 连接并下发控制指令。
    public void sendToBiSocket(String deviceName, JsonNode data) {
        Channel ch = biSocketMap.get(deviceName);
        if (ch == null || !ch.isActive()) {
            throw new IllegalStateException("设备 " + deviceName + " 的 Socket 连接不存在或已断开");
        }
        ch.writeAndFlush(BridgeSupport.frameJson(data));
    }

    // 注册设备 TCP 连接，若已存在则替换旧连接。
    public void registerBiSocket(String deviceName, Channel ch) {
        Channel old = biSocketMap.put(deviceName, ch);
        if (old != null && old != ch) {
            old.close();
        }
    }

    // 仅在当前连接匹配时移除设备映射，防止误删新连接。
    public void removeBiSocket(String deviceName, Channel ch) {
        if (deviceName != null) {
            biSocketMap.remove(deviceName, ch);
        }
    }
}
