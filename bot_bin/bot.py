import asyncio
import contextlib
import logging
import re
import traceback
import uuid

try:
	import asyncpg
except ImportError:
	HAVE_ASYNCPG = False
else:
	HAVE_ASYNCPG = True
import discord
from discord.ext import commands
try:
	import uvloop
except ImportError:
	pass  # Windows
else:
	asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

class Bot(commands.AutoShardedBot):
	def __init__(self, *args, **kwargs):
		self.config = kwargs.pop('config')
		self._should_setup_db = kwargs.pop('setup_db', False)
		if self._should_setup_db and not HAVE_ASYNCPG:
			raise ImportError('this bot requires asyncpg but it is not installed')
		self.process_config()
		self._fallback_prefix = str(uuid.uuid4())

		super().__init__(
			command_prefix=self.get_prefix_,
			description=kwargs.pop('description', self.config.get('description')),
			help_command=kwargs.pop('help_command', commands.MinimalHelpCommand()),
			*args, **kwargs)
		# do this after super().__init__ in case initial_activity depends on self.is_ready()
		self.activity = self.initial_activity()

	def process_config(self):
		self.config['success_emojis'] = {
			k: convert_emoji(v)
			for k, v
			in self.config.get('success_emojis', {False: '❌', True: '✅'}).items()}

		ignore_bots_conf = self.config.setdefault('ignore_bots', {})
		ignore_bots_conf.setdefault('default', True)
		overrides_conf = ignore_bots_conf.setdefault('overrides', {})
		overrides_conf.setdefault('guilds', ())
		overrides_conf.setdefault('channels', ())
		overrides_conf['guilds'] = set(overrides_conf['guilds'])
		overrides_conf['channels'] = set(overrides_conf['channels'])

	def initial_activity(self):
		try:
			prefixes = self.config['prefixes']
		except KeyError:
			return None

		return discord.Game(name=prefixes[0] + 'help') if prefixes else None

	def get_prefix_(self, bot, message):
		match = self.prefix_re.search(message.content)

		if match is None:
			# Callable prefixes must always return at least one prefix,
			# but no prefix was found in the message,
			# so we still have to return *something*.
			# Use a UUID because it's practically guaranteed not to be in the message.
			return self._fallback_prefix
		else:
			return match[0]

	@property
	def prefix_re(self):
		prefixes = self.config.get('prefixes', [])

		prefixes = list(prefixes)  # ensure it's not a tuple
		if self.is_ready():
			prefixes.extend([f'<@{self.user.id}>', f'<@!{self.user.id}>'])

		prefixes = '|'.join(map(re.escape, prefixes))
		prefixes = f'(?:{prefixes})'

		return re.compile(fr'{prefixes}\s*', re.IGNORECASE)

	### Events

	async def on_ready(self):
		separator = '━' * 44
		logger.info(separator)
		logger.info('Logged in as: %s', self.user)
		logger.info('ID: %s', self.user.id)
		logger.info(separator)
		# in case there's an activity that depends on being ready
		await self.change_presence(activity=self.initial_activity())

	async def on_message_edit(self, before, after):
		if before.content != after.content:
			await self.process_commands(after)

	async def process_commands(self, message):
		if self.should_reply(message):
			ctx = await self.get_context(message)
			await self.invoke(ctx)

	# based on https://github.com/Rapptz/RoboDanny/blob/ca75fae7de132e55270e53d89bc19dd2958c2ae0/bot.py#L77-L85
	async def on_command_error(self, ctx, error):
		with contextlib.suppress(discord.HTTPException):
			if isinstance(error, commands.NoPrivateMessage):
				await ctx.author.send('This command cannot be used in private messages.')
			elif isinstance(error, commands.DisabledCommand):
				message = 'Sorry. This command is disabled and cannot be used.'
				try:
					await ctx.author.send(message)
				except discord.Forbidden:
					await ctx.send(message)
			elif isinstance(error, commands.NotOwner):
				logger.error('%s tried to run %s but is not the owner', ctx.author, ctx.command.name)
				await ctx.message.add_reaction(self.config['success_emojis'][False])
			elif isinstance(error, (commands.UserInputError, commands.CheckFailure)):
				await ctx.send(error)
			elif (
				isinstance(error, commands.CommandInvokeError)
				and (not ctx.cog or type(ctx.cog).cog_command_error is commands.Cog.cog_command_error)  # not overridden
				and not hasattr(ctx.command, 'on_error')
			):
				logger.error('"%s" caused an exception <%s>', ctx.message.content, ctx.message.jump_url)
				logger.error(''.join(traceback.format_tb(error.original.__traceback__)))
				# pylint: disable=logging-format-interpolation
				logger.error('{0.__class__.__name__}: {0}'.format(error.original))

				await ctx.send('An internal error occured while trying to run that command.')

	### Utility functions

	def should_reply(self, message):
		"""return whether the bot should reply to a given message"""
		return not (
			message.author == self.user
			or (message.author.bot and not self.should_reply_to_bot(message)))

	def should_reply_to_bot(self, message):
		should_reply = not self.config['ignore_bots'].get('default')
		overrides = self.config['ignore_bots']['overrides']

		def check_override(location, overrides_key):
			return location and location.id in overrides[overrides_key]

		if check_override(message.guild, 'guilds') or check_override(message.channel, 'channels'):
			should_reply = not should_reply

		return should_reply

	async def is_privileged(self, member):
		return member.guild_permissions.administrator or await self.is_owner(member)

	### Init / Shutdown

	async def start(self):
		if self._should_setup_db:
			await self.init_db()
		self.load_extensions()

		await super().start(self.config['tokens'].pop('discord'))

	async def close(self):
		if self._should_setup_db:
			with contextlib.suppress(AttributeError):
				await self.pool.close()
		await super().close()

	async def init_db(self):
		credentials = self.config['database']
		self.pool = await asyncpg.create_pool(**credentials)

	def load_extensions(self):
		for extension in self.startup_extensions:  # subclasses must define this
			self.load_extension(extension)

def convert_emoji(s) -> discord.PartialEmoji:
	match = re.search(r'<?(a?):([A-Za-z0-9_]+):([0-9]{17,})>?', s)
	if match:
		return discord.PartialEmoji(animated=match[1], name=match[2], id=int(match[3]))
	return discord.PartialEmoji(animated=None, name=s, id=None)
