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
    name="bungo-map",
    version="2.0.0",
    description="文豪ゆかり地図システム - 作家・作品・舞台地名の3階層データ管理システム",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    author="Masa",
    author_email="masa@example.com",
    url="https://github.com/masa/bungo-map",
    packages=find_packages(),
    package_data={
        'bungo_map': ['**/*.sql', '**/*.json', '**/*.yaml'],
    },
    include_package_data=True,
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=0.991',
            'isort>=5.10.0',
            'coverage>=6.0.0',
            'pytest-cov>=3.0.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'bungo=bungo_map.cli.main:main',
            'bungo-server=bungo_map.api.server:main',
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