import semver
import sys

release = len(sys.argv) > 2 and sys.argv[2] or "patch"
version = semver.VersionInfo.parse(sys.argv[1].lstrip("v"))

print(getattr(version, f"bump_{release}")())
