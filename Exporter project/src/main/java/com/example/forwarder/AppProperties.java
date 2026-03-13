package com.example.forwarder;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app")
// 告诉 Spring，去配置文件里找所有以 app. 开头的属性。
// 依赖 Setter 方法：Spring 框架在启动时，会通过反射调用你写的 setBatchSize、setHost 等方法，把配置文件里的值“塞”进这个类里。
// 自带默认值：如果配置文件里没写，它就会使用代码里初始化的默认值（例如 batchSize = 100，端口 12345）。
public class AppProperties {
    private Tcp tcp = new Tcp();
    private int batchSize = 100;

    public Tcp getTcp() {
        return tcp;
    }

    public void setTcp(Tcp tcp) {
        this.tcp = tcp;
    }

    public int getBatchSize() {
        return batchSize;
    }

    public void setBatchSize(int batchSize) {
        this.batchSize = batchSize;
    }

    public static class Tcp {
        private String host = "0.0.0.0";
        private int port = 12345;

        public String getHost() {
            return host;
        }

        public void setHost(String host) {
            this.host = host;
        }

        public int getPort() {
            return port;
        }

        public void setPort(int port) {
            this.port = port;
        }
    }
}
