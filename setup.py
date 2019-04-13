import os
import re
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

install_requires = [
    "html2text>=2018.1.9",
    "requests>=2.21.0",
    "Whoosh>=2.7.4",
    "xmltodict>=0.12.0",
    "peewee>=3.9.3",
]


def read(*parts):
    with open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="jirafts",
    url="https://github.com/reclosedev/jirafts/",
    version=find_version("jirafts", "__init__.py"),
    author="Roman Haritonov",
    description="Tool for searching in local copy of JIRA issues",
    author_email="reclosedev@gmail.com",
    license="MIT",
    packages=find_packages("."),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "console_scripts":
            [
                "jirafts = jirafts.cli:main",
            ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
)
