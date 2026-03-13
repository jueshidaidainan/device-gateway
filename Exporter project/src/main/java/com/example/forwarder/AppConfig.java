package com.example.forwarder;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

@Configuration //告诉 Spring 容器，这个类是一个配置类。
@EnableConfigurationProperties(AppProperties.class) //启用配置属性绑定功能，并指定要绑定的属性类是 AppProperties.class
public class AppConfig {
    @Bean //标记在一个方法上，表示该方法的返回值应该被实例化为一个 Spring Bean，并注册到容器中。
    public BlockingQueue<JsonNode> dataQueue() {
        return new LinkedBlockingQueue<>();//基于链表结构对 BlockingQueue的实现，主要用于多线程的生产者消费者模型，避免了手动写 wait 和 notify 的问题。
                                    //而且是线程安全的，不用自己加锁
    }
}

////------- 那 spring 连接项目的调用逻辑在哪里体现的呢？

// 在这几个地方体现：

// 启动入口
// TcpForwarderApplication.java
// SpringApplication.run(...) 启动 Spring 容器，开始扫描和装配。

// 扫描范围
// TcpForwarderApplication 在 com.example.forwarder 包下，Spring 默认扫描这个包及子包。
// 所以 @Component/@Service/@Configuration 都会被发现。

// Bean 定义与自动注入

// AppConfig.java：@Bean dataQueue() 定义 BlockingQueue Bean。
// 其他类构造函数里声明依赖，Spring 自动注入（构造器注入）。
// 生命周期回调（你关心的“谁调用”）

// @PostConstruct：Bean 创建后自动调用。
// TcpServerLifecycle.start() 启动 Netty
// ExporterWorker.start() 启动消费线程
// @PreDestroy：应用关闭前自动调用，做资源释放。
// 一句话：
// “连接项目调用逻辑”不在某个手写 main 里的调用链，而在“注解 + 容器启动 + 生命周期回调”这套机制里。


//------- 那 appconfig和 appproperties 是必须的吗？后者的作用是什么？我看不懂

// 不是“必须”，但在 Spring 里是推荐做法。

// AppConfig 不是必须
// 作用：声明 @Bean，比如共享的 BlockingQueue<JsonNode>。
// 不用它也行：你可以在某个类里 new LinkedBlockingQueue<>()，但会变成手工管理、耦合更高。
// AppProperties 也不是必须
// 作用：把 application.yml 里的配置映射成 Java 对象（类型安全）。
// 现在它承载的是：app.tcp.host、app.tcp.port、app.batch-size。
// 不用它也行：可以改成 @Value("${app.tcp.port}") 逐个注入，但字段多时会分散且难维护。
// 你可以把它理解为：

// application.yml = 配置文件
// AppProperties = 配置文件的 Java“结构体”
// 业务类只拿 properties.getTcp().getPort()，不直接写死字符串 key
// 所以：

// 不是强制
// 但能让配置集中、可读、可维护，尤其参数变多时差别很大。


