package com.example.controlproject.config;

import com.example.controlproject.support.ConnectionManager;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 应用配置类。
 * 作用：注册配置属性与核心业务 Bean，集中管理对象装配。
 */
@Configuration
@EnableConfigurationProperties(AppProperties.class)
public class AppConfig {

    @Bean
    public ConnectionManager connectionManager() {
        return new ConnectionManager();
    }
}
//----- 你观察得很准确，当前实现就是这个模式：

// 3003 WS -> 3001 TCP 是定向单发
// 按 device_name 从 biSocketMap 找到具体设备连接再发送。
// 代码在 [ConnectionManager.java](/Users/eason_liu/Documents/Control Project/src/main/java/com/example/controlproject/support/ConnectionManager.java) 的 sendToBiSocket(...)。
// 3001 TCP -> 3003 WS 是广播
// 设备上行消息会发给所有 3003 的 WS 客户端。
// 代码是 broadcastToBiWebSocket(...)。
// 3002 TCP -> 3004 WS 也是广播
// 推送消息和断开通知都广播给所有 3004 订阅端。
// 代码是 broadcastToUniWebSocket(...)。
// 所以现在确实是“一个方向定向，其余是广播”。

//---- 没大量用注解的原因是：核心通信逻辑是 Netty pipeline，不是 Spring MVC/WebFlux controller 风格。

// manager 和 bootstrap 分离，从设计角度是合理的，而且是好事：
// NettyBridgeServer（bootstrap）负责“生命周期和端口启动/关闭”
// ConnectionManager 负责“连接状态与转发策略”
// 这是典型的“启动编排”和“业务状态”解耦，便于测试和维护。