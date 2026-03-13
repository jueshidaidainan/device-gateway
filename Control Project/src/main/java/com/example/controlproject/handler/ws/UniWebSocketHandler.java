package com.example.controlproject.handler.ws;

import com.example.controlproject.support.ConnectionManager;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;

/**
 * 单向 WebSocket 处理器（3004）。
 * 作用：维护推送订阅端连接集合，本身不处理业务消息，
 * 仅负责连接加入/移除与异常关闭。
 */
public final class UniWebSocketHandler extends ChannelInboundHandlerAdapter {
    private final ConnectionManager manager;

    public UniWebSocketHandler(ConnectionManager manager) {
        this.manager = manager;
    }

    // 新订阅端连接时加入单向 WebSocket 集合。
    @Override
    public void handlerAdded(ChannelHandlerContext ctx) {
        manager.registerUniWebSocket(ctx.channel());
    }

    // 订阅端断开时从集合移除。
    @Override
    public void handlerRemoved(ChannelHandlerContext ctx) {
        manager.removeUniWebSocket(ctx.channel());
    }

    // 异常时关闭连接，避免悬挂会话。
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        System.out.println("单向通信异常: " + cause.getMessage());
        ctx.close();
    }
}
