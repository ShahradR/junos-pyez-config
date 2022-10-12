"""
Retrieve the VLAN configuration from a Juniper Networks appliance.
"""

import sys

from connection.connection_info import (
    ConnectionInfoManager,
    NetworkApplianceConnectionInfo,
)
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml import etree

VLAN_FILTER = "<configuration><vlans/></configuration>"


def connect_to_device(device_config: NetworkApplianceConnectionInfo):
    """
    Connect to a Juniper Networks appliance using the provided configuration, and retrieve the
    VLAN configuration.
    """
    try:
        with Device(
            host=device_config.hostname,
            user=device_config.username,
            password=device_config.password,
        ) as dev:
            print(
                etree.tostring(
                    dev.rpc.get_config(filter_xml=filter),
                    encoding="unicode",
                    pretty_print=True,
                )
            )
    except ConnectError as err:
        print(f"Cannot connect to device: {err}")
        sys.exit(1)


connect_to_device(ConnectionInfoManager().get_configuration())