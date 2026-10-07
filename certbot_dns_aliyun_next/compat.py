"""Keep host compatibility in one place, using Certbot's public APIs.

DNSAuthenticator already handles the annotated-challenge API changes between
Certbot 3 and 5. Inherit its public lifecycle instead of copying it or applying
the obsolete zope.interface decorators (removed from Certbot's dependencies).
"""

import sys

from certbot.plugins.dns_common import DNSAuthenticator

if sys.version_info < (3, 10):
    # Python 3.9's stdlib entry_points() does not support the group keyword.
    import importlib_metadata as metadata
else:
    from importlib import metadata


def certbot_major_version() -> int:
    """Return the actual installed host version, not a resolver assumption."""
    return int(metadata.version("certbot").split(".", 1)[0])


__all__ = ["DNSAuthenticator", "certbot_major_version", "metadata"]
