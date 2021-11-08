import subprocess

from worf import __version__


def get_current_version():
    try:
        hash = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .strip()
            .decode()
        )
        return f"{__version__}@{hash}"
    except:  # pragma: no cover # noqa E722 Dont crash for any reason whatsoever
        return __version__
