from app.models.domain import GatewayOpsEvidence, LogsEvidence, MetricPoint, MetricSeries, MetricsEvidence
from app.services.anomaly import evaluate_anomaly


def test_evaluate_anomaly_flags_large_drop_with_gateway_signal():
    metrics = MetricsEvidence(
        query='topic_packets_sent_flow{device_id="device-001"}',
        baseline_query='topic_packets_sent_flow{device_id="device-001"} offset 1d',
        series=[
            MetricSeries(
                label="device_id=device-001",
                metric={"device_id": "device-001"},
                points=[MetricPoint(timestamp="2026-04-07T00:00:00Z", value=10.0)],
                sample_count=1,
                average=10.0,
                latest=0.0,
            )
        ],
        baseline_series=[
            MetricSeries(
                label="device_id=device-001",
                metric={"device_id": "device-001"},
                points=[MetricPoint(timestamp="2026-04-06T00:00:00Z", value=100.0)],
                sample_count=1,
                average=100.0,
                latest=100.0,
            )
        ],
    )
    logs = LogsEvidence(query='{job="gateway"}', records=[], matched_keywords=[])
    gateway = GatewayOpsEvidence(device={"biSocketOnline": False}, events=[])

    assessment = evaluate_anomaly(metrics, logs, gateway)

    assert assessment.is_anomalous is True
    assert assessment.confidence >= 0.5
    assert any("offline" in reason for reason in assessment.reasons)
