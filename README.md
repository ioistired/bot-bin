# Bot Bin
Shared cogs and utilities for use in Discord bots.
Some cogs require bot configuration; those that do expect a `bot.config` dict attribute.

## bot_bin.bot

Contains an AutoShardedBot subclass. Contains custom error logging, customizable on_message bot ignoring,
case insensitive prefixes, and database setup if the setup_db kwarg is set to True. Requires the config kwarg
to be set to a dict. bot.config['tokens']['discord'] should be the bot's Discord token.

## bot_bin.debug

Contains memory usage and performance debugging commands. Most other debug functionality is already provided
by [jishaku](https://pypi.org/project/jishaku/).

## bot_bin.misc

Contains an uptime, ping, and copyright command. The latter requires bot.config['copyright_license_file'] to be
set to a path to a text file, the contents of which will be sent when the user runs the copyright command.

Also contains various utilities:
- `codeblock` wraps text in a markdown code block
- `absolute_natural_timedelta` returns an English string representing an amount of seconds
- `natural_timedelta` returns an English string representing the difference between two dates.
  This function differs from `absolute_natural_timedelta` in that it also supports years and months.
- `natural_rate` returns an English string representing a rate of occurence.
- `plural` is a format object which pluralizes strings. For example: `f'Found {plural(len(results)):weapon}'`
- `natural_join` joins a sequence of strings according to English grammar
- `timeit` is a context manager that times the code in the `with` block

## bot_bin.sql

Contains SQL execution commands for asyncpg.
Requires `bot.pool` to be set to either an asyncpg Connection or a ConnectionPool.
Requires the `bot_bin[sql]` extra.

## bot_bin.stats

Implements the guild count API for DBL, DBots, Bots For Discord, LBots, and Discord Boats.
This is configured using `bot.config['tokens']['stats']`.
Each key should be a domain, e.g. `bot.config['tokens']['stats']['discordbots.org']` would be the bot's DBL token.

Defines a `send-stats` owner only command which sends the current guild counts to the configured APIs
and reports any errors.
