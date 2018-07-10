#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from contextlib import redirect_stdout
import io

import discord.ext.commands
import objgraph


# ensure all commands in this module are hidden
# since there is no default way to hide an entire cog
def command(*args, **kwargs):
	kwargs['hidden'] = True
	return discord.ext.commands.command(*args, **kwargs)

# using code provided by khazhyk
# Copyright © 2017 khazhyk
# License: https://github.com/khazhyk/dango.py/blob/512c76eca8309cb5c311fc2d961e3defa1ccbd9e/LICENSE
# Debug plugin code: https://github.com/khazhyk/dango.py/blob/512c76eca8309cb5c311fc2d961e3defa1ccbd9e/plugins/debug.py

class Debug:
	async def __local_check(self, context):
		return await context.bot.is_owner(context.author)

	@command()
	async def objgrowth(self, context):
		stdout = io.StringIO()

		with redirect_stdout(stdout):
			await context.bot.loop.run_in_executor(None, objgraph.show_growth)

		await context.send(f'```{stdout.getvalue()}```')

def setup(bot):
	bot.add_cog(Debug())
