from unittest.mock import Mock

import josepy
import pytest
from acme import challenges, messages
from certbot import achallenges, errors
from cryptography.hazmat.primitives.asymmetric import rsa

from certbot_dns_aliyun_next.compat import certbot_major_version

FQDN = "_acme-challenge.example.com"


def test_create_and_cleanup_uses_saved_id(authenticator, helper):
    authenticator._perform("example.com", FQDN, "token")
    helper.client.add_domain_record.assert_called_once_with(
        "example.com", "_acme-challenge", "TXT", "token", 600
    )
    helper.client.list_zones.side_effect = AssertionError("cleanup must not discover zones")
    helper.client.get_domain_records.side_effect = AssertionError("cleanup must not list records")
    authenticator._cleanup("example.com", FQDN, "token")
    authenticator._cleanup("example.com", FQDN, "token")
    helper.client.delete_domain_record.assert_called_once_with("101")
    assert not helper._leases


def test_apex_and_wildcard_keep_both_values(authenticator, helper):
    authenticator._perform("example.com", FQDN, "apex-token")
    authenticator._perform("*.example.com", FQDN, "wildcard-token")
    assert [call.args[3] for call in helper.client.add_domain_record.call_args_list] == [
        "apex-token",
        "wildcard-token",
    ]
    authenticator._cleanup("example.com", FQDN, "apex-token")
    assert len(helper._leases) == 1
    authenticator._cleanup("*.example.com", FQDN, "wildcard-token")
    assert [call.args[0] for call in helper.client.delete_domain_record.call_args_list] == [
        "101",
        "102",
    ]


def test_shared_value_lives_until_last_user(helper):
    helper.add_txt_record(FQDN, "token")
    helper.add_txt_record(FQDN.upper() + ".", "token")
    helper.client.add_domain_record.assert_called_once()
    helper.del_txt_record(FQDN, "token")
    helper.client.delete_domain_record.assert_not_called()
    helper.del_txt_record(FQDN, "token")
    helper.client.delete_domain_record.assert_called_once_with("101")


def test_preexisting_record_is_not_owned(helper):
    helper.client.get_domain_records.return_value = [{"record_id": "old-id", "value": "token"}]
    helper.add_txt_record(FQDN, "token")
    helper.del_txt_record(FQDN, "token")
    helper.client.add_domain_record.assert_not_called()
    helper.client.delete_domain_record.assert_not_called()
    assert not helper._leases


def test_unrelated_txt_is_preserved(authenticator, helper):
    helper.client.get_domain_records.return_value = [{"record_id": "old-id", "value": "other"}]
    test_create_and_cleanup_uses_saved_id(authenticator, helper)


@pytest.mark.parametrize("operation", ["list_zones", "get_domain_records", "add_domain_record"])
def test_failed_perform_does_not_delete_unknown_records(helper, operation):
    getattr(helper.client, operation).side_effect = errors.PluginError("permission denied")
    with pytest.raises(errors.PluginError, match="permission denied"):
        helper.add_txt_record(FQDN, "token")
    helper.del_txt_record(FQDN, "token")
    helper.client.delete_domain_record.assert_not_called()
    assert not helper._leases


def test_cleanup_error_can_be_retried(helper, caplog):
    helper.add_txt_record(FQDN, "token")
    helper.client.delete_domain_record.side_effect = [errors.PluginError("permission denied"), True]
    helper.del_txt_record(FQDN, "token")
    assert "permission denied" in caplog.text
    assert len(helper._leases) == 1
    helper.del_txt_record(FQDN, "token")
    assert not helper._leases


def test_certbot_public_lifecycle_uses_real_acme_challenges(authenticator, helper, monkeypatch):
    # Certbot 3 uses domain; newer Certbot 5 uses identifier. Construct actual
    # annotated challenges so a Mock cannot hide host API incompatibilities.
    key = josepy.JWKRSA(key=rsa.generate_private_key(public_exponent=65537, key_size=2048))
    achalls = []
    for token in [b"apex-token-123456", b"wildcard-token-1"]:
        arguments = {"domain": "example.com"}
        if certbot_major_version() >= 5 and "identifier" in (
            achallenges.KeyAuthorizationAnnotatedChallenge.__slots__
        ):
            arguments = {
                "identifier": messages.Identifier(typ=messages.IDENTIFIER_FQDN, value="example.com")
            }
        achalls.append(
            achallenges.KeyAuthorizationAnnotatedChallenge(
                challb=messages.ChallengeBody(chall=challenges.DNS01(token=token)),
                account_key=key,
                **arguments,
            )
        )
    sleep = Mock()
    monkeypatch.setattr("certbot.plugins.dns_common.sleep", sleep)
    monkeypatch.setattr("certbot.plugins.dns_common.display_util.notify", Mock())
    responses = authenticator.perform(achalls)
    assert len(responses) == 2
    assert all(isinstance(response, challenges.DNS01Response) for response in responses)
    sleep.assert_called_once_with(0)
    authenticator.cleanup(achalls)
    assert helper.client.delete_domain_record.call_count == 2
    assert not helper._leases


def test_public_lifecycle_cleans_partial_failure(authenticator, helper, monkeypatch):
    monkeypatch.setattr(authenticator, "_setup_credentials", Mock())
    helper.client.add_domain_record.side_effect = ["101", errors.PluginError("write failed")]
    # The base sets its cleanup flag before any write. Both host APIs are covered.
    from types import SimpleNamespace

    achalls = []
    for token in ["first", "second"]:
        challenge = Mock()
        challenge.domain = "example.com"
        challenge.identifier = SimpleNamespace(value="example.com")
        challenge.validation_domain_name.return_value = FQDN
        challenge.validation.return_value = token
        achalls.append(challenge)
    with pytest.raises(errors.PluginError, match="write failed"):
        authenticator.perform(achalls)
    authenticator.cleanup(achalls)
    helper.client.delete_domain_record.assert_called_once_with("101")
