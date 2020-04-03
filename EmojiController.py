import logging

from discord.ext import commands


class Controller(commands.Cog):
    def __init__(self, model, view, bot):
        self.model = model
        self.view = view
        self.bot = bot
        self.logger = logging.getLogger('bot_logs')
        self.logger.info('Controller ON')

    @commands.command()
    async def me(self, ctx, args):
        """
        Repeats user input message and returns it all spaced out in bold
        Sends to view for display
        @param ctx: Discord context
        @param args: String user input argument
        @return: None
        """
        self.logger.info('[command] - me()')
        str_output = ''
        for word in args:
            str_output += '**' + word + '**' + ' '
        self.logger.debug(str_output)
        await self.view.print(ctx, str_output)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def log(self, ctx, *args):
        """
        Logs emojis, sets up logging parameters then calls model for logging
        @param ctx: Discord context
        @param args: List user input arguments
        @return: None
        """
        self.logger.info('[COMMAND] - log()')
        self.logger.debug(args)
        # log from last compiled
        list_date = list(self.model.db[ctx.guild.id])  # get dates from given ID
        last_date = list_date[-1]  # get latest entry

        # continue from last
        if args == ():
            last_date_index = len(list_date) - 1
            await self.model.prepare_db(ctx.guild.id, last_date)
            await self.model.log_helper(ctx.guild.me, ctx.guild.text_channels, last_date,
                                        index=last_date_index, guild_id=ctx.guild.id, is_new=False)
        # log from the start
        elif 'n' in args or 'new' in args:
            await self.model.new_db(ctx.guild.id)
            await self.model.log_helper(ctx.guild.me, ctx.guild.text_channels, last_date,
                                        guild_id=ctx.guild.id, is_new=True)
        # default do nothing
        else:
            return
        await self.view.db(ctx)

    @commands.command()
    async def re(self, ctx, *args):
        """
        Repeats user input, sends to view for display
        @param ctx: Discord context
        @param args: List user input arguments
        @return: None
        """
        self.logger.info('[COMMAND] - re()')
        self.logger.debug(args)
        msg = ' '.join(args)
        await self.view.print(ctx, msg)

    @commands.command(aliases=['exp', 'save'])
    @commands.has_permissions(manage_guild=True)
    async def export(self, ctx):
        """
        Export db contents, calls model to update & save to firebase (and locally)
        @param ctx: Discord context
        @return: None
        """
        self.logger.info('[COMMAND] - exp()')
        self.logger.debug(ctx.guild.id)
        self.model.export(ctx.guild.id)
        await self.view.print(ctx, 'done')

    @commands.command(aliases=['graph'])
    async def plot(self, ctx):
        """
        Creates time series graph, calls model for creation
        @param ctx: Discord context
        @return: None
        """
        self.logger.info('[COMMAND] - graph()')
        await self.view.graph(ctx)

    @commands.command('pie')
    async def pie(self, ctx):
        """
        Creates pie chart of latest data values, calls model for creation
        @param ctx: Discord context
        @return: None
        """
        self.logger.info('[COMMAND] - pie()')
        await self.view.pie(ctx)

    @commands.command()
    async def table(self, ctx, *args):
        """
        Creates table of all values formatted in descending order, calls model for creation
        @param ctx: Discord context
        @return: None
        """
        self.logger.info('[COMMAND] - table()')
        await self.view.table(ctx, 0 if args == () else int(args[0]) - 1)


    # todo: clean up argument use with extra args input
    @commands.command()
    async def bar(self, ctx, *arg):
        """
        Creates stacked bar graph of db data values, calls model for creation
        If no arguments, calls default format (instance)
        else, uses desired type: instance, total, alpha (alphabetical)
        @param ctx: Discord context
        @param arg: list user input arguments
        @return: None
        """
        self.logger.info('[COMMAND] - bar()')
        if arg:
            arg = arg[0]
            await self.view.bar(ctx, arg)
        else:
            await self.view.bar(ctx)

    @commands.command('bch')
    async def bar_change(self, ctx, *arg):
        """
        Creates stacked bar graph of db data values of change from prior month, calls model for creation
        If no arguments, calls default format (instance)
        else, uses desired type: instance or total
        @param ctx: Discord context
        @param arg: list user input arguments
        @return: None
        """
        self.logger.info('[COMMAND] - bar_change()')
        if arg:
            arg = arg[0]
            await self.view.bar(ctx, arg)
        else:
            await self.view.bar(ctx, is_delta=True)
