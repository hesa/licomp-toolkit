# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import setuptools
from licomp_toolkit.config import licomp_toolkit_version
from licomp_toolkit.config import description
from licomp_toolkit.config import module_name


requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

requirements_dev = []
with open('requirements-dev.txt') as f:
    requirements_dev = f.read().splitlines()

setuptools.setup(
    name='licomp_toolkit',
    version=licomp_toolkit_version,
    author="Henrik Sanklef",
    author_email="hesa@sandklef.com",
    description=description.replace('\n', ' '),
    long_description=description,
    long_description_content_type="text/markdown",
    license_files=('LICENSES/GPL-3.0-or-later.txt',),
    url="https://github.com/hesa/licomp-toolkit",
    packages=['licomp_toolkit'],
    entry_points={
        "console_scripts": [
            "licomp-toolkit = licomp_toolkit.__main__:main",
        ],
    },
    package_data={
        f'{module_name}': ['data/*.json'],
    },
    install_requires=requirements,
    extras_require={
        'dev': requirements_dev,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires='>=3.6',
)
