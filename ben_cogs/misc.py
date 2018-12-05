#!/usr/bin/env python3
# encoding: utf-8

import contextlib
from datetime import datetime
import os.path
import time

import discord
from discord.ext.commands import command
import inflect

inflect = inflect.engine()

class BenCogsMisc:
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

	async def on_ready(self):
		if not hasattr(self.bot, 'start_time'):
			self.bot.start_time = datetime.utcnow()

	@command(aliases=['license'])
	async def copyright(self, context):
		"""Tells you about the copyright license for the bot"""
		await context.send(self.license_message)

	@command(name='uptime')
	async def uptime_command(self, context):
		"""Shows you how long the bot has been online."""
		await context.send(self.uptime())

	def uptime(self, *, brief=False):
		try:
			seconds = (datetime.utcnow() - self.bot.start_time).total_seconds()
		except AttributeError:
			if brief:
				return 'Not up yet'
			return "I'm not up yet."

		if seconds < 1:
			natural_time = '0 seconds'
		else:
			natural_time = self.natural_time(round(seconds))

		if brief:
			return natural_time
		else:
			return f"I've been up for {natural_time}."

	@classmethod
	def natural_time(cls, seconds: int):
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

	@command()
	async def ping(self, context):
		"""Shows the bots latency to Discord's servers"""
		# trigger typing in DMs to minimize disruption
		# as sometimes a low enough ping means that the reply message
		# does not cancel the typing
		# also apparently we can always trigger typing in DMs
		# even if they blocked us
		rtt = await self.timeit(context.author.trigger_typing())
		await context.send(f'🏓 Pong! │{rtt}ms')

	@command(hidden=True)
	async def pong(self, context):
		reply = await context.send('Ping')
		if context.message.created_at < reply.created_at:
			# the messages appeared in the correct order
			await reply.delete()
		# due to loose snowflake ordering, we time travelled
		# so leave the reply message alone

	async def timeit(self, coro):
		"""return how long it takes to await coro, in milliseconds"""
		t0 = time.perf_counter()
		await coro
		t1 = time.perf_counter()
		return round((t1-t0)*1000)

# maintain alias for backwards compatibility of subclasses
class Misc(BenCogsMisc):
	pass

def setup(bot):
	bot.add_cog(BenCogsMisc(bot))
