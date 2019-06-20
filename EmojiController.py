from discord.ext import commands


class Controller(commands.Cog):
    def __init__(self, model, view, bot):
        self.model = model
        self.view = view
        self.bot = bot
        print('Controller ON')

    @commands.command()
    async def me(self, ctx, args):
        """
        Repeats user input message and returns it all spaced out in bold
        Sends to view for display
        @param ctx: Discord context
        @param args: String user input argument
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - me()')
        print("--------------------------")
        str_output = ''
        for word in args:
            str_output += '**' + word + '**' + ' '
        print(str_output)
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
        print("\n--------------------------")
        print('[COMMAND] - log()')
        print("--------------------------")
        print(args)
        # log from last compiled
        list_date = list(self.model.db[ctx.guild.id])
        last_date = list_date[-1]
        if args == ():
            args = ''
            last_date_index = len(list_date) - 1
            await self.model.prepare_db(ctx.guild.id, last_date)
        # log from the start
        elif 'n' in args or 'new' in args:
            args = 'n'
            await self.model.new_db(ctx.guild.id)
        # default do nothing
        else:
            return

        # log emojis in bot viewable channels
        for current_channel in list(filter(lambda channel:
                                           channel.permissions_for(ctx.guild.me).read_messages,
                                           ctx.guild.text_channels)):
            # log new from start
            if args in ['n', 'new']:
                await self.model.log_channel(current_channel)
            # log from last saved
            else:
                await self.model.log_channel(current_channel, last_date)
        # fix new entry
        if args == '':
            list_date = list(self.model.db[ctx.guild.id])
            for i in range(last_date_index+1, len(list_date)):
                self.model.merge_entry(ctx.guild.id, list_date[i], list_date[last_date_index])
        await self.view.db(ctx)

    @commands.command()
    async def re(self, ctx, *args):
        """
        Repeats user input, sends to view for display
        @param ctx: Discord context
        @param args: List user input arguments
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - re()')
        print("--------------------------")
        print(args)
        msg = ' '.join(args)
        await self.view.print(ctx, msg)

    @commands.command('exp')
    @commands.has_permissions(manage_guild=True)
    async def export(self, ctx):
        """
        Export db contents, calls model to update & save to firebase (and locally)
        @param ctx: Discord context
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - exp()')
        print("--------------------------")
        self.model.export(ctx.guild.id)
        await self.view.print(ctx, 'done')

    @commands.command('graph')
    async def plot(self, ctx):
        """
        Creates time series graph, calls model for creation
        @param ctx: Discord context
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - graph()')
        print("--------------------------")
        await self.view.graph(ctx)

    @commands.command('pie')
    async def pie(self, ctx):
        """
        Creates pie chart of latest data values, calls model for creation
        @param ctx: Discord context
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - pie()')
        print("--------------------------")
        await self.view.pie(ctx)

    @commands.command()
    async def table(self, ctx):
        """
        Creates table of all values formatted in descending order, calls model for creation
        @param ctx: Discord context
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - table()')
        print("--------------------------")
        await self.view.table(ctx)

    @commands.command('emb')
    async def embed(self, ctx, *args):
        """
        Creates embedded message of user input, calls model for creation using default values
        @param ctx: Discord context
        @param args: List user input arguments
        @return: None
        """
        print("\n--------------------------")
        print('[COMMAND] - embed()')
        print("--------------------------")
        msg = ' '.join(args)
        print(msg)
        await self.view.embed(ctx, msg)

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
        print("\n--------------------------")
        print('[COMMAND] - bar()')
        print("--------------------------")
        if arg:
            arg = arg[0]
            await self.view.bar(ctx, arg)
        else:
            await self.view.bar(ctx)
