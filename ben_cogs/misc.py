#!/usr/bin/env python3
# encoding: utf-8

from datetime import datetime
import time

import aiofiles
import discord
from discord.ext.commands import command
import humanize


class Misc:
	"""Miscellaneous commands that don't belong in any other category"""

	# I think DISCORD_EPOCH is in milliseconds, but we want seconds.
	UNKNOWN_CUTOFF = datetime.utcfromtimestamp(discord.utils.DISCORD_EPOCH // 1000)

	def __init__(self, bot):
		self.bot = bot

	async def on_ready(self):
		if not hasattr(self.bot, 'start_time'):
			self.bot.start_time = datetime.utcnow()

	@command(aliases=['license'])
	async def copyright(self, context):
		"""Tells you about the copyright license for the bot"""
		async with aiofiles.open(self.bot.config['copyright_license_file']) as f:
			await context.send(await f.read())

	@command()
	async def userinfo(self, context, *, user: discord.User = None):
		# https://github.com/khazhyk/dango.py/blob/e613d4457045c131dc212686e74c325418fd1399/plugins/info.py#L208-L243
		"""Show information about a user. Creds to @spoopy🍡#0567"""
		if user is None:
			user = context.message.author

		embed = discord.Embed()
		embed.add_field(name='User', value=str(user))
		if isinstance(user, discord.Member) and user.nick:
			embed.add_field(name='Nickname', value=user.nick)
		embed.add_field(name='ID', value=user.id)
		embed.add_field(name='Created', value=self.format_time(user.created_at))
		if isinstance(user, discord.Member):
			embed.add_field(name='Joined', value=self.format_time(user.joined_at))
			embed.add_field(name='Roles', value=', '.join(
				r.name for r in sorted(user.roles, key=lambda r: r.position, reverse=True)))
			if user.activity is not None:
				activity_type, activity_name = self.format_activity(user.activity)
				embed.add_field(name=activity_type, value=activity_name)
		await context.send(embed=embed)

	@staticmethod
	def format_activity(activity: discord.Activity):
		"""return a two tuple of the member's activity type and the activity name
		if joined with a space, it will look identical to what's displayed in the client.
		"""
		activity = member.activity
		if activity is None:
			return
		# e.g. ('Playing', 'Fortnite')
		return activity.type.name.title(), activity.name

	@command()
	async def uptime(self, context):
		"""Shows you how long the bot has been online."""
		natural_time = humanize.naturaltime(datetime.utcnow() - self.bot.start_time).replace(' ago', '')
		if natural_time == 'now':
			natural_time = '0 seconds'
		await context.send("I've been up for %s." % natural_time)

	@classmethod
	def format_time(cls, time):
		if time is None or time < cls.UNKNOWN_CUTOFF:
			return 'Unknown'
		natural_time = humanize.naturaltime(time + (datetime.now() - datetime.utcnow()))
		return '%s (%s UTC)' % (natural_time, time)

	@command()
	async def ping(self, context):
		"""Shows the bots latency to Discord's servers"""
		pong = '🏓 Pong! '
		start = time.time()
		message = await context.send(pong)
		rtt = (time.time() - start) * 1000
		# 10 µs is plenty precise
		await message.edit(content=pong + '│{:.2f}ms'.format(rtt))


def setup(bot):
	bot.add_cog(Misc(bot))
