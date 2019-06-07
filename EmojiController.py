from discord.ext import commands


class Controller(commands.Cog):
    def __init__(self, model, view, bot):
        self.model = model
        self.view = view
        self.bot = bot
        print('Controller ON')

    @commands.command()
    async def me(self, ctx, args):
        print("\n--------------------------")
        print('[COMMAND] - me()')
        print("--------------------------")
        str_output = ''
        for word in args:
            str_output += '**' + word + '**' + ' '
        print(str_output)
        await self.view.print(ctx, str_output)

    @commands.command()
    # @commands.has_permissions(administrator=True)
    @commands.has_permissions(manage_guild=True)
    async def log(self, ctx, *args):
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
        print("\n--------------------------")
        print('[COMMAND] - re()')
        print("--------------------------")
        print(args)
        msg = ' '.join(args)
        await self.view.print(ctx, msg)

    @commands.command('exp')
    @commands.has_permissions(administrator=True)
    async def export(self, ctx, *args):
        print("\n--------------------------")
        print('[COMMAND] - exp()')
        print("--------------------------")
        print(args)
        self.model.export()
        await self.view.print(ctx, 'done')

    @commands.command('graph')
    async def plot(self, ctx):
        print("\n--------------------------")
        print('[COMMAND] - graph()')
        print("--------------------------")
        await self.view.graph(ctx)

    @commands.command('pie')
    async def pie(self, ctx):
        print("\n--------------------------")
        print('[COMMAND] - pie()')
        print("--------------------------")
        await self.view.pie(ctx)

    @commands.command()
    async def table(self, ctx):
        print("\n--------------------------")
        print('[COMMAND] - table()')
        print("--------------------------")
        await self.view.table(ctx)

    @commands.command('emb')
    async def embed(self, ctx, *args):
        print("\n--------------------------")
        print('[COMMAND] - embed()')
        print("--------------------------")
        msg = ' '.join(args)
        print(msg)
        await self.view.embed(ctx, msg)

    @commands.command()
    async def bar(self, ctx):
        print("\n--------------------------")
        print('[COMMAND] - bar()')
        print("--------------------------")
        await self.view.bar(ctx)
