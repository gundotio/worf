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


long_description = read("README.md")

setup(
    author_email="wade@wadewilliams.com",
    author="Wade Williams",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    description="Worf (Wade's Own Rest Framework): A more djangonic approach",
    install_requires=[
        "Django>=3.0.0,<3.3",
        "django-url-filter>=0.3.15",
    ],
    include_package_data=True,
    keywords="django, rest, framework, api",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="worf",
    packages=find_packages(),
    python_requires=">=3.7",
    url="https://github.com/gundotio/worf",
    version=get_version("worf/__init__.py"),
    zip_safe=False,
)
