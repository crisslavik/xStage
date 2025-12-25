#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="xstage",
    version="0.1.0",
    author="NOX VFX",
    author_email="pipeline@nox-vfx.com",  # Update this
    description="Professional USD viewer with pipeline integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xstage-pipeline/xstage",
    project_urls={
        "Bug Tracker": "https://github.com/xstage-pipeline/xstage/issues",
        "Documentation": "https://xstage-pipeline.github.io",
        "Source Code": "https://github.com/xstage-pipeline/xstage",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "xstage=xstage.core.viewer:main",
        ],
    },
)