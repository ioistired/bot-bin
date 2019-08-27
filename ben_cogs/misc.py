import collections
import contextlib
import datetime
import math
import os.path
import time
from typing import Awaitable, Sequence, T, Tuple, Union

import discord
from discord.ext import commands
from dateutil.relativedelta import relativedelta
try:
	from prettytable import PrettyTable
except ImportError:
	HAVE_PRETTYTABLE = False
else:
	HAVE_PRETTYTABLE = True

def codeblock(s, *, lang=''):
	return f'```{lang}\n{s}```'

def absolute_natural_timedelta(seconds: int, *, accuracy=2):
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

# plural, human_join, and natural_timedelta use code provided by Rapptz under the MIT License
# © 2015 Rapptz
# https://github.com/Rapptz/RoboDanny/blob/6fd16002e0cbd3ed68bf5a8db10d61658b0b9d51/cogs/utils/formats.py
# https://github.com/Rapptz/RoboDanny/blob/b8c427ad97372cb47f16397ff04a6b80e2494757/cogs/utils/time.py
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

def natural_timedelta(dt, *, source=None, accuracy=3, brief=False, ago=False):
	now = source or datetime.datetime.utcnow()
	# Microsecond free zone
	now = now.replace(microsecond=0)
	dt = dt.replace(microsecond=0)

	# This implementation uses relativedelta instead of the much more obvious
	# divmod approach with seconds because the seconds approach is not entirely
	# accurate once you go over 1 week in terms of accuracy since you have to
	# hardcode a month as 30 or 31 days.
	# A query like "11 months" can be interpreted as "!1 months and 6 days"
	if dt > now:
		delta = relativedelta(dt, now)
		suffix = ''
	else:
		delta = relativedelta(now, dt)
		suffix = ' ago' if ago else ''

	attrs = [
		('year', 'y'),
		('month', 'mo'),
		('day', 'd'),
		('hour', 'h'),
		('minute', 'm'),
		('second', 's'),
	]

	output = []
	for attr, brief_attr in attrs:
		elem = getattr(delta, attr + 's')
		if not elem:
			continue

		if attr == 'day':
			weeks = delta.weeks
			if weeks:
				elem -= weeks * 7
				if not brief:
					output.append(format(plural(weeks), 'week'))
				else:
					output.append(f'{weeks}w')

		if elem <= 0:
			continue

		if brief:
			output.append(f'{elem}{brief_attr}')
		else:
			output.append(format(plural(elem), attr))

	if accuracy is not None:
		output = output[:accuracy]

	if not output:
		return 'now'
	if not brief:
		return human_join(output, conj='and') + suffix
	return ' '.join(output) + suffix

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
		if not hasattr(bot, 'start_time'):
			bot.start_time = None

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
			self.bot.start_time = datetime.datetime.utcnow()

	@commands.command(aliases=['license'])
	async def copyright(self, context):
		"""Tells you about the copyright license for the bot"""
		await context.send(self.license_message)

	@commands.command(name='uptime')
	async def uptime_command(self, context):
		"""Shows you how long the bot has been online."""
		await context.send(self.uptime())

	def uptime(self, *, brief=False):
		if not hasattr(self.bot, 'start_time'):
			return 'Not up yet' if brief else "I'm not up yet."

		humanized = natural_timedelta(self.bot.start_time, accuracy=None, brief=brief)
		if brief:
			return humanized
		else:
			return f"I've been up for {humanized}."

	# maintain backwards compatibility
	natural_time = staticmethod(absolute_natural_timedelta)
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
