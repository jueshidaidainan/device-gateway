package com.example.forwarder;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.LengthFieldBasedFrameDecoder;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.nio.ByteOrder;
import java.util.concurrent.BlockingQueue;

/**
 * 对应 Python 的 main(...) 生命周期管理：
 * - 启动 TCP server
 * - 进程退出时释放资源
 */
@Component
public class TcpServerLifecycle {
    private static final Logger log = LoggerFactory.getLogger(TcpServerLifecycle.class);
    // 安全上限：单帧最大 16MB，防止异常长度导致内存风险。
    private static final int MAX_FRAME_LENGTH = 16 * 1024 * 1024;

    private final AppProperties properties;
    private final BlockingQueue<JsonNode> dataQueue;
    private final ObjectMapper objectMapper;

    private EventLoopGroup bossGroup;
    private EventLoopGroup workerGroup;
    private Channel serverChannel;

    public TcpServerLifecycle(AppProperties properties,
                              BlockingQueue<JsonNode> dataQueue,
                              ObjectMapper objectMapper) {
        this.properties = properties;
        this.dataQueue = dataQueue;
        this.objectMapper = objectMapper;
    }

    @PostConstruct
    // 等 Spring 把这个对象创建好，并且把需要的参数（依赖）都塞进去之后，立刻执行这个方法。
    public void start() throws InterruptedException {
        // boss 负责接收连接；worker 负责读写与业务 handler 回调。
        bossGroup = new NioEventLoopGroup(1);
        workerGroup = new NioEventLoopGroup();

        ServerBootstrap bootstrap = new ServerBootstrap()
                .group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ch.pipeline()//pipeline 来管理两个负责处理的 handler
                                // Layer 1（传输层）：
                                // 用长度字段切帧，解决 TCP 粘包/半包。
                                // 协议头: <IHBB 小端序，前 4 字节 cmdlen(LE) 表示 payload 长度。
                                .addLast(new LengthFieldBasedFrameDecoder(
                                        ByteOrder.LITTLE_ENDIAN,
                                        MAX_FRAME_LENGTH,
                                        0, //长度字段从帧的第几个字节开始。    你的 cmdlen 在最开头，所以是 0
                                        4, // lengthFieldLength: cmdlen 占 4 字节。   长度字段占几个字节。cmdlen 是 uint32，所以是 4。
                                        4, // lengthAdjustment: 整帧长度 = 4(cmdlen字段) + 2 + 1 + 1 + payload。 对“长度字段值”做补偿。你的 cmdlen 只表示 payload 长度，不含头。Netty 的公式里已经算进了前 4 字节（length 字段本身），还差后面 2+1+1=4 字节头，所以这里填 4。
                                        0, // 不剥离头部，后续 handler 还要读取 hasnext
                                        true
                                ))
                                // Layer 2（业务层）：
                                // 只关心 hasnext 分片拼接和 JSON 入队，不再关心 TCP 字节流细节。
                                .addLast(new TcpServerHandler(dataQueue, objectMapper));
                    }
                });

        String host = properties.getTcp().getHost();
        int port = properties.getTcp().getPort();
        serverChannel = bootstrap.bind(host, port).sync().channel();
        log.info("TCP server listening on {}:{}", host, port);
    }

    @PreDestroy
    //@PreDestroy 正好是 @PostConstruct 的反面：当 Spring 准备销毁这个对象（通常是程序被终止、服务停机时），它会立刻被执行。
    //释放创建的资源
    public void stop() {
        if (serverChannel != null) {
            serverChannel.close();
        }
        if (bossGroup != null) {
            bossGroup.shutdownGracefully();
        }
        if (workerGroup != null) {
            workerGroup.shutdownGracefully();
        }
        log.info("TCP server stopped");
    }
}
