package com.example.controlproject.ops;

import com.example.controlproject.support.ConnectionManager;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping("/ops")
public class OpsController {
    private final ConnectionManager connectionManager;

    public OpsController(ConnectionManager connectionManager) {
        this.connectionManager = connectionManager;
    }

    @GetMapping("/devices")
    public DeviceListResponse listDevices() {
        return new DeviceListResponse(connectionManager.getOverview(), connectionManager.getDeviceStatuses());
    }

    @GetMapping("/devices/{deviceName}/status")
    public DeviceStatusResponse getDeviceStatus(@PathVariable String deviceName) {
        ConnectionManager.DeviceStatus status = connectionManager.getDeviceStatus(deviceName);
        if (status == null) {
            throw new ResponseStatusException(NOT_FOUND, "Unknown device: " + deviceName);
        }
        return new DeviceStatusResponse(connectionManager.getOverview(), status);
    }

    @GetMapping("/events")
    public EventListResponse getEvents(@RequestParam(defaultValue = "50") int limit) {
        return new EventListResponse(connectionManager.getOverview(), connectionManager.getRecentEvents(limit));
    }

    public record DeviceListResponse(
            ConnectionManager.OpsOverview overview,
            List<ConnectionManager.DeviceStatus> devices
    ) {
    }

    public record DeviceStatusResponse(
            ConnectionManager.OpsOverview overview,
            ConnectionManager.DeviceStatus device
    ) {
    }

    public record EventListResponse(
            ConnectionManager.OpsOverview overview,
            List<ConnectionManager.GatewayEvent> events
    ) {
    }
}
