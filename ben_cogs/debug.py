#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from contextlib import redirect_stdout
import io

from discord.ext.commands import command
import objgraph


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
