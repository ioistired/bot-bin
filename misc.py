#!/usr/bin/env python3
# encoding: utf-8

from datetime import datetime
import time

import discord
from discord.ext.commands import command
import humanize


class Misc:
	"""Miscellaneous commands that don't belong in any other category"""

	UNKNOWN_CUTOFF = datetime.utcfromtimestamp(discord.utils.DISCORD_EPOCH // 1000)

	def __init__(self, bot):
		self.bot = bot

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
			if user.game:
				embed.add_field(name='Playing', value=user.game)
		await context.send(embed=embed)

	@classmethod
	def format_time(cls, time):
		if time is None or time < cls.UNKNOWN_CUTOFF:
			return 'Unknown'
		return '{} ({} UTC)'.format(
			humanize.naturaltime(time + (datetime.now() - datetime.utcnow())), time)

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
