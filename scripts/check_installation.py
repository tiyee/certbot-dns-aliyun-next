"""Verify the installed wheel outside the source tree in a disposable Certbot host."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from certbot_dns_aliyun_next.compat import metadata


def main() -> None:
    distribution = metadata.distribution("certbot-dns-aliyun-next")
    plugins = [
        p for p in metadata.entry_points(group="certbot.plugins") if p.name == "dns-aliyun-next"
    ]
    assert len(plugins) == 1, plugins
    from certbot.plugins.dns_common import DNSAuthenticator

    from certbot_dns_aliyun_next import __version__

    plugin = plugins[0].load()
    assert issubclass(plugin, DNSAuthenticator)
    assert __version__ == distribution.version
    # tox invokes this script from its temp directory, never the project root.
    import certbot_dns_aliyun_next

    package = Path(certbot_dns_aliyun_next.__file__).resolve()
    root = Path(__file__).resolve().parents[1]
    assert root / "certbot_dns_aliyun_next" not in package.parents, (
        f"Imported source tree instead of wheel: {package}"
    )
    print("Installed plugin:", distribution.version, "Host Certbot:", metadata.version("certbot"))
    with TemporaryDirectory(prefix="certbot-dns-aliyun-check-") as directory:
        cwd = Path(directory)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from certbot_dns_aliyun_next.compat import metadata; "
                "cli = next(p for p in metadata.distribution('certbot').entry_points "
                "if p.group == 'console_scripts' and p.name == 'certbot'); "
                "raise SystemExit(cli.load()())",
                "plugins",
                "--text",
                "--config-dir",
                str(cwd / "config"),
                "--work-dir",
                str(cwd / "work"),
                "--logs-dir",
                str(cwd / "logs"),
            ],
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True,
        )
        print(result.stdout)
        assert "dns-aliyun-next" in result.stdout, result.stderr


if __name__ == "__main__":
    main()
