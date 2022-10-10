"""
This module contains tests for the src/junos-pyez-config-shahradr/connection/connection_info.py
module.
"""

import os
import re
from moto import mock_secretsmanager
import boto3
import pytest
from .connection_info import (
    AWSConfigStrategy,
    MissingConfigurationError,
    MissingCloudProviderEnvVarError,
    MissingConfigItemEnvVarError,
    ConnectionInfoManager,
)


@mock_secretsmanager
def test_retrieve_configuration_from_aws_secretsmanager():
    """
    This test is used to verify that the AWSConfigStrategy class is able to retrieve the
    configuration from AWS Secrets Manager.
    """
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="secret_configuration",
        SecretString='{"username": "juniper", '
        + '"password": "Passw0rd!", '  # pragma: allowlist secret
        + '"hostname": "router1.example.com"}',
    )

    secret = AWSConfigStrategy("secret_configuration").get_secret()
    assert secret.username == "juniper"
    assert secret.password == "Passw0rd!"  # pragma: allowlist secret
    assert secret.hostname == "router1.example.com"


@mock_secretsmanager
def test_retrieve_configuration_from_aws_secretsmanager_with_missing_hostname():
    """
    This test is used to verify that the AWSConfigStrategy class throws a
    `MissingConfigurationError` when the hostname is missing from the configuration.
    """
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="secret_configuration",
        SecretString='{"username": "juniper", "password": "Passw0rd!"}',  # pragma: allowlist secret
    )

    with pytest.raises(
        MissingConfigurationError, match="The hostname configuration item is missing."
    ):
        AWSConfigStrategy("secret_configuration").get_secret()


@mock_secretsmanager
def test_retrieve_configuration_from_aws_secretsmanager_with_missing_password():
    """
    This test is used to verify that the AWSConfigStrategy class throws a
    `MissingConfigurationError` when the password is missing from the configuration.
    """
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="secret_configuration",
        SecretString='{"username": "juniper", "hostname": "router1.example.com"}',
    )  # pragma: allowlist secret

    with pytest.raises(
        MissingConfigurationError, match="The password configuration item is missing."
    ):
        AWSConfigStrategy("secret_configuration").get_secret()


@mock_secretsmanager
def test_retrieve_configuration_from_aws_secretsmanager_with_missing_username():
    """
    This test is used to verify that the AWSConfigStrategy class throws a
    `MissingConfigurationError` when the username is missing from the configuration.
    """
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="secret_configuration",
        SecretString='{"password": "Passw0rd!", "hostname": "router1.example.com"}',  # pragma: allowlist secret
    )

    with pytest.raises(
        MissingConfigurationError, match="The username configuration item is missing."
    ):
        AWSConfigStrategy("secret_configuration").get_secret()


@mock_secretsmanager
def test_retrieve_configuration_from_aws_secretsmanager_with_missing_secret():
    """
    This test is used to verify that the AWSConfigStrategy class throws a `Exception` when the
    secret is missing from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="test_secret",
        SecretString='{"username": "juniper", '
        + '"password": "Passw0rd!", '  # pragma: allowlist secret
        + '"hostname": "router1.example.com"}',
    )

    with pytest.raises(
        Exception,
        match=re.escape(
            "An error occurred (ResourceNotFoundException) when calling the "
            + "GetSecretValue operation: Secrets Manager can't find the specified secret."
        ),
    ):
        AWSConfigStrategy("secret_configuration").get_secret()


def test_connection_info_manager_aws(mocker):
    """
    This test is used to verify that the ConnectionInfoManager class is able to retrieve the
    configuration from AWS Secrets Manager.
    """
    method = mocker.patch.object(AWSConfigStrategy, "__init__", return_value=None)

    os.environ["CONFIGURATION_CLOUD_PROVIDER"] = "AWS"
    os.environ["CONFIGURATION_ITEM_NAME"] = "secret_configuration"

    ConnectionInfoManager().config_manager_factory()

    method.assert_called_once_with("secret_configuration")


def test_connection_info_manager_missing_cloud_provider_env_var():
    """
    This test is used to verify that the ConnectionInfoManager class throws a
    `MissingCloudProviderEnvVarError` when the CONFIGURATION_CLOUD_PROVIDER environment variable is
    missing.
    """

    os.environ.pop("CONFIGURATION_CLOUD_PROVIDER", None)
    os.environ["CONFIGURATION_ITEM_NAME"] = "secret_configuration"

    with pytest.raises(
        MissingCloudProviderEnvVarError,
        match="The CONFIGURATION_CLOUD_PROVIDER environment variable has not been set.",
    ):
        ConnectionInfoManager().config_manager_factory()


def test_connection_info_manager_missing_configuration_item_name_env_var():
    """
    This test is used to verify that the ConnectionInfoManager class throws a
    `MissingConfigItemEnvVarError` when the CONFIGURATION_ITEM_NAME environment variable is
    missing.
    """
    os.environ["CONFIGURATION_CLOUD_PROVIDER"] = "AWS"
    os.environ.pop("CONFIGURATION_ITEM_NAME", None)

    with pytest.raises(
        MissingConfigItemEnvVarError,
        match="The CONFIGURATION_ITEM_NAME environment variable has not been set.",
    ):
        ConnectionInfoManager().config_manager_factory()


def test_connection_info_manager_unsupported_cloud_provider():
    """
    This test is used to verify that the ConnectionInfoManager class throws a
    `IncorrectCloudProviderEnvVarError` when the CONFIGURATION_CLOUD_PROVIDER environment variable
    is set to an unsupported cloud provider.
    """
    os.environ["CONFIGURATION_CLOUD_PROVIDER"] = "GCP"
    os.environ["CONFIGURATION_ITEM_NAME"] = "secret_configuration"

    with pytest.raises(
        NotImplementedError,
        match="The GCP cloud provider is not supported. Valid values are `AWS` or `AZURE`",
    ):
        ConnectionInfoManager().config_manager_factory()


def test_connection_info_manager_azure_not_implemented():
    """
    This test is used to verify that the ConnectionInfoManager class throws a `NotImplementedError`
    when the CONFIGURATION_CLOUD_PROVIDER environment variable is set to `AZURE`.
    """
    os.environ["CONFIGURATION_CLOUD_PROVIDER"] = "AZURE"
    os.environ["CONFIGURATION_ITEM_NAME"] = "secret_configuration"

    with pytest.raises(
        NotImplementedError,
        match="The Azure Cloud integration has not yet been implemented.",
    ):
        ConnectionInfoManager().config_manager_factory()
