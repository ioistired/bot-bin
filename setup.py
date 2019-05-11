#!/usr/bin/env python3
# encoding: utf-8

import re
from setuptools import setup

with open('ben_cogs/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
	name='ben_cogs',
	author='bmintz',
	author_email='bmintz@protonmail.com',
	description='Shared cogs for use in Discord bots',
	url='https://github.com/bmintz/cogs',
	download_url='https://github.com/bmintz/cogs/archive/{}.tar.gz'.format(version),
	version=version,
	packages=['ben_cogs'],
	install_requires=[
		'discord.py>=1.1.0,<2.0.0',
		'humanize',
		'inflect',
		'jishaku>=1.6.1,<2.0.0',
		'objgraph',
		'psutil'],
	python_requires='>=3.6.0',
	license='MIT',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Framework :: AsyncIO',
		'License :: OSI Approved :: MIT License',
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Topic :: Internet',
		'Topic :: Utilities'])
