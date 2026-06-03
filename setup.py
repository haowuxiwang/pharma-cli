"""Setup configuration for stats-cli."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

setup(
    name="stats-cli",
    version="0.4.0",
    description="AI-friendly statistical analysis CLI for manufacturing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stats CLI",
    url="https://github.com/haowuxiwang/stats-cli",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    package_data={
        "": ["skills/**/*", "r_scripts/*.R", "templates/*.html"],
    },
    include_package_data=True,
    install_requires=[
        "click>=8.0",
        "pandas",
        "numpy",
        "plotly",
        "jinja2",
    ],
    entry_points={
        "console_scripts": [
            "stats-cli=cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
