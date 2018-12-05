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


class BenCogsStats:
	# credit to @Tom™#7887 (ID 248294452307689473) on the Discord Bots List guild
	# for much of this

	API_URLS = {
		'bots.discord.pw':    'https://bots.discord.pw/api/bots/{}/stats',
		'discordbots.org':    'https://discordbots.org/api/bots/{}/stats',
		'botsfordiscord.com': 'https://botsfordiscord.com/api/v1/bots/{}',
	}

	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession(loop=bot.loop)
		self.config = self.bot.config['tokens']['stats']

		self.configured_apis = []
		for config_key in self.API_URLS:
			if self.config.get(config_key) is None:
				logger.warning(f"{config_key} was not loaded! Please make sure it's configured correctly.")
			else:
				self.configured_apis.append(config_key)

		self.bot.add_listener(self.send, 'on_ready')
		for guild_change_event in 'on_guild_join', 'on_guild_remove':
			self.bot.add_listener(self.on_guild_change, guild_change_event)

	def __unload(self):
		self.bot.loop.create_task(self.session.close())

	async def send(self):
		"""send guild counts to the API gateways."""

		await self.notify_owner()

		for config_key in self.configured_apis:
			url = self.API_URLS[config_key].format(self.bot.user.id)
			data = json.dumps({'server_count': await self.guild_count()})
			headers = {'Authorization': self.config[config_key], 'Content-Type': 'application/json'}

			async with self.session.post(url, data=data, headers=headers) as resp:
				if resp.status // 100 == 2:  # 2xx codes are success
					logger.info('%s response: %s', config_key, await resp.text())
				else:
					logger.warning('%s failed with status code %s', config_key, resp.status)

	async def notify_owner(self):
		"""Notify the owner of the bot if the guild count is large."""
		guild_count = await self.guild_count()
		# check if it's a power of two
		# x = 0b100 (4)
		# x-1 = 0b011
		#   0b100
		# & 0b011
		# ───────
		#   0b000
		# ∵ x & x - 1 == 0
		# ∴ x is a power of two
		# also typically a bot is in a few guilds for testing (test server + DBL + discord.pw),
		# so ignore 4 guilds
		if guild_count > 4 and guild_count & (guild_count - 1) == 0:
			await self._get_owner().send(f'Guild count ({guild_count}) is a power of 2!')

	def _get_owner(self):
		"""Get the bot's owner as a discord.py User object."""
		owner_id = int(self.bot.config.get('send_logs_to', self.bot.owner_id))
		return self.bot.get_user(owner_id)

	async def guild_count(self):
		"""Return the guild count for the bot associated with this cog.
		Override this if your guild count needs manipulation."""
		return len(self.bot.guilds)

	@commands.command(name='send-stats', hidden=True)
	@commands.is_owner()
	async def send_command(self, context):
		await self.send()
		await context.message.add_reaction('\N{white heavy check mark}')

	async def on_guild_change(self, _):
		await self.send()

# maintain alias for backwards compatibility of subclasses
class Stats(BenCogsStats):
	pass

def setup(bot):
	bot.add_cog(BenCogsStats(bot))
