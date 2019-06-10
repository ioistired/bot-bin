import asyncpg
from discord.ext import commands

from .misc import codeblock, timeit, PrettyTable

class BenCogsSql(commands.Cog):
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
		elapsed, result = await timeit(self.pool.execute(query.strip('`')))
		elapsed = round(elapsed * 1000, 2)

		await context.send(f'`{result}`\n*Executed in {elapsed}ms.*')

	@sql_command.command(name='fetch', aliases=['f'])
	async def sql_fetch_command(self, context, *, query):
		"""Get the rows of a SQL query."""
		elapsed, results = await timeit(self.pool.fetch(query.strip('`')))
		elapsed = round(elapsed * 1000, 2)

		message = codeblock(str(PrettyTable(results)))
		await context.send(f'{message}\n*{len(results)} rows retrieved in {elapsed}ms.*')

	@sql_command.command(name='fetchval', aliases=['fv'])
	async def sql_fetchval_command(self, context, *, query):
		"""Get a single value from a SQL query."""
		elapsed, result = await timeit(self.pool.fetchval(query.strip('`')))
		elapsed = round(elapsed * 1000, 2)

		# fetchval returns a native python result
		# so its repr is probably python code
		message = codeblock(repr(result), lang='python')
		await context.send(f'{message}\n*Retrieved in {elapsed}ms.*')

def setup(bot):
	if bot.case_insensitive:
		BenCogsSql.sql_command.aliases.clear()
	bot.add_cog(BenCogsSql(bot.pool))
