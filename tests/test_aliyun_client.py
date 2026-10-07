from types import SimpleNamespace

import pytest
from alibabacloud_alidns20150109 import models
from certbot import errors
from Tea.exceptions import TeaException, UnretryableException


def dto(cls, data):
    return SimpleNamespace(body=cls().from_map(data))


def zones(names, total):
    return dto(
        models.DescribeDomainsResponseBody,
        {
            "TotalCount": total,
            "Domains": {"Domain": [{"DomainName": name} for name in names]},
        },
    )


def records(items, total):
    return dto(
        models.DescribeDomainRecordsResponseBody,
        {
            "TotalCount": total,
            "DomainRecords": {"Record": items},
        },
    )


def record(id_, rr="host", value="token", type_="TXT", status="ENABLE", line="default"):
    return {
        "RecordId": id_,
        "RR": rr,
        "Value": value,
        "Type": type_,
        "Status": status,
        "Line": line,
        "TTL": 600,
    }


def test_all_zone_pages(client):
    call = client.client.describe_domains_with_options
    call.side_effect = [zones(["example.com", "example.co.uk"], 3), zones(["sub.example.co.uk"], 3)]
    assert client.list_zones() == ["example.com", "example.co.uk", "sub.example.co.uk"]
    assert [item.args[0].to_map() for item in call.call_args_list] == [
        {"PageNumber": 1, "PageSize": 2},
        {"PageNumber": 2, "PageSize": 2},
    ]


def test_all_record_pages_and_exact_host_filter(client):
    call = client.client.describe_domain_records_with_options
    call.side_effect = [
        records([record("1"), record("2", rr="other-host")], 3),
        records([record("3", value="second-value")], 3),
    ]
    found = client.get_domain_records("example.com", "host")
    assert [(item["record_id"], item["value"]) for item in found] == [
        ("1", "token"),
        ("3", "second-value"),
    ]
    assert call.call_args.args[0].to_map() == {
        "DomainName": "example.com",
        "RRKeyWord": "host",
        "Type": "TXT",
        "SearchMode": "EXACT",
        "PageNumber": 2,
        "PageSize": 2,
    }


def test_only_active_txt_on_default_line_reused(client):
    client.client.describe_domain_records_with_options.return_value = records(
        [record("1", status="DISABLE"), record("2", type_="CNAME"), record("3", line="telecom")], 3
    )
    client.page_size = 100
    assert client.get_domain_records("example.com", "host") == []


def test_empty_lists(client):
    client.client.describe_domains_with_options.return_value = zones([], 0)
    client.client.describe_domain_records_with_options.return_value = records([], 0)
    assert client.list_zones() == []
    assert client.get_domain_records("example.com", "@") == []


@pytest.mark.parametrize("kind", ["zones", "records"])
@pytest.mark.parametrize("total", [10, None])
def test_incomplete_pagination_fails(client, kind, total):
    if kind == "zones":
        client.client.describe_domains_with_options.return_value = zones([], total)
        operation = client.list_zones
    else:
        client.client.describe_domain_records_with_options.return_value = records([], total)

        def operation():
            return client.get_domain_records("example.com", "host")

    with pytest.raises(errors.PluginError, match="incomplete"):
        operation()


def test_create_delete_update_real_sdk_request_schema(client):
    client.client.add_domain_record_with_options.return_value = dto(
        models.AddDomainRecordResponseBody, {"RecordId": "123"}
    )
    assert client.add_domain_record("example.com", "@", "TXT", "token", 600) == "123"
    call = client.client.add_domain_record_with_options
    assert call.call_args.args[0].to_map() == {
        "DomainName": "example.com",
        "RR": "@",
        "Type": "TXT",
        "Value": "token",
        "TTL": 600,
        "Line": "default",
    }
    assert call.call_args.args[1].autoretry is False
    assert client.delete_domain_record("123") is True
    assert client.client.delete_domain_record_with_options.call_args.args[0].to_map() == {
        "RecordId": "123"
    }
    assert client.update_domain_record("123", "host", "TXT", "new") is True
    assert client.client.update_domain_record_with_options.call_args.args[0].to_map() == {
        "RecordId": "123",
        "RR": "host",
        "Type": "TXT",
        "Value": "new",
        "TTL": 600,
    }


def test_create_requires_record_id(client):
    client.client.add_domain_record_with_options.return_value = dto(
        models.AddDomainRecordResponseBody, {}
    )
    with pytest.raises(errors.PluginError, match="record ID"):
        client.add_domain_record("example.com", "host", "TXT", "token")


@pytest.mark.parametrize(
    "operation",
    [
        "describe_domains",
        "describe_domain_records",
        "add_domain_record",
        "delete_domain_record",
        "update_domain_record",
    ],
)
def test_permission_errors_are_redacted(client, operation):
    getattr(client.client, operation + "_with_options").side_effect = TeaException(
        {"code": "UnauthorizedOperation", "message": "sensitive request details"}
    )
    with pytest.raises(errors.PluginError, match="UnauthorizedOperation") as exc:
        if operation == "describe_domains":
            client.list_zones()
        elif operation == "describe_domain_records":
            client.get_domain_records("example.com", "host")
        elif operation == "add_domain_record":
            client.add_domain_record("example.com", "host", "TXT", "token")
        elif operation == "delete_domain_record":
            client.delete_domain_record("123")
        else:
            client.update_domain_record("123", "host", "TXT", "token")
    assert "sensitive" not in str(exc.value)


def test_already_deleted_record_is_success(client):
    client.client.delete_domain_record_with_options.side_effect = TeaException(
        {"code": "InvalidRecordId.NotFound", "message": "gone"}
    )
    assert client.delete_domain_record("123") is True


def test_empty_response(client):
    client.client.describe_domains_with_options.return_value = SimpleNamespace(body=None)
    with pytest.raises(errors.PluginError, match="empty response"):
        client.list_zones()


def test_network_failure_is_a_plugin_error(client):
    client.client.describe_domains_with_options.side_effect = UnretryableException(
        None, OSError("sensitive network details")
    )
    with pytest.raises(errors.PluginError, match="UnretryableException") as exc:
        client.list_zones()
    assert "sensitive" not in str(exc.value)
