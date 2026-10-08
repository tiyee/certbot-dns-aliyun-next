# Certbot DNS 阿里云插件

这是一个用于 Certbot 的阿里云 DNS 插件，支持通过阿里云 DNS API 进行 DNS-01 验证来获取 SSL 证书。支持泛域名。

## 功能特性

- 支持通过阿里云 DNS API 自动管理 DNS 记录
- 支持普通域名、子域名和泛域名
- 支持 Certbot 3、4 和 5
- 兼容 Python 3.9–3.14
- 支持 DNS-01 验证方式
- 自动清理本次创建的临时 DNS 记录，保留已有记录
- 支持 STS 临时凭证
- 完善的错误处理和日志记录

Python 3.9 支持 Certbot 3 和 4，Python 3.10–3.13 支持 Certbot 3、4 和 5，Python 3.14 支持 Certbot 4 和 5。
使用 Certbot 3 时需安装 `pyopenssl<25`，Certbot 4 和 5 由上游依赖选择兼容版本。

## 安装

### 从 PyPI 安装

```bash
pip3 install certbot-dns-aliyun-next
```

插件需安装在实际运行的 Certbot 所在的 Python 环境中。

## 配置文件

```ini
dns_aliyun_next_access_key_id = YOUR_ACCESS_KEY_ID
dns_aliyun_next_access_key_secret = YOUR_ACCESS_KEY_SECRET
# 可选，默认 cn-hangzhou
dns_aliyun_next_region_id = cn-hangzhou
# 可选，STS 临时凭证
dns_aliyun_next_security_token = YOUR_SECURITY_TOKEN
```

使用 AccessKey 长期凭证时无需配置 `security_token`。使用 STS 临时凭证时，续期前需确保凭证仍有效。

插件自动查询并匹配阿里云托管域名，无需手动配置。

修改配置文件权限（假如文件是 `~/aliyun.ini`）：

```bash
chmod 600 ~/aliyun.ini
```

Windows 用户请通过系统文件权限限制凭证文件的访问。

## 运行

```bash
certbot certonly \
  --authenticator dns-aliyun-next \
  --dns-aliyun-next-credentials ~/aliyun.ini \
  --dns-aliyun-next-propagation-seconds 30 \
  -d "*.example.com" \
  -d "example.com"
```

DNS 传播等待默认 30 秒，可根据实际情况调整。TXT 记录 TTL 默认 600 秒，可通过 `--dns-aliyun-next-ttl` 设置，实际允许值取决于阿里云套餐。

后续使用 `certbot renew` 自动续期。

## 阿里云权限配置

确保您的阿里云 AccessKey 具有 `AliyunDNSFullAccess`，或自定义权限策略包含：

- `alidns:AddDomainRecord`
- `alidns:DeleteDomainRecord`
- `alidns:DescribeDomainRecords`
- `alidns:DescribeDomains`

从 1.x 升级时可继续使用原来的认证器名称、命令行参数和 AccessKey 配置。使用自定义权限策略时，请新增 `DescribeDomains` 权限。

## 自动部署

此程序只是 Certbot 的 DNS 验证插件，如果需要自动运行申请部署，可以使用 [AutoCert](https://github.com/tiyee/AutoCert)。
