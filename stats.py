#!/usr/bin/env python3
# encoding: utf-8

import json
import logging
import sys
import traceback

import aiohttp
from discord.ext import commands

"""A simple stats cog, for use with several bot lists.
Make sure your bot.config['tokens']['stats'] has a key
which maps each domain name to either null or a token.
"""

logger = logging.getLogger('stats')


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
				logger.warning(f"{config_key} was not loaded! Please make sure it's configured correctly.")
			else:
				self.configured_apis.append(config_key)

		bot.add_listener(self.send, 'on_ready')

	def __unload(self):
		self.bot.loop.create_task(self.session.close())

	async def send(self):
		"""send guild counts to the API gateways."""

		for config_key in self.configured_apis:
			url = 'https://{}/api/bots/{}/stats'.format(config_key, self.bot.user.id)
			data = json.dumps({'server_count': self.guild_count})
			headers = {'Authorization': self.config[config_key], 'Content-Type': 'application/json'}

			async with self.session.post(url, data=data, headers=headers) as resp:
				message = config_key
				print('[STATS]', config_key, end=' ', file=sys.stderr)
				if resp.status // 100 == 2:  # 2xx codes are success
					# unholy mix of f-strings and %s because f-strings aren't async
					logger.info(f'{config_key} response: %s', await resp.text())
				else:
					logger.warning(f'{config_key} failed with status code {resp.status}')

	@property
	def guild_count(self):
		"""Return the guild count for the bot associated with this cog.
		Override this if your guild count needs manipulation."""
		return len(self.bot.guilds)

	@commands.command(name='send-stats', hidden=True)
	@commands.is_owner()
	async def send_command(self, context):
		await self.send()
		await context.message.add_reaction('\N{white heavy check mark}')

	async def on_guild_join(self, _):
		await self.send()

	on_guild_remove = on_guild_join

def setup(bot):
	bot.add_cog(Stats(bot))
