# Certbot DNS 阿里云插件

这是一个用于 Certbot 的阿里云 DNS 插件，支持通过阿里云 DNS API 进行 DNS-01 验证来获取 SSL 证书。支持泛域名。

## 功能特性

- 支持通过阿里云DNS API自动管理DNS记录
- 支持泛域名
- 支持certbot 3 版本(更低没测试)
- 兼容 Python 3.8+(含)版本
- 支持 DNS-01 验证方式
- 自动清理临时DNS记录
- 完善的错误处理和日志记录

## 安装

### 从 PyPI 安装

```bash

pip3 install certbot-dns-aliyun-next

```

## 配置文件


```ini
dns_aliyun_next_access_key_id = ??
dns_aliyun_next_access_key_secret = ??
dns_aliyun_next_region_id = cn-hangzhou

```

修改配置文件权限(假如文件是~/aliyun.ini)

`chmod 600 ~/aliyun.ini`


## 运行

```bash

certbot certonly  \
  --authenticator dns-aliyun-next \
  --dns-aliyun-next-credentials ~/aliyun.ini  \
  --dns-aliyun-next-propagation-seconds 30 \
  -d "*.example.com" \
  -d "example.com"

```


## 阿里云权限配置

确保您的阿里云AccessKey具有以下权限：

AliyunDNSFullAccess 或自定义权限策略包含：

* alidns:AddDomainRecord
* alidns:DeleteDomainRecord
* alidns:DescribeDomainRecords
* alidns:UpdateDomainRecord

