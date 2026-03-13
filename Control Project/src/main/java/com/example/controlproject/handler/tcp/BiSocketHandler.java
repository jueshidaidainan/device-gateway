package com.example.controlproject.handler.tcp;

import com.example.controlproject.support.BridgeSupport;
import com.example.controlproject.support.ConnectionManager;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;

import java.net.InetSocketAddress;
import java.time.Instant;

/**
 * 双向 TCP 处理器（3001）。
 * 作用：处理设备侧控制连接，完成首次设备绑定，
 * 并把后续设备上行消息广播到 3003 WebSocket 客户端。
 */
public final class BiSocketHandler extends SimpleChannelInboundHandler<String> {
    private final ConnectionManager manager;
    private boolean deviceBound;

    public BiSocketHandler(ConnectionManager manager) {
        this.manager = manager;
    }

    // 新连接建立后先发送欢迎包，随后等待设备回报身份。
    @Override
    public void channelActive(ChannelHandlerContext ctx) throws Exception {
        InetSocketAddress addr = (InetSocketAddress) ctx.channel().remoteAddress();
        System.out.println("双向Socket连接: " + addr);

        ObjectNode welcome = BridgeSupport.MAPPER.createObjectNode();
        welcome.put("cmd", 101);
        welcome.put("from", 10000);
        welcome.put("stamp", Instant.now().getEpochSecond());

        ctx.writeAndFlush(BridgeSupport.frameJson(welcome));
        super.channelActive(ctx);
    }

    // 首帧用于绑定设备名，后续帧转发给双向 WebSocket。
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, String msg) throws Exception {
        if (!deviceBound) {
            JsonNode json = BridgeSupport.MAPPER.readTree(msg);
            JsonNode from = json.get("from");
            if (from != null) {
                String deviceName = from.asText();
                ctx.channel().attr(BridgeSupport.DEVICE_NAME_KEY).set(deviceName);
                manager.registerBiSocket(deviceName, ctx.channel());
                deviceBound = true;
                System.out.println("设备绑定: " + deviceName + " + " + ctx.channel().remoteAddress());
            }
            return;
        }

        manager.broadcastToBiWebSocket(msg);
    }

    // 设备断开时移除映射，避免脏连接。
    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        String deviceName = ctx.channel().attr(BridgeSupport.DEVICE_NAME_KEY).get();
        manager.removeBiSocket(deviceName, ctx.channel());
        System.out.println("双向Socket断开:" + deviceName + " : " + ctx.channel().remoteAddress() + " + 且已移除对应socket_map");
    }

    // 异常时打印日志并关闭当前连接。
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        System.out.println("双向Socket异常: " + cause.getMessage());
        ctx.close();
    }
}
