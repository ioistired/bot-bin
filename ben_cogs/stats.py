#!/usr/bin/env python3
# encoding: utf-8

from collections import Counter
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

		self.guild_counts = Counter()
		self._update_counts()
		self._load_configured_apis()

		self.bot.add_listener(self.send, 'on_ready')
		for guild_change_event in 'on_guild_join', 'on_guild_remove':
			self.bot.add_listener(self.on_guild_change, guild_change_event)

	def __unload(self):
		self.bot.loop.create_task(self.session.close())

	def _update_counts(self):
		for guild in self.bot.guilds:
			self.guild_counts.update(guild.shard_id)

	def _load_configured_apis(self):
		self.configured_apis = []
		for config_key in ('bots.discord.pw', 'discordbots.org'):
			if self.config[config_key] is None:
				logger.warning(f"{config_key} was not loaded! Please make sure it's configured correctly.")
			else:
				self.configured_apis.append(config_key)

	async def send(self):
		"""send guild counts to the API gateways."""

		await self._notify_owner()

		for config_key in self.configured_apis:
			await self._post(config_key)

	async def _post(self, config_key: str, shard=None):
		url = 'https://{}/api/bots/{}/stats'.format(config_key, self.bot.user.id)
		data = await self._get_data(shard)
		headers = {'Authorization': self.config[config_key], 'Content-Type': 'application/json'}

		async with self.session.post(url, data=data, headers=headers) as resp:
			if resp.status // 100 == 2:  # 2xx codes are success
				logger.info('%s response: %s', config_key, await resp.text())
			else:
				logger.warning('%s failed with status code %s', config_key, resp.status)

	async def _get_data(self, shard=None):
		data = {'server_count': await self.guild_count(shard)}
		if shard is not None:
			data['shard_id'] = shard
		return json.dumps(data)

	async def _notify_owner(self):
		"""Notify the owner of the bot if the guild count is large."""
		guild_count = await self.guild_count()
		# check if it's a power of two, which is cause for celebration/concern
		# also typically a bot is in a few guilds for testing (test server + DBL + discord.pw),
		# so ignore 4 guilds
		if guild_count > 4 and self._power_of_two(guild_count):
			await self._get_owner().send(f'Guild count ({guild_count}) is a power of 2!')

	@staticmethod
	def _power_of_two(n):
		return n & (n - 1) == 0

	def _get_owner(self):
		"""Get the bot's owner as a discord.py User object."""
		owner_id = int(self.bot.config.get('send_logs_to', self.bot.owner_id))
		return self.bot.get_user(owner_id)

	async def guild_count(self, shard=None):
		"""Return the guild count for the bot associated with this cog.
		Override this if your guild count needs manipulation."""
		return len(self.bot.guilds)

	@commands.command(name='send-stats', hidden=True)
	@commands.is_owner()
	async def send_command(self, context):
		await self.send()
		await context.message.add_reaction('\N{white heavy check mark}')

	async def on_guild_change(self, guild):
		await self.send(guild.shard_id)


def setup(bot):
	bot.add_cog(Stats(bot))
