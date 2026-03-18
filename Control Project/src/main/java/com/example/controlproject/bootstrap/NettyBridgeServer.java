package com.example.controlproject.bootstrap;

import com.example.controlproject.codec.StxEtxFrameDecoder;
import com.example.controlproject.config.AppProperties;
import com.example.controlproject.handler.tcp.BiSocketHandler;
import com.example.controlproject.handler.tcp.UniSocketHandler;
import com.example.controlproject.handler.ws.BiWebSocketHandler;
import com.example.controlproject.handler.ws.UniWebSocketHandler;
import com.example.controlproject.support.ConnectionManager;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelPipeline;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.http.HttpObjectAggregator;
import io.netty.handler.codec.http.HttpServerCodec;
import io.netty.handler.codec.http.websocketx.WebSocketServerProtocolHandler;
import io.netty.handler.timeout.IdleStateHandler;
import org.springframework.context.SmartLifecycle;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * Netty 网桥服务生命周期类。
 * 作用：在应用启动时绑定 TCP/WebSocket 端口，
 * 并在应用关闭时统一释放 Netty 线程池与监听通道。
 * 因为 web 浏览器不能作为服务器来监听，所以这个网关服务器需要一边对接 Linux 的服务器，另一边对接 grafana 的 web 浏览器。也就是 TCP 和 WebSocket。
 * 又因为既有控制消息流又有推送的通知消息流，简单的做法是分别做两条连接来实现。所以，就有了两种协议各自的双向和单向连接。
 */
@Component
public class NettyBridgeServer implements SmartLifecycle {
    // SmartLifecycle 是 Spring 的生命周期接口。让 Netty 服务器跟随 SpringBoot 一起启动刚和关闭
    private final AppProperties properties;
    private final ConnectionManager manager;
    private final List<Channel> serverChannels = new ArrayList<>();

    private static final int UNI_TCP_READ_IDLE_SECONDS = 2;

    private volatile boolean running;
    private NioEventLoopGroup boss;
    private NioEventLoopGroup workers;

    public NettyBridgeServer(AppProperties properties, ConnectionManager manager) {
        this.properties = properties;
        this.manager = manager;
    }

    // 启动所有端口监听与 Netty 线程资源。
    @Override
    public synchronized void start() {
        if (running) {
            return;
        }
        boss = new NioEventLoopGroup(1);
        workers = new NioEventLoopGroup();

        try {
            serverChannels.add(startBiTcpServer(properties.getBiTcpPort()).channel());
            serverChannels.add(startUniTcpServer(properties.getUniTcpPort()).channel());
            serverChannels.add(startBiWebSocketServer(properties.getBiWebSocketPort()).channel());
            serverChannels.add(startUniWebSocketServer(properties.getUniWebSocketPort()).channel());
            running = true;

            System.out.println("服务器已启动：");
            System.out.println("- 双向通信：" + properties.getBiTcpPort() + "（Socket） ↔ "
                    + properties.getBiWebSocketPort() + "（WebSocket，每个devicename唯一）");
            System.out.println("- 单向广播：" + properties.getUniTcpPort() + "（Socket） → "
                    + properties.getUniWebSocketPort() + "（WebSocket）");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("启动 Netty 服务被中断", e);
        } catch (Exception e) {
            stop();
            throw new IllegalStateException("启动 Netty 服务失败", e);
        }
    }

    // 停止所有端口并释放 Netty 线程池。
    @Override
    public synchronized void stop() {
        for (Channel channel : serverChannels) {
            if (channel != null && channel.isOpen()) {
                channel.close().awaitUninterruptibly();//等待端口释放完毕，且无视中断异常。然后close
            }
        }
        serverChannels.clear();

        if (boss != null) {
            boss.shutdownGracefully().awaitUninterruptibly();
            boss = null;
        }
        if (workers != null) {
            workers.shutdownGracefully().awaitUninterruptibly();//shutdownGracefully 拒绝接受新任务，等现在手里的发完之后，优雅通知断开连接。
            workers = null;
        }
        running = false;
    }

    @Override
    public boolean isRunning() {
        return running;
    }

    @Override
    public int getPhase() {
        return Integer.MAX_VALUE;
    }

    @Override
    public boolean isAutoStartup() {
        return true;
    }

    // 初始化双向 TCP 服务端。
    private ChannelFuture startBiTcpServer(int port) throws InterruptedException {
        // ChannelFuture 是一个绑定端口的异步结果凭证
        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(boss, workers)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ChannelPipeline pipeline = ch.pipeline();
                        pipeline.addLast(new StxEtxFrameDecoder(properties.getMaxFrameLength()));
                        pipeline.addLast(new BiSocketHandler(manager));
                    }
                });
        return bootstrap.bind(port).sync();//sync 代表等到OS 告诉端口绑定成功后才返回
    }

    // 初始化单向 TCP 服务端。
    private ChannelFuture startUniTcpServer(int port) throws InterruptedException {
        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(boss, workers)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ChannelPipeline pipeline = ch.pipeline();
                        // 2s 无入站数据触发 idle 事件（用于单向推送通道超时关闭）
                        pipeline.addLast(new IdleStateHandler(UNI_TCP_READ_IDLE_SECONDS, 0, 0));
                        pipeline.addLast(new StxEtxFrameDecoder(properties.getMaxFrameLength()));
                        pipeline.addLast(new UniSocketHandler(manager));
                    }
                });
        return bootstrap.bind(port).sync();
    }

    // 初始化双向 WebSocket 服务端。
    private ChannelFuture startBiWebSocketServer(int port) throws InterruptedException {
        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(boss, workers)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ChannelPipeline pipeline = ch.pipeline();
                        pipeline.addLast(new HttpServerCodec());
                        pipeline.addLast(new HttpObjectAggregator(65536));
                        pipeline.addLast(new WebSocketServerProtocolHandler(properties.getWebSocketPath()));
                        pipeline.addLast(new BiWebSocketHandler(manager));
                    }
                });
        return bootstrap.bind(port).sync();
    }

    // 初始化单向 WebSocket 服务端。
    private ChannelFuture startUniWebSocketServer(int port) throws InterruptedException {
        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(boss, workers)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ChannelPipeline pipeline = ch.pipeline();
                        pipeline.addLast(new HttpServerCodec());//把字节流编解码成 HTTP 请求/响应对象。
                        pipeline.addLast(new HttpObjectAggregator(65536));//把分片 HTTP 消息聚合成完整消息（例如完整握手请求）。
                        //多的这两个是因为，ws 是基于 http upgrade的
                        pipeline.addLast(new WebSocketServerProtocolHandler(properties.getWebSocketPath()));
                        pipeline.addLast(new UniWebSocketHandler(manager));
                    }
                });
        return bootstrap.bind(port).sync();
    }
}
