import contextlib
import functools
import inspect

import aiocontextvars
import asyncpg
from discord.ext import commands

from .misc import codeblock, timeit, PrettyTable

_connection = aiocontextvars.ContextVar('connection')
# make the interface a bit shorter
connection = lambda: _connection.get()
connection.set = _connection.set

def optional_connection(func):
	"""Decorator that acquires a connection for the decorated function if the contextvar is not set."""
	class pool:
		def __init__(self, pool):
			self.pool = pool
		async def __aenter__(self):
			try:
				# allow someone to call a decorated function twice within the same Task
				# the second time, a new connection will be acquired
				connection().is_closed()
			except (asyncpg.InterfaceError, LookupError):
				self.connection = conn = await self.pool.acquire()
				connection.set(conn)
				return conn
			else:
				return connection()
		async def __aexit__(self, *excinfo):
			with contextlib.suppress(AttributeError):
				await self.pool.release(self.connection)

	if inspect.isasyncgenfunction(func):
		@functools.wraps(func)
		async def inner(self, *args, **kwargs):
			async with pool(self.bot.pool) as conn:
				# this does not handle two-way async gens, but i don't have any of those either
				async for x in func(self, *args, **kwargs):
					yield x
	else:
		@functools.wraps(func)
		async def inner(self, *args, **kwargs):
			async with pool(self.bot.pool) as conn:
				return await func(self, *args, **kwargs)

	return inner

class BotBinSql(commands.Cog):
	def __init__(self, pool):
		self.pool = pool

	async def cog_command_error(self, context, error):
		error = getattr(error, 'original', error)
		if isinstance(error, (asyncpg.PostgresError, asyncpg.InterfaceError)):
			await context.send(f'{type(error).__name__}: {error}')
			return
		raise

	@commands.group(name='sql', aliases=['SQL'], hidden=True, invoke_without_command=False, ignore_extra=True)
	@commands.is_owner()
	async def sql_command(self, context):
		pass

	@sql_command.command(name='execute', aliases=['e'])
	async def sql_execute_command(self, context, *, query):
		"""Execute a SQL query."""
		with timeit() as timer:
			result = await self.pool.execute(query.strip('`'))
		elapsed = round(timer.elapsed * 1000, 2)

		await context.send(f'`{result}`\n*Executed in {elapsed}ms.*')

	@sql_command.command(name='fetch', aliases=['f'])
	async def sql_fetch_command(self, context, *, query):
		"""Get the rows of a SQL query."""
		with timeit() as timer:
			results = await self.pool.fetch(query.strip('`'))
		elapsed = round(timer.elapsed * 1000, 2)

		message = codeblock(str(PrettyTable(results)))
		await context.send(f'{message}\n*{len(results)} rows retrieved in {elapsed}ms.*')

	@sql_command.command(name='fetchval', aliases=['fv'])
	async def sql_fetchval_command(self, context, *, query):
		"""Get a single value from a SQL query."""
		with timeit() as timer:
			result = await self.pool.fetchval(query.strip('`'))
		elapsed = round(timer.elapsed * 1000, 2)

		# fetchval returns a native python result
		# so its repr is probably python code
		message = codeblock(repr(result), lang='python')
		await context.send(f'{message}\n*Retrieved in {elapsed}ms.*')

def setup(bot):
	if bot.case_insensitive:
		BotBinSql.sql_command.aliases.clear()
	bot.add_cog(BotBinSql(bot.pool))
