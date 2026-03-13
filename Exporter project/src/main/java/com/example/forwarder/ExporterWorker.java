package com.example.forwarder;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;

/**
 * 对应 Python 的 exporter_loop(data_queue, batch_size)：
 * - 先阻塞获取一条
 * - 再批量 drain 现有队列
 * - 按 device/topics/flow 更新指标
 */
@Component
public class ExporterWorker {
    private static final Logger log = LoggerFactory.getLogger(ExporterWorker.class);

    private final BlockingQueue<JsonNode> dataQueue;
    private final MetricsService metricsService;
    private final AppProperties properties;
    private Thread workerThread;

    public ExporterWorker(BlockingQueue<JsonNode> dataQueue, MetricsService metricsService, AppProperties properties) {
        this.dataQueue = dataQueue;
        this.metricsService = metricsService;
        this.properties = properties;
    }

    @PostConstruct
    //Bean初始化之后自动调用
    public void start() {
        // 启动一个后台线程持续消费 dataQueue（对应 Python 的 exporter_loop 协程）
        workerThread = new Thread(this::runLoop, "exporter-worker");
        workerThread.setDaemon(true);
        workerThread.start();
    }

    private void runLoop() {
        int batchSize = Math.max(1, properties.getBatchSize());
        List<JsonNode> batch = new ArrayList<>(batchSize);

        while (!Thread.currentThread().isInterrupted()) {
            try {
                // 至少阻塞拿到 1 条，避免空转。队列为空的时候挂起，避免消耗 CPU 资源。
                // 这里充当哨兵，下面的 drainTo 负责搬。分工明确
                JsonNode first = dataQueue.take();
                batch.clear();
                batch.add(first);
                // 非阻塞地批量带走当前队列里的其余数据，提升吞吐
                dataQueue.drainTo(batch, batchSize - 1);

                for (JsonNode item : batch) {
                    String deviceId = item.path("device").asText("");
                    JsonNode topics = item.path("topics");
                    //防御性编程，真牛逼啊
                    //如果提取出来的 topics 字段不是一个 JSON 数组（Array），就直接跳过当前这条数据，继续处理 batch 里的下一条。
                    if (!topics.isArray()) {
                        continue;
                    }
                    for (JsonNode topic : topics) {
                        String topicId = topic.path("ipadd").asText("");
                        long sentCount = topic.path("flow").path("count").asLong(0);
                        double sentFlow = topic.path("flow").path("value").asDouble(0.0);
                        metricsService.update(topicId, deviceId, sentCount, sentFlow);
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (Exception e) {
                log.error("Exporter batch processing failed", e);
            }
        }
    }

    @PreDestroy
    public void stop() throws InterruptedException {
        // 应用关闭时优雅停止后台线程
        if (workerThread != null) {
            workerThread.interrupt();
            workerThread.join(2000);
        }
    }
}
