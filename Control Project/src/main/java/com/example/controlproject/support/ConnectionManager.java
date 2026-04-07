package com.example.controlproject.support;

import com.fasterxml.jackson.databind.JsonNode;
import io.netty.channel.Channel;
import io.netty.handler.codec.http.websocketx.TextWebSocketFrame;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * Maintains live connection routing and exposes a lightweight ops view for the
 * diagnostic agent service.
 */
public final class ConnectionManager {
    private static final int MAX_EVENTS = 200;

    private final Map<String, Channel> biSocketMap = new ConcurrentHashMap<>();
    private final Map<String, DeviceRuntime> deviceStates = new ConcurrentHashMap<>();
    private final Deque<GatewayEvent> recentEvents = new ConcurrentLinkedDeque<>();
    private final CopyOnWriteArraySet<Channel> biWebSockets = new CopyOnWriteArraySet<>();
    private final CopyOnWriteArraySet<Channel> uniWebSockets = new CopyOnWriteArraySet<>();

    public void registerBiWebSocket(Channel ch) {
        biWebSockets.add(ch);
    }

    public void removeBiWebSocket(Channel ch) {
        biWebSockets.remove(ch);
    }

    public void registerUniWebSocket(Channel ch) {
        uniWebSockets.add(ch);
    }

    public void removeUniWebSocket(Channel ch) {
        uniWebSockets.remove(ch);
    }

    public int biWebSocketCount() {
        return biWebSockets.size();
    }

    public int uniWebSocketCount() {
        return uniWebSockets.size();
    }

    public String biWebSocketSnapshot() {
        return biWebSockets.toString();
    }

    public void broadcastToBiWebSocket(String data) {
        for (Channel ws : biWebSockets) {
            if (ws.isActive()) {
                ws.writeAndFlush(new TextWebSocketFrame(data));
            }
        }
    }

    public void broadcastToUniWebSocket(String data) {
        for (Channel ws : uniWebSockets) {
            if (ws.isActive()) {
                ws.writeAndFlush(new TextWebSocketFrame(data));
            }
        }
    }

    public void sendToBiSocket(String deviceName, JsonNode data) {
        Channel ch = biSocketMap.get(deviceName);
        if (ch == null || !ch.isActive()) {
            throw new IllegalStateException("Device " + deviceName + " socket is unavailable");
        }
        ch.writeAndFlush(BridgeSupport.frameJson(data));
    }

    public void registerBiSocket(String deviceName, Channel ch) {
        Channel old = biSocketMap.put(deviceName, ch);
        Instant now = Instant.now();
        DeviceRuntime runtime = deviceStates.computeIfAbsent(deviceName, DeviceRuntime::new);
        runtime.markBiSocketConnected(String.valueOf(ch.remoteAddress()), now);
        appendEvent(new GatewayEvent(
                now,
                "bi_socket_connected",
                deviceName,
                "bi_socket",
                String.valueOf(ch.remoteAddress()),
                "Control channel connected"
        ));
        if (old != null && old != ch) {
            old.close();
        }
    }

    public void removeBiSocket(String deviceName, Channel ch) {
        if (deviceName == null) {
            return;
        }
        boolean removed = biSocketMap.remove(deviceName, ch);
        if (removed) {
            Instant now = Instant.now();
            DeviceRuntime runtime = deviceStates.computeIfAbsent(deviceName, DeviceRuntime::new);
            runtime.markBiSocketDisconnected(now);
            appendEvent(new GatewayEvent(
                    now,
                    "bi_socket_disconnected",
                    deviceName,
                    "bi_socket",
                    String.valueOf(ch.remoteAddress()),
                    "Control channel disconnected"
            ));
        }
    }

    public void recordUniSocketMessage(String deviceName, Channel ch) {
        if (deviceName == null || deviceName.isBlank()) {
            return;
        }
        Instant now = Instant.now();
        DeviceRuntime runtime = deviceStates.computeIfAbsent(deviceName, DeviceRuntime::new);
        runtime.markUniSocketSeen(String.valueOf(ch.remoteAddress()), now);
        appendEvent(new GatewayEvent(
                now,
                "uni_socket_message",
                deviceName,
                "uni_socket",
                String.valueOf(ch.remoteAddress()),
                "Push channel payload received"
        ));
    }

    public void recordUniSocketDisconnected(String deviceName, Channel ch) {
        if (deviceName == null || deviceName.isBlank()) {
            return;
        }
        Instant now = Instant.now();
        DeviceRuntime runtime = deviceStates.computeIfAbsent(deviceName, DeviceRuntime::new);
        runtime.markUniSocketDisconnected(now);
        appendEvent(new GatewayEvent(
                now,
                "uni_socket_disconnected",
                deviceName,
                "uni_socket",
                String.valueOf(ch.remoteAddress()),
                "Push channel disconnected"
        ));
    }

    public OpsOverview getOverview() {
        return new OpsOverview(
                biSocketMap.size(),
                biWebSocketCount(),
                uniWebSocketCount(),
                deviceStates.size(),
                recentEvents.size()
        );
    }

    public List<DeviceStatus> getDeviceStatuses() {
        return deviceStates.values().stream()
                .map(DeviceRuntime::snapshot)
                .sorted(Comparator.comparing(DeviceStatus::deviceName))
                .toList();
    }

    public DeviceStatus getDeviceStatus(String deviceName) {
        DeviceRuntime runtime = deviceStates.get(deviceName);
        return runtime == null ? null : runtime.snapshot();
    }

    public List<GatewayEvent> getRecentEvents(int limit) {
        int cappedLimit = Math.max(1, Math.min(limit, MAX_EVENTS));
        List<GatewayEvent> snapshot = new ArrayList<>(cappedLimit);
        for (GatewayEvent event : recentEvents) {
            snapshot.add(event);
            if (snapshot.size() >= cappedLimit) {
                break;
            }
        }
        return snapshot;
    }

    private void appendEvent(GatewayEvent event) {
        recentEvents.addFirst(event);
        while (recentEvents.size() > MAX_EVENTS) {
            recentEvents.removeLast();
        }
    }

    public record OpsOverview(
            int biSocketConnections,
            int biWebSocketConnections,
            int uniWebSocketConnections,
            int observedDevices,
            int recentEventCount
    ) {
    }

    public record DeviceStatus(
            String deviceName,
            boolean biSocketOnline,
            String biSocketAddress,
            Instant biSocketConnectedAt,
            Instant biSocketLastDisconnectedAt,
            String uniSocketAddress,
            Instant uniSocketLastSeenAt,
            Instant uniSocketLastDisconnectedAt,
            String lastEventType,
            Instant lastUpdatedAt
    ) {
    }

    public record GatewayEvent(
            Instant timestamp,
            String eventType,
            String deviceName,
            String channelType,
            String remoteAddress,
            String message
    ) {
    }

    private static final class DeviceRuntime {
        private final String deviceName;
        private volatile boolean biSocketOnline;
        private volatile String biSocketAddress;
        private volatile Instant biSocketConnectedAt;
        private volatile Instant biSocketLastDisconnectedAt;
        private volatile String uniSocketAddress;
        private volatile Instant uniSocketLastSeenAt;
        private volatile Instant uniSocketLastDisconnectedAt;
        private volatile String lastEventType;
        private volatile Instant lastUpdatedAt;

        private DeviceRuntime(String deviceName) {
            this.deviceName = deviceName;
        }

        private void markBiSocketConnected(String remoteAddress, Instant now) {
            biSocketOnline = true;
            biSocketAddress = remoteAddress;
            biSocketConnectedAt = now;
            lastEventType = "bi_socket_connected";
            lastUpdatedAt = now;
        }

        private void markBiSocketDisconnected(Instant now) {
            biSocketOnline = false;
            biSocketLastDisconnectedAt = now;
            lastEventType = "bi_socket_disconnected";
            lastUpdatedAt = now;
        }

        private void markUniSocketSeen(String remoteAddress, Instant now) {
            uniSocketAddress = remoteAddress;
            uniSocketLastSeenAt = now;
            lastEventType = "uni_socket_message";
            lastUpdatedAt = now;
        }

        private void markUniSocketDisconnected(Instant now) {
            uniSocketLastDisconnectedAt = now;
            lastEventType = "uni_socket_disconnected";
            lastUpdatedAt = now;
        }

        private DeviceStatus snapshot() {
            return new DeviceStatus(
                    deviceName,
                    biSocketOnline,
                    biSocketAddress,
                    biSocketConnectedAt,
                    biSocketLastDisconnectedAt,
                    uniSocketAddress,
                    uniSocketLastSeenAt,
                    uniSocketLastDisconnectedAt,
                    lastEventType,
                    lastUpdatedAt
            );
        }
    }
}
