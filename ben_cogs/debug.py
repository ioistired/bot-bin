#!/usr/bin/env python3
# encoding: utf-8

import asyncio
import contextlib
import copy
import io

import discord
from discord.ext import commands
import humanize
import objgraph
import psutil

# ensure all commands in this module are hidden
# since there is no default way to hide an entire cog
def command(*args, **kwargs):
	kwargs['hidden'] = True
	return commands.command(*args, **kwargs)

# using code provided by khazhyk under the MIT License
# Copyright © 2017 khazhyk
# License: https://github.com/khazhyk/dango.py/blob/512c76eca8309cb5c311fc2d961e3defa1ccbd9e/LICENSE
# Debug plugin code: https://github.com/khazhyk/dango.py/blob/512c76eca8309cb5c311fc2d961e3defa1ccbd9e/plugins/debug.py

class Debug:
	def __init__(self):
		self.process = psutil.Process()

	async def __local_check(self, context):
		if not await context.bot.is_owner(context.author):
			raise commands.NotOwner
		return True

	@commands.command(aliases=('su', 'sudo'))
	async def runas(self, context, who: discord.User, *, cmd):
		"""Run a command impersonating another user."""
		fake_message = copy.copy(context.message)

		# Message._update handles clearing cached properties
		fake_message._update(context.channel, dict(
			content=context.prefix + cmd))
		fake_message.author = who
		new_context = await context.bot.get_context(fake_message)
		await context.bot.invoke(new_context)

	@command(name='most-common-types')
	async def most_common_types(self, context):
		await context.send(str(await context.bot.loop.run_in_executor(None, objgraph.most_common_types)))

	@command()
	async def objgrowth(self, context):
		"""Show the increase in peak object counts since last call."""

		stdout = io.StringIO()

		with contextlib.redirect_stdout(stdout):
			await context.bot.loop.run_in_executor(None, objgraph.show_growth)

		await context.send(f'```{stdout.getvalue()}```')

	@command()
	async def mem(self, context, base1024: bool = False):
		"""current memory usage

		output is in base 1000 units unless base1024 is set to True
		"""
		await context.send(self.memory_usage(base1024=base1024))

	def memory_usage(self, *, base1024=False):
		return humanize.naturalsize(self.process.memory_full_info().uss, binary=base1024)


def setup(bot):
	bot.add_cog(Debug())
