"""Use real plugin configuration and mock only the external SDK boundary."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from certbot_dns_aliyun_next.aliyun_client import AliCloudDNSClient
from certbot_dns_aliyun_next.dns_aliyun_next import Authenticator, _AliCloudDNSHelper


@pytest.fixture
def client(monkeypatch):
    sdk = Mock()
    monkeypatch.setattr("certbot_dns_aliyun_next.aliyun_client.Client", Mock(return_value=sdk))
    result = AliCloudDNSClient("id", "secret", security_token="session")
    result.page_size = 2
    return result


@pytest.fixture
def helper(monkeypatch):
    cloud = Mock(spec=AliCloudDNSClient)
    cloud.list_zones.return_value = ["example.com", "example.co.uk", "sub.example.co.uk"]
    cloud.get_domain_records.return_value = []
    cloud.add_domain_record.side_effect = ["101", "102", "103"]
    monkeypatch.setattr(
        "certbot_dns_aliyun_next.dns_aliyun_next.AliCloudDNSClient", Mock(return_value=cloud)
    )
    return _AliCloudDNSHelper("id", "secret", "cn-hangzhou", 600)


@pytest.fixture
def authenticator(helper):
    config = SimpleNamespace(
        dns_aliyun_next_credentials=None,
        dns_aliyun_next_ttl=600,
        dns_aliyun_next_propagation_seconds=0,
        noninteractive_mode=True,
    )
    result = Authenticator(config, "dns-aliyun-next")
    result._helper = helper
    return result
