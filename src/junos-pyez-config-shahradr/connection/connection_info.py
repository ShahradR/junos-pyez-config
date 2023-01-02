"""
The connection_info module provides classes and methods to retrieve connection information for the
Junos devices we want to parse.

The AbstractConnectionInfoManager and its concrete implementations are used to retrieve the
connection information from different sources. Currently AWS Secrets Manager and Azure are
supported as sources.

The factory method returns a NetworkApplianceConnectionInfo object which contains the hostname,
username, and password used to connect to the appliance.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from opentelemetry import trace
import json
import os
import boto3

tracer = trace.get_tracer("junos_pyez_config")

class AbstractConnectionInfoManager(ABC):
    """
    This AbstractCredentialsManager class defines the interface for the concrete implementations of
    the Factory Method design pattern.

    It creates objects of type ConfigStrategy which are used to retrieve the credentials from
    different sources. The get_configuration method then retrieves the connection information from
    the ConfigStrategy, and returns a NetworkApplianceConnectionInfo model object which can be
    consumed by the caller to connect to the network appliance.
    """

    @abstractmethod
    def config_manager_factory(self) -> ConfigStrategy:
        """
        This method is used to create a concrete implementation of the ConfigStrategy class.
        """

    @tracer.start_as_current_span("AbstractConnectionInfoManager.get_configuration")
    def get_configuration(self) -> NetworkApplianceConnectionInfo:
        """
        This method is used to retrieve the credentials from the concrete implementation of the
        ConfigStrategy class.
        """
        credential_manager = self.config_manager_factory()
        return credential_manager.get_secret()


class ConnectionInfoManager(AbstractConnectionInfoManager):
    """
    This class retrieves credential information from different cloud providers. Environment
    variables are used to control the cloud provider and the name of the resource from which the
    configuration should be retrieved.
    """

    @tracer.start_as_current_span("ConnectionInfoManager.__init__")
    def __init__(self):
        """
        This method is used to instantiate the ConnectionInfoManager class. It sets the cloud
        provider and configuration item name from which the network appliance connection info
        should be retrieved.

        Raises:
            MissingConfigurationError: The CONFIGURATION_CLOUD_PROVIDER environment variable is not
            defined.
            MissingConfigurationError: The CONFIGURATION_ITEM_NAME environment variable is not
            defined.
        """
        if os.getenv("CONFIGURATION_CLOUD_PROVIDER") is None:
            raise MissingCloudProviderEnvVarError()
        if os.getenv("CONFIGURATION_ITEM_NAME") is None:
            raise MissingConfigItemEnvVarError()
        self.cloud_provider = os.getenv("CONFIGURATION_CLOUD_PROVIDER")
        self.config_name = os.getenv("CONFIGURATION_ITEM_NAME")

        if self.cloud_provider not in ["AWS", "AZURE"]:
            raise IncorrectCloudProviderEnvVarError(self.cloud_provider)

    @tracer.start_as_current_span("ConnectionInfoManager.config_manager_factory")
    def config_manager_factory(self):
        """
        This method is used to create a ConfigStrategy based on the cloud provider used to retrieve
        the configuration.
        """
        match self.cloud_provider:
            case "AWS":
                return AWSConfigStrategy(self.config_name)
            case "AZURE":
                raise NotImplementedError(
                    "The Azure Cloud integration has not yet been implemented."
                )


class NetworkApplianceConnectionInfo:
    """
    The NetworkApplianceConnectionInfo class stores credentials for a given network appliance.
    """

    @tracer.start_as_current_span("NetworkApplianceConnectionInfo.__init__")
    def __init__(self, username, password, hostname):
        """
        The constructor for the NetworkApplianceConnectionInfo class.
        :param username: The username to use to connect to the network appliance.
        :param password: The password to use to connect to the network appliance.
        :param hostname: The hostname of the network appliance.
        """
        self.username = username
        self.password = password
        self.hostname = hostname


class ConfigStrategy(ABC):
    """
    The SecretStrategy class is used to define the interface for the concrete implementations of
    the SecretStrategy class.
    """

    @abstractmethod
    def get_secret(self) -> NetworkApplianceConnectionInfo:
        """
        The get_secret method is used to retrieve the secret from the secret store.
        :return: The secret from the secret store.
        """


class AWSConfigStrategy(ConfigStrategy):
    """
    The AWSSecretStrategy class is used to retrieve the credentials from AWS Secrets Manager.
    """

    @tracer.start_as_current_span("AWSConfigStrategy.__init__")
    def __init__(self, config_name):
        """
        The constructor for the AWSSecretStrategy class.
        """
        self.secret_id = config_name

        self.client = boto3.client(
            service_name="secretsmanager", region_name="us-east-1"
        )

    @tracer.start_as_current_span("AWSConfigStrategy.get_secret")
    def get_secret(self) -> NetworkApplianceConnectionInfo:
        """
        The get_secret method is used to retrieve the credentials from AWS Secrets Manager.
        :return: The credentials for the network appliance.
        """

        secret_string = self.client.get_secret_value(SecretId=self.secret_id)[
            "SecretString"
        ]

        secret_json = json.loads(secret_string)

        try:
            config = NetworkApplianceConnectionInfo(
                username=secret_json["username"],
                password=secret_json["password"],
                hostname=secret_json["hostname"],
            )
        except KeyError as error:
            raise MissingConfigurationError(error.args[0]) from error

        return config


class MissingCloudProviderEnvVarError(Exception):
    """Raised when a cloud provider environment variable is missing."""

    def __init__(self):
        super().__init__(
            self,
            "The CONFIGURATION_CLOUD_PROVIDER environment variable has not been set.",
        )


class MissingConfigItemEnvVarError(Exception):
    """Raised when a cloud provider environment variable is missing."""

    def __init__(self):
        super().__init__(
            self, "The CONFIGURATION_ITEM_NAME environment variable has not been set."
        )


class IncorrectCloudProviderEnvVarError(Exception):
    """Raised when a configuration item is missing."""

    def __init__(self, cloud_provider):
        self.cloud_provider = cloud_provider
        super().__init__(
            self,
            f"The {cloud_provider} cloud provider is not supported. "
            + "Valid values are `AWS` or `AZURE`",
        )


class MissingConfigurationError(Exception):
    """Raised when a configuration item is missing from the configuration."""

    def __init__(self, configuration_item):
        super().__init__(
            self, f"The {configuration_item} configuration item is missing."
        )
