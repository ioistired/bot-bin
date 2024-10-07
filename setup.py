#!/usr/bin/env python3

import re
from setuptools import setup

with open('bot_bin/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

with open('README.md') as f:
	long_description = f.read()

setup(
	name='bot-bin',
	author='@lambda.dance',
	description='Shared cogs and utilities for use in Discord bots',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/ioistired/bot-bin',
	version=version,
	packages=['bot_bin'],
	install_requires=[
		'discord.py>=2.3.2,<3.0.0',
		'humanize',
		'python-dateutil',
		'objgraph',
	],
	extras_require={
		'sql': [
			'aiocontextvars>=0.2.2',
			'asyncpg',
			'prettytable',
		],
		'uvloop': [
			'uvloop>=0.14.0,<1.0.0',
		],
	},
	python_requires='>=3.6.0',
	license='BlueOak-1.0.0',
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Framework :: AsyncIO',
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3.11',
		'Programming Language :: Python :: 3.12',
		'Topic :: Internet',
		'Topic :: Utilities',
		'Topic :: Communications :: Chat',
	],
)
