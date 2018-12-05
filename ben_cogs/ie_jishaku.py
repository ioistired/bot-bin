# as jishaku now supports import expressions,
# this cog is no longer necessary, and is left here for backwards compatibility
from jishaku.cog import Jishaku

# if we just import setup from jishaku, it'll add a cog that isn't in ben_cogs
# which means that unload_extension('ben_cogs.ie_jishaku') will not remove Jishaku
# so we make a dummy class so that __module__ is properly updated
class Jishaku(Jishaku):
	pass

def setup(bot):
	bot.add_cog(Jishaku(bot))
