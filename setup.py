#!/usr/bin/env python3

import setuptools
from pathlib import Path

package_name = 'vsrgtools'

exec(Path(f'{package_name}/_metadata.py').read_text(), meta := dict[str, str]())

readme = Path('README.md').read_text()
requirements = Path('requirements.txt').read_text()


setuptools.setup(
    name=package_name,
    version=meta['__version__'],
    author=meta['__author_name__'],
    author_email=meta['__author_email__'],
    maintainer=meta['__maintainer_name__'],
    maintainer_email=meta['__maintainer_email__'],
    description=meta['__doc__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    project_urls={
        'Source Code': 'https://github.com/Irrational-Encoding-Wizardry/vs-rgtools',
        'Documentation': 'https://vsrgtools.encode.moe/en/latest/',
        'Contact': 'https://discord.gg/qxTxVJGtst',
    },
    install_requires=requirements,
    python_requires='>=3.10',
    packages=[
        package_name, f'{package_name}.aka_expr'
    ],
    package_data={
        package_name: ['py.typed']
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
