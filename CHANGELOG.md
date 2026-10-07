# 更新记录

## 2.0.0

- 支持 Python 3.9–3.14，Certbot 3 和 5 共用一个实现；Python 3.9 使用 Certbot 3，Python 3.14 使用 Certbot 5（Certbot 3 的 josepy 1.x 不兼容延迟注解）。
- 使用 uv、Hatchling、pyproject.toml 和 uv.lock 管理依赖与构建，移除重复的 setup.py 和 requirements.txt。
- 移除 zope.interface 装饰器，继承 Certbot 公共 DNSAuthenticator；文件权限检查委托 Certbot 兼容模块。
- 增加 pytest、真实 SDK DTO 测试、tox-uv 的 10 组 wheel 兼容测试及 Certbot CLI 插件发现检查。
- CI 和发布流程均要求 Certbot 3/5 完整矩阵通过；发布标签必须与项目版本一致。
- 修复客户端状态丢失和同名不同值 TXT 记录的清理问题，仅删除本次创建的记录，保留预先存在的记录。
- 使用托管 zone 最长后缀匹配，支持多级域名、子 zone 和 IDN，取代末两段根域名猜测。
- 完整读取分页结果，精确过滤启用的默认线路 TXT 记录；API 失败不回退到猜测结果。
- 使用阿里云 DNS 公共端点和超时配置，关闭自动写入重试，隐藏 SDK 异常中的敏感请求信息。
- 增加可选 STS security_token 配置与 --dns-aliyun-next-ttl 参数。
- DNS 传播等待由 Certbot 统一执行，移除每条记录额外固定 10 秒等待。

升级时保持原插件名称、命令行凭证参数和 AccessKey 配置项。
自动发现托管域名新增 `alidns:DescribeDomains` 权限。
