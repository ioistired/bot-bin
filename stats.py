#!/usr/bin/env python3
# encoding: utf-8

import json
import sys
import traceback

import aiohttp
from discord.ext import commands

"""A simple stats cog, for use with several bot lists.
Make sure your bot.config['tokens']['stats'] has a key
which maps each domain name to either null or a token.
"""


class Stats:
	# credit to @Tom™#7887 (ID 248294452307689473) on the Discord Bots List guild
	# for much of this
	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession(loop=bot.loop)
		self.config = self.bot.config['tokens']['stats']

		self.configured_apis = []
		for config_key in ('bots.discord.pw', 'discordbots.org'):
			if self.config[config_key] is None:
				print(config_key, "was not loaded! Please make sure it's configured correctly.")
			else:
				self.configured_apis.append(config_key)

	def __unload(self):
		self.bot.loop.create_task(self.session.close())

	async def send(self):
		"""send guild counts to the API gateways."""

		for config_key in self.configured_apis:
			url = 'https://{}/api/bots/{}/stats'.format(config_key, self.bot.user.id)
			data = json.dumps({'server_count': self.guild_count})
			headers = {'Authorization': self.config[config_key], 'Content-Type': 'application/json'}

			async with self.session.post(url, data=data, headers=headers) as resp:
				print('[STATS]', config_key, end=' ', file=sys.stderr)
				if resp.status // 100 == 2:  # 2xx codes are success
					print('response:', await resp.text(), file=sys.stderr)
				else:
					print('failed with status code', resp.status, file=sys.stderr)

	@commands.command(name='stats', hidden=True)
	@commands.is_owner()
	async def send_command(self, context):
		await self.send()
		await context.message.add_reaction('\N{white heavy check mark}')

	@property
	def guild_count(self):
		count = len(self.bot.guilds)
		if self.bot.user.id == 405953712113057794:  # Emoji Connoisseur
			count -= 100
		return count

	async def on_ready(self):
		await self.send()

	async def on_guild_join(self, server):
		await self.send()

	async def on_guild_remove(self, server):
		await self.send()


def setup(bot):
	bot.add_cog(Stats(bot))
