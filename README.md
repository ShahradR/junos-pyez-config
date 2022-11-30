# Junos PyEZ configuration fetcher

![GitHub workflow](https://img.shields.io/github/workflow/status/ShahradR/git-template/CI%20workflow?logo=github)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![License: MIT-0](https://img.shields.io/badge/license-MIT--0-yellowgreen)](https://spdx.org/licenses/MIT-0.html)
[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

## Enabling OpenTelemetry

### Running the collector

```shell
docker run \
    -p 4317:4317 \
    -v /tmp/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
    otel/opentelemetry-collector:latest \
    --config=/etc/otel-collector-config.yaml
```

### Running Jaeger

```shell
docker run -d --name jaeger \
    -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
    -p 5775:5775/udp \
    -p 6831:6831/udp \
    -p 6832:6832/udp \
    -p 5778:5778 \
    -p 16686:16686 \
    -p 14268:14268 \
    -p 14250:14250 \
    -p 9411:9411 \
    jaegertracing/all-in-one:latest
```

### Running the application with OpenTelemetry

```shell
opentelemetry-instrument \
    --traces_exporter jaeger \
    --metrics_exporter console \
    python /workspaces/junos-pyez-config/src/junos-pyez-config-shahradr/fetch_vlan_config.py
```

### OpenTelemetry Connector configuration

```yaml
receivers:
  otlp:
    protocols:
      grpc:
exporters:
  logging:
    loglevel: debug
  otlp:
    endpoint: tempo-us-central1.grafana.net:443
    headers:
      authorization: Basic <base64 data>
processors:
  batch:
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlp]
      processors: [batch]
    metrics:
      receivers: [otlp]
      exporters: [logging]
      processors: [batch]
```
