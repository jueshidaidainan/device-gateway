package com.example.controlproject.handler.ws;

import com.example.controlproject.support.ConnectionManager;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.handler.timeout.IdleState;
import io.netty.handler.timeout.IdleStateEvent;

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

    // 2s 内无入站数据：关闭连接
    @Override
    public void userEventTriggered(ChannelHandlerContext ctx, Object evt) {
        if (evt instanceof IdleStateEvent) {
            IdleStateEvent e = (IdleStateEvent) evt;
            if (e.state() == IdleState.READER_IDLE) {
                System.out.println("单向WebSocket读超时(>2s), 关闭连接: " + ctx.channel().remoteAddress());
                ctx.close();
                return;
            }
        }
        ctx.fireUserEventTriggered(evt);
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
