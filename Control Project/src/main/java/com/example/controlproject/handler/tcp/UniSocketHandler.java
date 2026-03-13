package com.example.controlproject.handler.tcp;

import com.example.controlproject.support.BridgeSupport;
import com.example.controlproject.support.ConnectionManager;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;

/**
 * 单向 TCP 处理器（3002）。
 * 作用：接收设备推送数据并广播到 3004 WebSocket，
 * 在连接断开时向订阅端发送 404 关闭通知。
 */
public final class UniSocketHandler extends SimpleChannelInboundHandler<String> {
    private final ConnectionManager manager;

    public UniSocketHandler(ConnectionManager manager) {
        this.manager = manager;
    }

    // 记录单向推送 TCP 连接建立。
    @Override
    public void channelActive(ChannelHandlerContext ctx) {
        System.out.println("单向Socket连接: " + ctx.channel().remoteAddress());
    }

    // 转发推送消息给所有 3004 订阅端。
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, String msg) throws Exception {
        JsonNode json = BridgeSupport.MAPPER.readTree(msg);
        if (json.has("from")) {
            ctx.channel().attr(BridgeSupport.DEVICE_NAME_KEY).set(json.get("from").asText());
        }
        manager.broadcastToUniWebSocket(msg);
    }

    // 连接断开时广播 404 关闭通知。
    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        try {
            ObjectNode closed = BridgeSupport.MAPPER.createObjectNode();
            String deviceName = ctx.channel().attr(BridgeSupport.DEVICE_NAME_KEY).get();
            closed.put("from", deviceName == null ? "unknown" : deviceName);
            closed.put("addr", String.valueOf(ctx.channel().remoteAddress()));
            closed.put("content", 404);
            manager.broadcastToUniWebSocket(BridgeSupport.MAPPER.writeValueAsString(closed));
        } catch (Exception e) {
            System.out.println("发送断开消息失败: " + e.getMessage());
        }
        System.out.println("单向Socket断开: " + ctx.channel().remoteAddress());
    }

    // 异常时记录并关闭连接。
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        System.out.println("单向Socket异常: " + cause.getMessage());
        ctx.close();
    }
}
