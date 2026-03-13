package com.example.controlproject.support;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.util.AttributeKey;

/**
 * 网桥公共支持类。
 * 作用：集中定义协议常量、公共 ObjectMapper，
 * 以及将 JSON 数据封装为 STX/ETX 帧的工具方法。
 */
public final class BridgeSupport {
    public static final byte STX = 0x02;
    public static final byte ETX = 0x03;

    public static final ObjectMapper MAPPER = new ObjectMapper();//Jackson 库里的东西，专门负责数据格式转换。将 Java 对象转成 JSON，或把 JSON 转回 Java 对象。
    public static final AttributeKey<String> DEVICE_NAME_KEY = AttributeKey.valueOf("device_name");
    //专门负责记录连接状态。相当于 Web 开发里的 Session，用于给当前的网络连接（Channel）临时绑定一些自定义数据。

    private BridgeSupport() {
    }

    // 将 JSON 对象封装为 STX/ETX 协议帧后发送。
    public static ByteBuf frameJson(JsonNode data) {
        try {
            byte[] payload = MAPPER.writeValueAsBytes(data);
            ByteBuf framed = Unpooled.buffer(payload.length + 2);
            framed.writeByte(STX);
            framed.writeBytes(payload);
            framed.writeByte(ETX);
            return framed;
        } catch (Exception e) {
            throw new RuntimeException("序列化发送数据失败", e);
        }
    }
}
