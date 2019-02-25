#!/usr/bin/env python3
# encoding: utf-8

import contextlib
import math
import os.path
import time

import discord
from discord.ext import commands
import inflect

inflect = inflect.engine()

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
			with contextlib.suppress(AttributeError):
				del type(self).copyright
			return

		with open(self.bot.config['copyright_license_file']) as f:
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

		natural_time = self.natural_time(math.floor(seconds))

		if brief:
			return natural_time
		else:
			return f"I've been up for {natural_time}."

	@classmethod
	def natural_time(cls, seconds: int):
		if not seconds:
			return '0 seconds'

		split = cls.split_seconds(round(seconds))
		words = zip(('week', 'day', 'hour', 'minute', 'second'), split)

		return inflect.join([cls.pluralize(word, value) for word, value in words if value])

	@staticmethod
	def pluralize(word, value):
		return f'{value} {inflect.plural_noun(word, value)}'

	@staticmethod
	def split_seconds(seconds: int):
		minutes, seconds = divmod(seconds, 60)
		hours, minutes = divmod(minutes, 60)
		days, hours = divmod(hours, 24)
		weeks, days = divmod(days, 7)
		# we stop at weeks because that is the largest unit that we can divide exactly
		# ie a week is always 7 days, but a month is not always 4 weeks.
		return weeks, days, hours, minutes, seconds

	@commands.command()
	async def ping(self, context):
		"""Shows the bots latency to Discord's servers"""
		# trigger typing in DMs to minimize disruption
		# as sometimes a low enough ping means that the reply message
		# does not cancel the typing
		# also apparently we can always trigger typing in DMs
		# even if they blocked us
		rtt, _ = await self.timeit(context.author.trigger_typing())
		await context.send(f'🏓 Pong! │{rtt}ms')

	@commands.command(hidden=True)
	async def pong(self, context):
		reply = await context.send('Ping')
		if context.message.created_at < reply.created_at:
			# the messages appeared in the correct order
			await reply.delete()
		# due to loose snowflake ordering, we time travelled
		# so leave the reply message alone

	@staticmethod
	async def timeit(coro, _timer=time.perf_counter):
		"""return how long it takes to await coro, in milliseconds"""
		t0 = _timer()
		result = await coro
		t1 = _timer()
		return round((t1 - t0) * 1000), result

# maintain alias for backwards compatibility of subclasses
class Misc(BenCogsMisc):
	pass

def setup(bot):
	bot.add_cog(BenCogsMisc(bot))
