#!/usr/bin/env python3.6
# encoding: utf-8

import re
from setuptools import setup


with open('requirements.txt') as f:
	requirements = f.read().splitlines()


with open('ben_cogs/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)


setup(
	name='ben_cogs',
	author='bmintz',
	author_email='bmintz@protonmail.com',
	url='https://github.com/bmintz/cogs',
	version=version,
	packages=['ben_cogs'],
	install_requires=requirements,
	python_requires='>=3.6.0',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Framework :: AsyncIO',
		'License :: OSI Approved :: MIT License',
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3.6',
		'Topic :: Internet',
		'Topic :: Utilities'])
