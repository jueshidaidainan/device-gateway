package com.example.controlproject.handler.tcp;

import com.example.controlproject.support.BridgeSupport;
import com.example.controlproject.support.ConnectionManager;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.timeout.IdleState;
import io.netty.handler.timeout.IdleStateEvent;

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
            String deviceName = json.get("from").asText();
            ctx.channel().attr(BridgeSupport.DEVICE_NAME_KEY).set(deviceName);
            manager.recordUniSocketMessage(deviceName, ctx.channel());
        }
        manager.broadcastToUniWebSocket(msg);
    }

    // 2s 内无入站数据：关闭连接
    @Override
    public void userEventTriggered(ChannelHandlerContext ctx, Object evt) {
        if (evt instanceof IdleStateEvent) {
            IdleStateEvent e = (IdleStateEvent) evt;
            if (e.state() == IdleState.READER_IDLE) {
                System.out.println("单向Socket读超时(>2s), 关闭连接: " + ctx.channel().remoteAddress());
                ctx.close();
                return;
            }
        }
        ctx.fireUserEventTriggered(evt);
    }

    // 连接断开时广播 404 关闭通知。
    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        try {
            ObjectNode closed = BridgeSupport.MAPPER.createObjectNode();
            String deviceName = ctx.channel().attr(BridgeSupport.DEVICE_NAME_KEY).get();
            manager.recordUniSocketDisconnected(deviceName, ctx.channel());
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
