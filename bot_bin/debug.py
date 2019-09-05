import contextlib
import copy
import functools
import io
import time
import traceback

import discord
from discord.ext import commands
import humanize
import objgraph
try:
	import psutil
except (OSError, ImportError):
	HAVE_PSUTIL = False
else:
	HAVE_PSUTIL = True

from .misc import codeblock

# Code provided by Rapptz under the MIT License
# © 2015 Rapptz
# https://github.com/Rapptz/RoboDanny/blob/d3148649ba504dcb6ca5499421bd397419ce7c1d/cogs/admin.py
class PerformanceMocker:
	"""A mock object that can also be used in await expressions."""

	def permissions_for(self, obj):
		# Lie and say we don't have permissions to embed
		# This makes it so pagination sessions just abruptly end on __init__
		# Most checks based on permission have a bypass for the owner anyway
		# So this lie will not affect the actual command invocation.
		perms = discord.Permissions.all()
		perms.administrator = False
		perms.embed_links = False
		perms.add_reactions = False
		return perms

	def __getattr__(self, attr):
		return self

	def __call__(self, *args, **kwargs):
		return self

	def __repr__(self):
		return '<PerformanceMocker>'

	def __await__(self):
		async def nop():
			return self
		return nop().__await__()

	def __enter__(self):
		return self

	def __exit__(self, *args):
		pass

	async def __aenter__(self):
		return self

	async def __aexit__(self, *args):
		pass

	def __len__(self):
		return 0

	def __bool__(self):
		return False

class BotBinDebug(commands.Cog, command_attrs=dict(hidden=True)):
	def __init__(self):
		if HAVE_PSUTIL:
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

	# Code provided by Rapptz under the MIT License
	# © 2015 Rapptz
	# https://github.com/Rapptz/RoboDanny/blob/d3148649ba504dcb6ca5499421bd397419ce7c1d/cogs/admin.py
	@commands.command()
	async def perf(self, context, *, command):
		"""Checks the timing of a command, attempting to suppress HTTP calls."""

		msg = copy.copy(context.message)
		msg.content = context.prefix + command

		new_context = await context.bot.get_context(msg, cls=type(context))

		# Intercepts the Messageable interface a bit
		new_context._state = PerformanceMocker()
		new_context._author = PerformanceMocker()
		new_context.author._state = PerformanceMocker()
		new_context.message._state = PerformanceMocker()
		new_context.message.channel = PerformanceMocker()
		new_context.channel = PerformanceMocker()

		if new_context.command is None:
			return await context.send('No command found')

		start = time.perf_counter()
		try:
			await new_context.command.invoke(new_context)
		except commands.CommandError:
			end = time.perf_counter()
			success = '❌'
			with contextlib.suppress(discord.HTTPException):
				await context.send(f'```py\n{traceback.format_exc()}\n```')
		else:
			end = time.perf_counter()
			success = '✅'

		await context.send(f'Status: {success} Time: {(end - start) * 1000:.2f}ms')


def setup(bot):
	bot.add_cog(BotBinDebug())

	if not HAVE_PSUTIL:
		for command in 'objgrowth', 'most-common-types', 'mem':
			bot.remove_command(command)
