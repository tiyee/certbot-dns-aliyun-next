"""Alibaba Cloud DNS operations using the official SDK and real request models."""

from typing import Optional

from alibabacloud_alidns20150109 import models
from alibabacloud_alidns20150109.client import Client
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions
from certbot import errors
from Tea.exceptions import TeaException, UnretryableException


class AliCloudDNSClient:
    """Manage individual records without replacing an existing TXT RRset."""

    page_size = 100

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        region_id: str = "cn-hangzhou",
        *,
        security_token: Optional[str] = None,
    ) -> None:
        self.client = Client(
            Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                security_token=security_token,
                region_id=region_id,
                endpoint="alidns.aliyuncs.com",
            )
        )
        # Do not replay a write after a timeout: it may already have succeeded.
        self.runtime = RuntimeOptions(connect_timeout=10000, read_timeout=30000, autoretry=False)

    def _call(self, operation: str, request):
        try:
            body = getattr(self.client, operation)(request, self.runtime).body
        except (TeaException, UnretryableException) as exc:
            # SDK error messages may contain sensitive request information.
            code = getattr(exc, "code", None) or type(exc).__name__
            raise errors.PluginError(f"Aliyun DNS {operation} failed ({code})") from exc
        if body is None:
            raise errors.PluginError(f"Aliyun DNS {operation} returned an empty response")
        return body

    def list_zones(self) -> list[str]:
        zones = []
        page = 1
        while True:
            body = self._call(
                "describe_domains_with_options",
                models.DescribeDomainsRequest(page_number=page, page_size=self.page_size),
            )
            items = (body.domains.domain if body.domains else None) or []
            zones.extend(item.domain_name for item in items)
            if body.total_count is None or (not items and page * self.page_size < body.total_count):
                raise errors.PluginError("Aliyun DNS returned an incomplete zone list")
            if page * self.page_size >= body.total_count:
                return zones
            page += 1

    def get_domain_records(self, domain_name: str, rr: str, record_type: str = "TXT") -> list[dict]:
        records = []
        page = 1
        while True:
            body = self._call(
                "describe_domain_records_with_options",
                models.DescribeDomainRecordsRequest(
                    domain_name=domain_name,
                    rrkey_word=rr,
                    type=record_type,
                    search_mode="EXACT",
                    page_number=page,
                    page_size=self.page_size,
                ),
            )
            items = (body.domain_records.record if body.domain_records else None) or []
            records.extend(
                {
                    "record_id": str(item.record_id),
                    "rr": item.rr,
                    "type": item.type,
                    "value": item.value,
                    "ttl": item.ttl,
                    "line": item.line,
                }
                for item in items
                if item.record_id
                and item.type == record_type
                and item.rr.lower() == rr.lower()
                and item.status == "ENABLE"
                and item.line == "default"
            )
            if body.total_count is None or (not items and page * self.page_size < body.total_count):
                raise errors.PluginError("Aliyun DNS returned an incomplete record list")
            if page * self.page_size >= body.total_count:
                return records
            page += 1

    def add_domain_record(
        self, domain_name: str, rr: str, record_type: str, value: str, ttl: int = 600
    ) -> str:
        body = self._call(
            "add_domain_record_with_options",
            models.AddDomainRecordRequest(
                domain_name=domain_name,
                rr=rr,
                type=record_type,
                value=value,
                ttl=ttl,
                line="default",
            ),
        )
        if not body.record_id:
            raise errors.PluginError("Aliyun DNS did not return a new record ID")
        return str(body.record_id)

    def delete_domain_record(self, record_id: str) -> bool:
        try:
            self._call(
                "delete_domain_record_with_options",
                models.DeleteDomainRecordRequest(record_id=record_id),
            )
        except errors.PluginError as exc:
            if getattr(exc.__cause__, "code", None) != "InvalidRecordId.NotFound":
                raise
        return True

    def update_domain_record(
        self, record_id: str, rr: str, record_type: str, value: str, ttl: int = 600
    ) -> bool:
        """Retain the old client API; the authenticator never updates existing records."""
        self._call(
            "update_domain_record_with_options",
            models.UpdateDomainRecordRequest(
                record_id=record_id,
                rr=rr,
                type=record_type,
                value=value,
                ttl=ttl,
            ),
        )
        return True
