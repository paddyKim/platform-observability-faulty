# Platform Observability Faulty

런타임 장애 탐지와 LLM 근거 기반 분석을 검증하는 FastAPI workload다. Pod readiness와 `/metrics`는 정상 상태를 유지하지만 주문 API는 downstream timeout을 모사해 지연 후 HTTP 500을 반환한다.

## Local verification

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/uvicorn faulty_service.main:app --port 8102
```

다른 terminal에서 장애 traffic을 생성한다.

```bash
REQUESTS=120 CONCURRENCY=10 ./scripts/generate-traffic.sh
curl -s http://localhost:8102/metrics | grep http_requests_total
```

## Expected failure evidence

- Argo CD: 배포 자체는 `Synced / Healthy`일 수 있음
- Pod readiness: 정상
- 주문 API: 약 1.25초 후 HTTP 500
- error rate: 임계값 20% 초과
- p95 latency: 임계값 1초 초과
- Alertmanager: `ObservabilityFaultyHighErrorRate`, `ObservabilityFaultyHighLatency`
- Alert label: `application=platform-observability-faulty`

Assistant에서 `platform-observability-faulty`를 선택하고 다음과 같이 질의한다.

```text
현재 애플리케이션 장애 원인을 관측 데이터만 근거로 분석해줘.
확정된 사실과 가설을 구분하고 먼저 실행할 read-only 검증 명령을 알려줘.
```

Assistant는 실행 권한이 없음을 밝히고 Argo CD 상태, 5xx error rate, p95 latency, active alert를 근거로 검증 절차를 제시해야 한다.

## Delivery flow

GitHub Actions, GHCR, Argo CD Image Updater digest/Git write-back, automated sync 설정은 healthy 저장소와 동일하다.

기본 `monitoring.labels.release=monitoring`은 현재 검증 cluster의 Prometheus selector와 일치한다. 다른 cluster에서는 Prometheus의 ServiceMonitor/Rule selector를 먼저 확인한다.

이 장애는 검증을 위해 의도적으로 구현되었다. 운영 workload에 적용하지 않는다. 현재 검증 범위는 metrics와 alert 기반 관측성이며 trace 기반 분산 APM은 포함하지 않는다.
