package com.example.controlproject.bootstrap;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Spring Boot 启动入口类。
 * 作用：启动 Spring 容器，并触发 NettyBridgeServer 的生命周期回调。
 */
@SpringBootApplication(scanBasePackages = "com.example.controlproject")
public class ControlProjectApplication {
    public static void main(String[] args) {
        // args 为 Java 程序标准入口参数；当前启动流程未使用命令行参数。
        SpringApplication.run(ControlProjectApplication.class, args);
    }
}
