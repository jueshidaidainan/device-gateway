package com.example.controlproject.codec;

import com.example.controlproject.support.BridgeSupport;
import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.ByteToMessageDecoder;

import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * STX/ETX 分包解码器。
 * 作用：从 TCP 字节流中按协议提取完整 JSON 文本帧，
 * 处理半包/粘包并在超长缓冲时做保护。
 */
public final class StxEtxFrameDecoder extends ByteToMessageDecoder {
    private final int maxLength;

    public StxEtxFrameDecoder(int maxLength) {
        this.maxLength = maxLength;
    }

    // 从缓存字节流中切出完整消息帧，输出为 UTF-8 文本。
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) {
        // ctx 为 Netty 解码器固定签名参数；当前逻辑不依赖上下文对象本身。
        while (in.isReadable()) {
            int stxPos = in.indexOf(in.readerIndex(), in.writerIndex(), BridgeSupport.STX);
            if (stxPos < 0) {
                // 没有包头说明当前字节流无效，直接丢弃，避免无意义积压。
                in.skipBytes(in.readableBytes());
                return;
            }

            if (stxPos > in.readerIndex()) {
                in.skipBytes(stxPos - in.readerIndex());
            }

            int etxPos = in.indexOf(in.readerIndex() + 1, in.writerIndex(), BridgeSupport.ETX);
            if (etxPos < 0) {
                // 有包头但迟迟没有包尾：
                // 1) 未超长：保留当前半包，等待后续字节补齐。
                // 2) 已超长：丢弃当前这个可疑 STX，继续寻找下一个包头，避免卡死在坏包上。
                if (in.readableBytes() > maxLength) {
                    in.skipBytes(1);
                    continue;//继续在 while 循环里找下一个STX
                }
                return;// return 是退出 while 循环，等待下一个包的到来。
            }

            in.skipBytes(1);//此时刚好停在 stx 上，所以跳过他
            int len = etxPos - in.readerIndex();
            ByteBuf payload = in.readRetainedSlice(len);// Netty的内存是池化的，所以这里不会对 payload 进行复制，
            // 而是对这段区域加了个类似业务锁
            // 然后指针移动了。
            in.skipBytes(1);//跳过包尾

            out.add(payload.toString(StandardCharsets.UTF_8));//将这段 payload 转换为 string 
            payload.release();// 切记释放这个锁，将内存归还 Netty
        }
    }
}
