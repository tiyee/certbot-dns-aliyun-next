from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="certbot-dns-aliyun-next",
    version="1.0.0",
    author="tiyee",
    author_email="tiyee@live.com",
    description="阿里云DNS插件，用于Certbot的DNS-01验证",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="certbot-dns certbot-plugin certbot-dns-plugin certbot-dns-authenticator certbot-aliyun",
    url="https://github.com/tiyee/certbot-dns-aliyun-next",
    project_urls={
        "Homepage": "https://github.com/tiyee/certbot-dns-aliyun-next"
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        'Operating System :: POSIX',
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "certbot.plugins": [
            "dns-aliyun-next = certbot_dns_aliyun_next.dns_aliyun_next:Authenticator",
        ],
    },
    include_package_data=True,
)
