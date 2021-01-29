from setuptools import setup, find_packages

setup(
    name="worf",
    version="0.1.0",
    description="Wade's Own Rest Framework: A more djangonic approach",
    long_description="",
    keywords="django, rest, framework",
    author="Wade Williams",
    author_email="wade@wadewilliams.com",
    url="https://github.com/flowcanon/worf",
    license="MIT",
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        "Django>=3.0.0",
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Environment :: Web Environment",
    ]
)
