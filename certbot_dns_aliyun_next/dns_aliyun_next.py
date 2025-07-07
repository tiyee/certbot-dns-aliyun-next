"""
阿里云DNS认证器插件
"""

import logging
import time
from typing import Any, Callable, Optional

import zope.interface
from certbot import errors, interfaces
from certbot.plugins import dns_common

from .aliyun_client import AliCloudDNSClient

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """阿里云DNS认证器"""

    description = "通过阿里云DNS API获取证书，使用DNS-01验证"
    ttl = 600  # DNS记录TTL

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.credentials: Optional[dns_common.CredentialsConfiguration] = None

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None], default_propagation_seconds: int = 30) -> None:
        """添加命令行参数"""
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="阿里云API凭证文件路径")

    def more_info(self) -> str:
        """返回插件的更多信息"""
        return (
            "此插件通过阿里云DNS API配置DNS记录来完成DNS-01验证。"
            "需要在凭证文件中配置阿里云AccessKey ID和AccessKey Secret。"
        )

    def _setup_credentials(self) -> None:
        """设置API凭证"""
        self.credentials = self._configure_credentials(
            "credentials",
            "阿里云API凭证文件路径",
            {
                "access_key_id": "阿里云AccessKey ID",
                "access_key_secret": "阿里云AccessKey Secret",
               # "region_id": "阿里云地域ID (可选，默认为cn-hangzhou)"
            }
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        """
        添加DNS TXT记录进行验证

        :param domain: 要验证的域名
        :param validation_name: 验证记录名称
        :param validation: 验证值
        """
        self._get_alicloud_client().add_txt_record(validation_name, validation)

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        """
        清理DNS TXT记录

        :param domain: 要验证的域名
        :param validation_name: 验证记录名称
        :param validation: 验证值
        """
        self._get_alicloud_client().del_txt_record(validation_name, validation)

    def _get_alicloud_client(self) -> "_AliCloudDNSHelper":
        """获取阿里云DNS客户端"""
        if not self.credentials:
            raise errors.Error("凭证未配置")

        access_key_id = self.credentials.conf("access_key_id")
        access_key_secret = self.credentials.conf("access_key_secret")
        region_id = self.credentials.conf("region_id") or "cn-hangzhou"

        return _AliCloudDNSHelper(access_key_id, access_key_secret, region_id, self.ttl)


def _get_rr_from_record_name(record_name: str, domain: str) -> str:
    """
    从记录名称获取主机记录

    :param record_name: 完整的记录名称
    :param domain: 根域名
    :return: 主机记录
    """
    if record_name.endswith("." + domain):
        rr = record_name[:-len(domain) - 1]
    else:
        rr = record_name

    return rr


class _AliCloudDNSHelper:
    """阿里云DNS辅助类"""

    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str, ttl: int):
        """
        初始化DNS辅助类

        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :param region_id: 地域ID
        :param ttl: DNS记录TTL
        """
        self.client = AliCloudDNSClient(access_key_id, access_key_secret, region_id)
        self.ttl = ttl
        self._record_ids = {}  # 存储添加的记录ID，用于清理

    def add_txt_record(self, record_name: str, record_content: str) -> None:
        """
        添加TXT记录

        :param record_name: 记录名称
        :param record_content: 记录内容
        """
        domain = self._get_domain_from_record_name(record_name)
        rr = _get_rr_from_record_name(record_name, domain)

        logger.debug(f"添加TXT记录: {record_name} -> {record_content}")

        try:
            # 检查是否已存在相同的记录
            existing_records = self.client.get_domain_records(domain, rr, "TXT")
            for record in existing_records:
                if record["value"] == record_content:
                    logger.info(f"TXT记录已存在: {record_name}")
                    self._record_ids[record_name] = record["record_id"]
                    return

            # 添加新记录
            record_id = self.client.add_domain_record(domain, rr, "TXT", record_content, self.ttl)
            self._record_ids[record_name] = record_id

            # 等待DNS传播
            time.sleep(10)

        except Exception as e:
            logger.error(f"添加TXT记录失败: {e}")
            raise errors.PluginError(f"添加TXT记录失败: {e}")

    def del_txt_record(self, record_name: str, record_content: str) -> None:
        """
        删除TXT记录

        :param record_name: 记录名称
        :param record_content: 记录内容
        """
        logger.debug(f"删除TXT记录: {record_name}")

        try:
            # 使用存储的记录ID删除
            if record_name in self._record_ids:
                record_id = self._record_ids[record_name]
                self.client.delete_domain_record(record_id)
                del self._record_ids[record_name]
                return

            # 如果没有存储的记录ID，尝试查找并删除
            domain = self._get_domain_from_record_name(record_name)
            rr = _get_rr_from_record_name(record_name, domain)

            existing_records = self.client.get_domain_records(domain, rr, "TXT")
            for record in existing_records:
                if record["value"] == record_content:
                    self.client.delete_domain_record(record["record_id"])
                    break
            else:
                logger.warning(f"未找到要删除的TXT记录: {record_name}")

        except Exception as e:
            logger.error(f"删除TXT记录失败: {e}")
            # 清理时的错误不应该导致程序失败
            logger.warning(f"清理TXT记录时出错，但不影响证书获取: {e}")

    @staticmethod
    def _get_domain_from_record_name(record_name: str) -> str:
        """
        从记录名称获取域名

        :param record_name: 完整的记录名称
        :return: 根域名
        """
        # 移除 _acme-challenge. 前缀
        if record_name.startswith("_acme-challenge."):
            domain = record_name[16:]  # 移除 "_acme-challenge." 前缀
        else:
            domain = record_name

        return AliCloudDNSClient.get_root_domain(domain)
