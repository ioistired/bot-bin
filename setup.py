#!/usr/bin/env python3

import re
from setuptools import setup

with open('bot_bin/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
	name='bot-bin',
	author='lambda#0987',
	description='Shared cogs and utilities for use in Discord bots',
	url='https://github.com/bmintz/bot-bin',
	download_url='https://github.com/bot-bin/cogs/archive/v{}.tar.gz'.format(version),
	version=version,
	packages=['bot_bin'],
	install_requires=[
		'discord.py>=1.2.3,<2.0.0',
		'humanize',
		'python-dateutil',
		'objgraph'],
	extras_require={
		'sql': [
			'asyncpg',
			'prettytable']},
	python_requires='>=3.6.0',
	license='BlueOak-1.0.0',
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
