package com.example.controlproject.handler.ws;

import com.example.controlproject.support.BridgeSupport;
import com.example.controlproject.support.ConnectionManager;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.http.websocketx.TextWebSocketFrame;

/**
 * 双向 WebSocket 处理器（3003）。
 * 作用：接收前端控制指令，按 device_name 找到对应 TCP 设备并下发；
 * 同时维护双向 WebSocket 客户端集合。
 */
public final class BiWebSocketHandler extends SimpleChannelInboundHandler<TextWebSocketFrame> {
    private final ConnectionManager manager;

    public BiWebSocketHandler(ConnectionManager manager) {
        this.manager = manager;
    }

    // 新客户端加入双向 WebSocket 集合。
    @Override
    public void handlerAdded(ChannelHandlerContext ctx) {
        manager.registerBiWebSocket(ctx.channel());
        System.out.println("双向客户端ws set：" + manager.biWebSocketSnapshot());
    }

    // 解析控制指令并转发到对应设备 TCP 连接。
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, TextWebSocketFrame frame) {
        String text = frame.text();
        try {
            JsonNode data = BridgeSupport.MAPPER.readTree(text);
            JsonNode device = data.get("device_name");
            if (device == null) {
                ctx.channel().writeAndFlush(new TextWebSocketFrame("{\"error\":\"Missing device_name\"}"));
                return;
            }

            ObjectNode copy = ((ObjectNode) data).deepCopy();
            copy.remove("device_name");
            manager.sendToBiSocket(device.asText(), copy);
        } catch (Exception e) {
            String err = "{\"error\":\"内部错误: " + e.getMessage().replace("\"", "\\\"") + "\"}";
            ctx.channel().writeAndFlush(new TextWebSocketFrame(err));
        }
    }

    // 客户端离开时移除集合并输出连接数。
    @Override
    public void handlerRemoved(ChannelHandlerContext ctx) {
        manager.removeBiWebSocket(ctx.channel());
        System.out.println("连接关闭，当前连接数：" + manager.biWebSocketCount());
    }

    // WebSocket 异常统一关闭连接。
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        System.out.println("WebSocket error " + cause.getMessage());
        ctx.close();
    }
}
