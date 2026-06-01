"""Setup configuration for pharma-cli."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

setup(
    name="pharma-cli",
    version="0.2.0",
    description="AI-agent-friendly statistical analysis CLI powered by R",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pharma CLI",
    url="https://github.com/pharma-cli/pharma-cli",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    package_data={
        "": ["skills/**/*", "r_scripts/*.R"],
    },
    include_package_data=True,
    install_requires=[
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "pharma-cli=cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
