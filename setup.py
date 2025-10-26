"""
Setup script for the taxcalc package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="taxcalc",
    version="1.0.0",
    author="Tax Calculator",
    description="Comprehensive Federal and California Tax Calculator for Tax Year 2024/2025",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies required - uses only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "jupyter>=1.0",
            "notebook>=6.0",
        ],
    },
)
