package com.example.forwarder;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/**
 * 对应 Python 的 Prometheus 指标定义与更新：
 * - sent_gauge.labels(...).set(...)
 * - sent_flow_gauge.labels(...).set(...)
 */
@Service
public class MetricsService {
    private final MeterRegistry meterRegistry;
    // 每个 (topic_id, device_id) 一组 Gauge，持有当前最新值。
    private final ConcurrentMap<MetricKey, AtomicLong> totalMap = new ConcurrentHashMap<>();
    private final ConcurrentMap<MetricKey, AtomicReference<Double>> flowMap = new ConcurrentHashMap<>();

    public MetricsService(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    public void update(String topicId, String deviceId, long sentCount, double sentFlow) {
        MetricKey key = new MetricKey(topicId, deviceId);

        // 第一次出现该标签组合时注册 Gauge，之后只更新值。
        AtomicLong total = totalMap.computeIfAbsent(key, k -> {
            // --- 只有当 key 不存在时，才会执行这个大括号里的代码 ---
            
            // 1. 创建一个原子长整型容器，初始值为 0。 这个容器可以保证 Micrometer 拿到的指标是实时更新且线程安全的
            AtomicLong holder = new AtomicLong(0); 
            
            // 2. 构建并注册一个 Gauge 指标到监控中心 (meterRegistry)
            Gauge.builder("topic_packets_sent_total", holder, AtomicLong::get)
                    .tag("topic_id", k.topicId)   // 添加标签：主题ID
                    .tag("device_id", k.deviceId) // 添加标签：设备ID
                    .register(meterRegistry);     // 真正注册到 Prometheus/Grafana 等系统中
                    
            // 3. 返回这个容器，它会被放入 totalMap 中，key 就是当前的 k
            return holder;
        });

        // 4. 无论是否刚创建，都拿到这个 holder，然后更新最新的发送数量
        total.set(sentCount);

        AtomicReference<Double> flow = flowMap.computeIfAbsent(key, k -> {
            AtomicReference<Double> holder = new AtomicReference<>(0.0);
            Gauge.builder("topic_packets_sent_flow", holder, AtomicReference::get)
                    .tag("topic_id", k.topicId)
                    .tag("device_id", k.deviceId)
                    .register(meterRegistry);
            return holder;
        });
        flow.set(sentFlow);
    }

    private record MetricKey(String topicId, String deviceId) {
        //record 是 Java 的轻量数据类语法，会自动生成构造器、equals/hashCode/toString。
        // 所以它可以直接当 Map 的 key 用。
        private MetricKey {
            topicId = Objects.requireNonNullElse(topicId, "");
            deviceId = Objects.requireNonNullElse(deviceId, "");
        }
    }
}
