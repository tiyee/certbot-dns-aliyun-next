"""
阿里云DNS API客户端
"""

import logging
from typing import Any, Dict, List

from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_tea_openapi import models as open_api_models

logger = logging.getLogger(__name__)


class AliCloudDNSClient:
    """阿里云DNS客户端"""

    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-hangzhou"):
        """
        初始化阿里云DNS客户端

        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :param region_id: 地域ID，默认为cn-hangzhou
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region_id = region_id
        self.client = self._create_client()

    def _create_client(self) -> Alidns20150109Client:
        """创建阿里云DNS客户端"""
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id
        )
        config.endpoint = f"alidns.{self.region_id}.aliyuncs.com"
        return Alidns20150109Client(config)

    def get_domain_records(self, domain_name: str, rr: str, record_type: str = "TXT") -> List[Dict[str, Any]]:
        """
        获取域名记录

        :param domain_name: 域名
        :param rr: 主机记录
        :param record_type: 记录类型
        :return: 记录列表
        """
        try:
            request = alidns_20150109_models.DescribeDomainRecordsRequest(
                domain_name=domain_name,
                rrkey_word=rr,
                type=record_type
            )
            response = self.client.describe_domain_records(request)

            if response.body and response.body.domain_records:
                return [
                    {
                        "record_id": record.record_id,
                        "rr": record.rr,
                        "type": record.type,
                        "value": record.value,
                        "ttl": record.ttl,
                        "line": record.line
                    }
                    for record in response.body.domain_records.record
                ]
            return []
        except Exception as e:
            logger.error(f"获取域名记录失败: {e}")
            raise

    def add_domain_record(self, domain_name: str, rr: str, record_type: str, value: str, ttl: int = 600) -> str:
        """
        添加域名记录

        :param domain_name: 域名
        :param rr: 主机记录
        :param record_type: 记录类型
        :param value: 记录值
        :param ttl: TTL值
        :return: 记录ID
        """
        try:
            request = alidns_20150109_models.AddDomainRecordRequest(
                domain_name=domain_name,
                rr=rr,
                type=record_type,
                value=value,
                ttl=ttl
            )
            response = self.client.add_domain_record(request)

            if response.body and response.body.record_id:
                logger.info(f"成功添加DNS记录: {rr}.{domain_name} -> {value}")
                return response.body.record_id
            else:
                raise Exception("添加记录失败，未返回记录ID")
        except Exception as e:
            logger.error(f"添加域名记录失败: {e}")
            raise

    def delete_domain_record(self, record_id: str) -> bool:
        """
        删除域名记录

        :param record_id: 记录ID
        :return: 是否成功
        """
        try:
            request = alidns_20150109_models.DeleteDomainRecordRequest(
                record_id=record_id
            )
            response = self.client.delete_domain_record(request)

            logger.info(f"成功删除DNS记录: {record_id} {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"删除域名记录失败: {e}")
            raise

    def update_domain_record(self, record_id: str, rr: str, record_type: str, value: str, ttl: int = 600) -> bool:
        """
        更新域名记录

        :param record_id: 记录ID
        :param rr: 主机记录
        :param record_type: 记录类型
        :param value: 记录值
        :param ttl: TTL值
        :return: 是否成功
        """
        try:
            request = alidns_20150109_models.UpdateDomainRecordRequest(
                record_id=record_id,
                rr=rr,
                type=record_type,
                value=value,
                ttl=ttl
            )
            response = self.client.update_domain_record(request)

            logger.info(f"成功更新DNS记录: {record_id} {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"更新域名记录失败: {e}")
            raise

    @staticmethod
    def get_root_domain(domain: str) -> str:
        """
        获取根域名

        :param domain: 完整域名
        :return: 根域名
        """
        # 简单的根域名提取逻辑，可以根据需要完善
        parts = domain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return domain
