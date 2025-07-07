# Certbot DNS 阿里云插件

这是一个用于 Certbot 的阿里云 DNS 插件，支持通过阿里云 DNS API 进行 DNS-01 验证来获取 SSL 证书。

## 功能特性

- 支持通过阿里云DNS API自动管理DNS记录
- 兼容 Python 3.8+ 版本
- 支持 DNS-01 验证方式
- 自动清理临时DNS记录
- 完善的错误处理和日志记录

## 安装

### 从 PyPI 安装

```bash
pip install certbot-dns-aliyun-next
