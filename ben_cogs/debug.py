import asyncio
import functools
import io

import discord
from discord.ext import commands
import humanize
import objgraph
import psutil

from .misc import codeblock

class BenCogsDebug(commands.Cog, command_attrs=dict(hidden=True)):
	def __init__(self):
		self.process = psutil.Process()

	async def cog_check(self, context):
		if not await context.bot.is_owner(context.author):
			raise commands.NotOwner
		return True

	@commands.command(name='most-common-types')
	async def most_common_types(self, context):
		await context.send(codeblock(await self.objgraph_show(objgraph.show_most_common_types)))

	@commands.command()
	async def objgrowth(self, context):
		"""Show the increase in peak object counts since last call."""
		await context.send(codeblock(await self.objgraph_show(objgraph.show_growth)))

	async def objgraph_show(self, fn):
		out = io.StringIO()
		fn = functools.partial(fn, file=out)
		await context.bot.loop.run_in_executor(None, fn)
		return out.read()

	@commands.command()
	async def mem(self, context, base1024: bool = False):
		"""current memory usage

		output is in base 1000 units unless base1024 is set to True
		"""
		await context.send(self.memory_usage(base1024=base1024))

	def memory_usage(self, *, base1024=False):
		return humanize.naturalsize(self.process.memory_full_info().uss, binary=base1024)

# maintain alias for backwards compatibility of subclasses
class Debug(BenCogsDebug):
	pass

def setup(bot):
	bot.add_cog(BenCogsDebug())
