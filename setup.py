#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v2.0 - セットアップファイル
"""

from setuptools import setup, find_packages

# requirements.txtから依存関係を読み込み
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    requirements = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('==='):
            requirements.append(line)
    
    return requirements

setup(
    name="bungo_map",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "beautifulsoup4",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "aozora-scraper=bungo_map.cli.commands:cli",
        ],
    },
    python_requires='>=3.10',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="nlp, japanese, literature, geography, map, bungo",
    project_urls={
        "Bug Reports": "https://github.com/masa/bungo-map/issues",
        "Source": "https://github.com/masa/bungo-map",
        "Documentation": "https://bungo-map.readthedocs.io",
    },
) 