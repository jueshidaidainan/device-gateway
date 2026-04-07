package com.example.controlproject.support;

import io.netty.channel.embedded.EmbeddedChannel;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ConnectionManagerTest {

    @Test
    void shouldExposeDeviceStatusAndRecentEvents() {
        ConnectionManager manager = new ConnectionManager();
        EmbeddedChannel biChannel = new EmbeddedChannel();
        EmbeddedChannel uniChannel = new EmbeddedChannel();

        manager.registerBiSocket("device-a", biChannel);
        manager.recordUniSocketMessage("device-a", uniChannel);

        ConnectionManager.DeviceStatus status = manager.getDeviceStatus("device-a");

        assertNotNull(status);
        assertTrue(status.biSocketOnline());
        assertEquals("uni_socket_message", status.lastEventType());
        assertNotNull(status.uniSocketLastSeenAt());
        assertFalse(manager.getRecentEvents(10).isEmpty());

        manager.removeBiSocket("device-a", biChannel);

        ConnectionManager.DeviceStatus offline = manager.getDeviceStatus("device-a");
        assertNotNull(offline);
        assertFalse(offline.biSocketOnline());
        assertEquals("bi_socket_disconnected", offline.lastEventType());
    }
}
