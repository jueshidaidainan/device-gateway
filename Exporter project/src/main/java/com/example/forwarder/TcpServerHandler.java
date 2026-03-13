package com.example.forwarder;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;

/**
 * Layer 2 handler:
 * 对应 Python make_handle_client(...) 里业务层 hasnext 分片拼接与 JSON 入队逻辑。
 * TCP 粘包/半包已由 LengthFieldBasedFrameDecoder 在前置 handler 中处理。
 * - 放入 data_queue
 */
public class TcpServerHandler extends SimpleChannelInboundHandler<ByteBuf> {
    private static final Logger log = LoggerFactory.getLogger(TcpServerHandler.class);
    // 固定头长度：uint32 + uint16 + uint8 + uint8 = 8 字节
    private static final int HEADER_SIZE = 8;

    private final BlockingQueue<JsonNode> dataQueue;
    private final ObjectMapper objectMapper;//java 里将序列化的 json 字符串反序列化为 json 结构（Tree 状的）
    private final List<byte[]> fragments = new ArrayList<>();

    public TcpServerHandler(BlockingQueue<JsonNode> dataQueue, ObjectMapper objectMapper) {
        this.dataQueue = dataQueue;
        this.objectMapper = objectMapper;
    }

    // Netty的框架中，下面这些带有 override 的方法都是回调函数，在特定的事件触发的时候会自动调用的。
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, ByteBuf frame) throws Exception {
        // 进入这里时，frame 已经是“完整一帧”(由 LengthFieldBasedFrameDecoder 保证)
        if (frame.readableBytes() < HEADER_SIZE) {
            log.warn("Invalid frame: less than header size, bytes={}", frame.readableBytes());
            return;
        }

        // 按小端读取协议头
        int cmdLen = (int) frame.readUnsignedIntLE();
        frame.skipBytes(2); // cmdtype
        frame.skipBytes(1); // cmd_field
        boolean hasNext = frame.readUnsignedByte() != 0;

        int remaining = frame.readableBytes();
        if (remaining < cmdLen) {
            log.warn("Invalid frame: payload length mismatch, expected={}, actual={}", cmdLen, remaining);
            return;
        }

        byte[] payload = new byte[cmdLen];
        frame.readBytes(payload);
        // 每帧都先暂存，直到遇到 hasNext = false 才认为业务消息完整
        fragments.add(payload);

        if (!hasNext) {
            byte[] fullPayload = joinFragments();
            fragments.clear();
            String json = new String(fullPayload, StandardCharsets.UTF_8);
            JsonNode node = objectMapper.readTree(json);
            dataQueue.put(node);
        }
    }

    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        if (!fragments.isEmpty()) {
            log.warn("Channel closed with unfinished business fragments, dropping {} fragments", fragments.size());
            fragments.clear();
        }
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        log.error("TCP connection error", cause);
        ctx.close();
    }

    private byte[] joinFragments() {
        // 业务层多段拼接：把多个 payload 片段按到达顺序拼成一个完整 JSON 文本。
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        for (byte[] fragment : fragments) {
            out.write(fragment, 0, fragment.length);
        }
        return out.toByteArray();
    }
}
