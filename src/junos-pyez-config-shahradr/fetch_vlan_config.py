"""
Retrieve the VLAN configuration from a Juniper Networks appliance.
"""

import sys
import inspect

from connection.connection_info import (
    ConnectionInfoManager,
    NetworkApplianceConnectionInfo,
)
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml import etree
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

VLAN_FILTER = "<configuration><vlans/></configuration>"

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("fetch_vlan_config")
def connect_to_device(device_config: NetworkApplianceConnectionInfo):
    """
    Connect to a Juniper Networks appliance using the provided configuration, and retrieve the
    VLAN configuration.
    """
    junos_config = None

    with tracer.start_as_current_span(name="junos-connection", kind=trace.SpanKind.SERVER) as network_span:
        network_span.set_attributes(
            {
                SpanAttributes.NET_PEER_IP: device_config.hostname,
                SpanAttributes.NET_PEER_NAME: device_config.hostname,
                SpanAttributes.NET_PEER_PORT: 830,
                SpanAttributes.NET_TRANSPORT: "IP.TCP",
                "net.app.protocol.name": "netconf",
                "net.app.protocol.version": "1.0",
                SpanAttributes.ENDUSER_ID: device_config.username,
                SpanAttributes.CODE_FILEPATH: __file__,
                SpanAttributes.CODE_FUNCTION: inspect.currentframe().f_code.co_name,
                SpanAttributes.CODE_LINENO: inspect.currentframe().f_lineno,
                SpanAttributes.CODE_NAMESPACE: __name__
            }
        )

        with Device(
            host=device_config.hostname,
            user=device_config.username,
            password=device_config.password,
        ) as dev:
            try:
                junos_config = dev.rpc.get_config(filter_xml=filter)
            except ConnectError as err:
                network_span.set_status(Status(StatusCode.ERROR, err))
                network_span.record_exception(err)
                sys.exit(1)

    etree.tostring(
        junos_config,
        encoding="unicode",
        pretty_print=True,
    )


with tracer.start_as_current_span("connect_to_device") as span:
    connect_to_device(ConnectionInfoManager().get_configuration())
