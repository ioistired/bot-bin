#!/usr/bin/env python3
# encoding: utf-8

import collections
import contextlib
import math
import os.path
import time
from typing import Awaitable, Sequence, T, Tuple, Union

import discord
from discord.ext import commands
try:
	from prettytable import PrettyTable
except ImportError:
	HAVE_PRETTYTABLE = False
else:
	HAVE_PRETTYTABLE = True

def codeblock(s, *, lang=''):
	return f'```{lang}\n{s}```'

def natural_time(seconds: int, *, accuracy=2):
	if not seconds:
		return '0 seconds'

	split = split_seconds(round(seconds))
	words = zip(('day', 'hour', 'minute', 'second'), split)
	pluralized = [format(plural(value), word) for word, value in words if value][:accuracy]
	return human_join(pluralized)

def split_seconds(seconds: int):
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	# no more perfectly divisible units after here (except weeks which we don't want)
	return days, hours, minutes, seconds

# pliral and human_join use code provided by Rapptz under the MIT License
# © 2015 Rapptz
# https://github.com/Rapptz/RoboDanny/blob/6fd16002e0cbd3ed68bf5a8db10d61658b0b9d51/cogs/utils/formats.py

class plural:
    def __init__(self, value):
        self.value = value
    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'
        if abs(v) != 1:
            return f'{v} {plural}'
        return f'{v} {singular}'

def human_join(seq, sep=', ', conj='and'):
    size = len(seq)
    if size == 0:
        return ''

    if size == 1:
        return seq[0]

    if size == 2:
        return f'{seq[0]} {conj} {seq[1]}'

    return sep.join(seq[:-1]) + f' {conj} {seq[-1]}'

async def timeit(coro: Awaitable[T], _timer=time.perf_counter) -> Tuple[float, T]:
	"""return how long it takes to await coro, in seconds, and its result"""
	t0 = _timer()
	result = await coro
	t1 = _timer()
	return t1 - t0, result

if HAVE_PRETTYTABLE:
	class PrettyTable(PrettyTable):
		"""an extension of PrettyTable that works with asyncpg's Records and looks better"""
		def __init__(self, rows: Sequence[Union['asyncpg.Record', collections.OrderedDict]], **options):
			defaults = dict(
				# super()'s default is ASCII | - +, which don't join seamlessly and look p bad
				vertical_char='│',
				horizontal_char='─',
				junction_char='┼')
			for option, default in defaults.items():
				options.setdefault(option, default)

			if rows:
				super().__init__(rows[0].keys(), **options)
			else:
				super().__init__()
			# PrettyTable's constructor does not set this property for some reason
			self.align = options.get('align', 'l')	# left align

			for row in rows:
				self.add_row(row)

class BenCogsMisc(commands.Cog):
	"""Miscellaneous commands that don't belong in any other category"""

	def __init__(self, bot):
		self.bot = bot
		self._init_license()

	def _init_license(self):
		try:
			filename = self.bot.config.get('copyright_license_file')
		except AttributeError:
			return

		if not filename or not os.path.isfile(filename):
			return

		with open(filename) as f:
			self.license_message = f.read()

	@commands.Cog.listener()
	async def on_ready(self):
		if not hasattr(self.bot, 'start_time'):
			self.bot.start_time = time.monotonic()

	@commands.command(aliases=['license'])
	async def copyright(self, context):
		"""Tells you about the copyright license for the bot"""
		await context.send(self.license_message)

	@commands.command(name='uptime')
	async def uptime_command(self, context):
		"""Shows you how long the bot has been online."""
		await context.send(self.uptime())

	def uptime(self, *, brief=False):
		try:
			seconds = time.monotonic() - self.bot.start_time
		except AttributeError:
			if brief:
				return 'Not up yet'
			return "I'm not up yet."

		humanized = natural_time(math.floor(seconds))

		if brief:
			return humanized
		else:
			return f"I've been up for {humanized}."

	# maintain backwards compatibility
	natural_time = staticmethod(natural_time)
	split_seconds = staticmethod(split_seconds)

	@commands.command()
	async def ping(self, context):
		"""Shows the bots latency to Discord's servers"""
		latency = round(self.bot.latency * 1000, 2)
		await context.send(f'🏓 Pong!│Average websocket latency: {latency}ms')

	@commands.command(hidden=True)
	async def pong(self, context):
		reply = await context.send('Ping')
		if context.message.created_at < reply.created_at:
			# the messages appeared in the correct order
			await reply.delete()
		# due to loose snowflake ordering, we time travelled
		# so leave the reply message alone

	timeit = staticmethod(timeit)

# maintain alias for backwards compatibility of subclasses
class Misc(BenCogsMisc):
	pass

def setup(bot):
	cog = BenCogsMisc(bot)
	bot.add_cog(cog)
	if not hasattr(cog, 'license_message'):
		bot.remove_command('copyright')
