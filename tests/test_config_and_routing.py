from unittest.mock import Mock

import pytest
from certbot import errors
from certbot.compat import filesystem

from certbot_dns_aliyun_next.dns_aliyun_next import _get_rr_from_record_name, _normalize_name


@pytest.mark.parametrize(
    ("name", "zone", "rr"),
    [
        ("_acme-challenge.sub.example.co.uk", "example.co.uk", "_acme-challenge.sub"),
        ("Example.COM.", "example.com", "@"),
        ("_ACME-CHALLENGE.Example.COM.", "EXAMPLE.COM.", "_acme-challenge"),
    ],
)
def test_relative_name(name, zone, rr):
    assert _get_rr_from_record_name(name, zone) == rr


def test_zone_label_boundary(helper):
    with pytest.raises(errors.PluginError, match="No managed"):
        helper._get_domain_from_record_name("notexample.com")
    with pytest.raises(errors.PluginError, match="outside zone"):
        _get_rr_from_record_name("notexample.com", "example.com")


def test_longest_managed_zone_and_cached_discovery(helper):
    assert helper._get_domain_from_record_name("_acme-challenge.sub.example.co.uk") == (
        "sub.example.co.uk"
    )
    assert helper._get_domain_from_record_name("_acme-challenge.other.example.co.uk") == (
        "example.co.uk"
    )
    helper.client.list_zones.assert_called_once()


def test_failed_discovery_can_be_retried(helper):
    helper.client.list_zones.side_effect = [errors.PluginError("denied"), ["example.com"]]
    with pytest.raises(errors.PluginError):
        helper._get_domain_from_record_name("_acme-challenge.example.com")
    assert helper._zones is None
    assert helper._get_domain_from_record_name("_acme-challenge.example.com") == "example.com"


def test_unicode_name():
    assert _normalize_name("例子.公司.cn.") == "xn--fsqu00a.xn--55qx5d.cn"


@pytest.mark.parametrize("name", ["", "*.example.com", "a..com"])
def test_invalid_name(name):
    with pytest.raises(errors.PluginError):
        _normalize_name(name)


def write_credentials(tmp_path, authenticator, text):
    path = tmp_path / "aliyun.ini"
    path.write_text(text, encoding="utf-8")
    filesystem.chmod(str(path), 0o600)
    authenticator.config.dns_aliyun_next_credentials = str(path)
    authenticator._helper = None
    return path


def test_real_credentials_and_client_reuse(tmp_path, authenticator, monkeypatch):
    factory = Mock()
    monkeypatch.setattr("certbot_dns_aliyun_next.dns_aliyun_next.AliCloudDNSClient", factory)
    path = write_credentials(
        tmp_path,
        authenticator,
        """
dns_aliyun_next_access_key_id = id
dns_aliyun_next_access_key_secret = secret
dns_aliyun_next_region_id = cn-shanghai
dns_aliyun_next_security_token = session
""",
    )
    authenticator._setup_credentials()
    saved = authenticator._get_alicloud_client()
    authenticator._setup_credentials()
    assert authenticator._get_alicloud_client() is saved
    assert authenticator.credentials.conf("access_key_id") == "id"
    assert authenticator.conf("credentials") == str(path)
    factory.assert_called_once_with("id", "secret", "cn-shanghai", security_token="session")
    factory.return_value.list_zones.return_value = ["Example.co.uk.", "sub.example.co.uk"]
    assert saved._get_domain_from_record_name("_acme-challenge.sub.example.co.uk") == (
        "sub.example.co.uk"
    )
    factory.return_value.list_zones.assert_called_once()


def test_legacy_credentials_defaults(tmp_path, authenticator, monkeypatch):
    factory = Mock()
    monkeypatch.setattr("certbot_dns_aliyun_next.dns_aliyun_next.AliCloudDNSClient", factory)
    write_credentials(
        tmp_path,
        authenticator,
        """
dns_aliyun_next_access_key_id = id
dns_aliyun_next_access_key_secret = secret
""",
    )
    authenticator._setup_credentials()
    factory.assert_called_once_with("id", "secret", "cn-hangzhou", security_token=None)
    assert authenticator._helper._zones is None


@pytest.mark.parametrize(
    "text",
    [
        "",
        "dns_aliyun_next_access_key_id=id",
        "dns_aliyun_next_access_key_id=id\ndns_aliyun_next_access_key_secret=",
        "dns_aliyun_next_access_key_id=\ndns_aliyun_next_access_key_secret=secret",
    ],
)
def test_invalid_credentials(tmp_path, authenticator, text):
    write_credentials(tmp_path, authenticator, text)
    with pytest.raises(errors.PluginError):
        authenticator._setup_credentials()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("dns_aliyun_next_ttl", 0),
        ("dns_aliyun_next_ttl", -1),
        ("dns_aliyun_next_propagation_seconds", -1),
    ],
)
def test_invalid_options(authenticator, key, value):
    setattr(authenticator.config, key, value)
    with pytest.raises(errors.PluginError):
        authenticator._setup_credentials()


def test_unconfigured_authenticator(authenticator):
    authenticator._helper = None
    with pytest.raises(errors.PluginError, match="not been configured"):
        authenticator._perform("example.com", "_acme-challenge.example.com", "token")
    authenticator._cleanup("example.com", "_acme-challenge.example.com", "token")
