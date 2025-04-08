#!/usr/bin/env python3
"""
Setup script for the RPLidarC1 package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rplidarc1",
    version="0.1.0",
    author="David Milad Saadatmandi",
    author_email="davidmilad@gmail.com",
    description="A Python library for interfacing with the RPLidar C1 360-degree laser scanner",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dsaadatmandi/rplidarc1",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Robotics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pyserial>=3.5",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
        ],
    },
)
