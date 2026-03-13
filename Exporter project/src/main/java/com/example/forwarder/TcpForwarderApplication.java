package com.example.forwarder;


import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;


@SpringBootApplication
// @SpringBootApplication：三合一全能插件
// 这个注解是 Spring Boot 的核心，它实际上是三个注解的集合体（复合注解）。当你把它贴在类上时，相当于同时开启了三个功能：

// @SpringBootConfiguration：
// 标识这是一个配置类。它告诉 Spring，这个类里可能会有你定义的 @Bean（就像你在 AppConfig.java 里定义 dataQueue 那样）。
// @EnableAutoConfiguration：
// 这是 Spring Boot 最“魔法”的地方。 它会根据你项目里引用的依赖（比如 Netty、Jackson、Prometheus 等），自动帮你把默认的配置配好。它发现你有 Netty，就会准备好相关的底层环境。
// @ComponentScan：
// 自动寻人启事。 它会从当前包（com.example.forwarder）开始，递归扫描所有子包，寻找带有 @Component、@Service（比如你的 MetricsService）等注解的类，并把它们实例化成对象放入容器。
public class TcpForwarderApplication {
    public static void main(String[] args) {
        SpringApplication.run(TcpForwarderApplication.class, args);//启动 spring
        // 传入 .class 的目的是给 Spring 提供一个起点坐标和图纸。
    }
    //虽然使用spring boot 进行依赖注入和控制反转，但是JVM 只认 psvm 这个函数标签，所以还得要这个打火机（很贴切）。
}
