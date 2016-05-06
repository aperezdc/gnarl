#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from setuptools import setup, find_packages
from setuptools import find_packages
from codecs import open
from os import path
import sys


def file_contents(*relpath):
    with open(path.join(path.dirname(__file__), *relpath), "rU",
            encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    setup(
        name="gnarl",
        version="0.1.0a4",
        description=("Lightweight module to define serializable, "
                     "schema-validated classes"),
        long_description=file_contents("README.rst"),
        author="Adrián Pérez de Castro",
        author_email="adrian@perezdecastro.org",
        url="https://github.com/aperezdc/gnarl",
        py_modules=["gnarl"],
        install_requires=[
            "delorean>=0.5.0",
        ],
        extras_require={
            "hipack": ["hipack>=12"],
        },
        license="MIT",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python",
            "Operating System :: OS Independent"
        ],
        test_suite="test",
        tests_require=["hipack>=12"],
    )
