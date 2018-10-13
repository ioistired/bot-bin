#!/usr/bin/env python3
# encoding: utf-8

from datetime import datetime
import os.path
import time

import discord
from discord.ext.commands import command
import humanize

class Misc:
	"""Miscellaneous commands that don't belong in any other category"""

	# I think DISCORD_EPOCH is in milliseconds, but we want seconds.
	UNKNOWN_CUTOFF = datetime.utcfromtimestamp(discord.utils.DISCORD_EPOCH // 1000)

	def __init__(self, bot):
		self.bot = bot

		filename = self.bot.config.get('copyright_license_file')
		if not filename or not os.path.isfile(filename):
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
		natural_time = humanize.naturaldelta(datetime.utcnow() - self.bot.start_time)
		if natural_time == 'now':
			natural_time = '0 seconds'

		if brief:
			return natural_time
		else:
			return f"I've been up for {natural_time}."

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

def setup(bot):
	bot.add_cog(Misc(bot))
