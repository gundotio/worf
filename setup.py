import os

from setuptools import setup, find_packages


def read(rel_path):
    # type: (str) -> str
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path):
    # type: (str) -> str
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


setup(
    name="worf",
    version=get_version("worf/__init__.py"),
    url="https://github.com/gundotio/worf",
    description="Wade's own REST Framework: A more Djangonic approach to REST APIs",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author_email="wade@wadewilliams.com",
    author="Wade Williams",
    keywords="django, rest, framework, api",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    include_package_data=True,
    install_requires=[
        "Django>=3.0.0,<4.2",
        "dj-url-filter>=0.4.2",
        "marshmallow>=3.18.0",
    ],
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    zip_safe=False,
)
