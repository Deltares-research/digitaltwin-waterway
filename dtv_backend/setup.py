#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

# install requirements.txt
requirements = ["Click>=7.0"]

setup_requirements = []

test_requirements = []

setup(
    author="Fedor Baart",
    author_email="fedor.baart@deltares.nl",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Digital Twin for Waterways backend server. Connected to OpenCLSim/OpenTNSim networks.",
    entry_points={
        "console_scripts": [
            "dtv_backend=dtv_backend.cli:main",
        ],
    },
    packages=find_packages(),
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="dtv_backend",
    name="dtv_backend",
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/deltares/digitaltwin-waterway",
    version="0.1.0",
    zip_safe=False,
)
