import asyncio
import json
import logging
import sys
import traceback
import urllib
from typing import Dict

import aiohttp
from discord.ext import commands

logger = logging.getLogger(__name__)

class BotBinStats(commands.Cog):
	"""A simple stats cog for use with several bot lists.
	Make sure your bot.config['tokens']['stats'] has a key
	which maps each configured domain name to a token.
	"""

	API_FORMATS = {
		urllib.parse.urlparse(url).netloc: url
		for url in (
			'https://discord.bots.gg/api/v1/bots/{}/stats',
			'https://discordbots.org/api/bots/{}/stats',
			'https://botsfordiscord.com/api/bot/{}',
			'https://lbots.org/api/v1/bots/{}/stats',
			'https://discord.boats/api/v2/bot/{}',
		)
	}

	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession(loop=self.bot.loop)
		self.config = self.bot.config['tokens']['stats']

		self.configured_apis = [
			config_key
			for config_key in self.API_FORMATS
			if self.config.get(config_key) is not None
		]

	def cog_unload(self):
		self.bot.loop.create_task(self.session.close())

	@commands.Cog.listener(name='on_ready')
	async def send(self) -> Dict[str, bool]:
		"""send guild counts to the API gateways. return a dict mapping config keys to HTTP response status codes."""
		async def post(config_key):
			url = self.API_FORMATS[config_key].format(self.bot.user.id)
			data = json.dumps({'server_count': await self.guild_count()})
			headers = {'Authorization': self.config[config_key], 'Content-Type': 'application/json'}

			async with self.session.post(url, data=data, headers=headers) as resp:
				if resp.status in range(200, 300):
					logger.info('%s response: %s', config_key, await resp.text())
				else:
					logger.warning('%s failed with status code %s', config_key, resp.status)
					logger.warning('response data: %s', await resp.text())

				return config_key, resp.status

		return dict(await asyncio.gather(*(post(config_key) for config_key in self.configured_apis)))

	async def notify_owners(self):
		"""Notify the owner(s) of the bot if the guild count is significant."""
		guild_count = await self.guild_count()
		# check if it's a power of two
		# also typically a bot is in a few guilds for testing (test server + DBL + discord.pw),
		# so ignore 4 guilds
		if guild_count <= 4 or guild_count & (guild_count - 1) != 0:
			return

		if self.bot.owner_id:
			owners = [self.bot.get_user(self.bot.owner_id)]
		elif self.bot.owner_ids:
			owners = map(self.bot.get_user, self.bot.owner_ids)

		async def send(user):
			await user.send(f'Guild count ({guild_count}) is a power of 2!')
		await asyncio.gather(*map(send, owners))

	async def guild_count(self):
		"""Return the guild count for the bot associated with this cog.
		Override this if your guild count needs manipulation.
		"""
		return len(self.bot.guilds)

	@commands.command(name='send-stats', hidden=True)
	@commands.is_owner()
	async def send_command(self, context):
		statuses = await self.send()
		if all(status in range(200, 300) for status in statuses.values()):
			await context.message.add_reaction('✅')
		else:
			await context.message.add_reaction('❌')
			await context.send(
				'The following APIs failed:'
				'\n'.join(f'• {config_key}: **{status}**' for config_key, status in statuses.items()))

	@commands.Cog.listener(name='on_guild_join')
	@commands.Cog.listener(name='on_guild_remove')
	async def on_guild_change(self, _):
		await self.notify_owners()
		await self.send()

def setup(bot):
	bot.add_cog(BotBinStats(bot))
