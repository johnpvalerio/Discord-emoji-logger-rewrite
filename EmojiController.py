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
        if args == ():
            args = ''
            last_date = list(self.model.db[ctx.guild.id])[-1]
            copy_date = list(self.model.db[ctx.guild.id])[-2]
            print(copy_date)
            print('FROM LAST', last_date)
            await self.model.prepare_db(ctx.guild.id, last_date)
        # log from the start
        else:
            args = 'n'
        for current_channel in list(filter(lambda channel:
                                           channel.permissions_for(ctx.guild.me).read_messages,
                                           ctx.guild.text_channels)):
            if args in ['n', 'new']:
                await self.model.log_channel(current_channel)
            else:
                # log from last saved
                await self.model.log_channel(current_channel, last_date)
        # todo: if continue, add missing data from last iteration, get ALL dates from last date to now
        if args == '':
            last_date = list(self.model.db[ctx.guild.id])[-1]
            copy_date = list(self.model.db[ctx.guild.id])[-2]
            self.model.merge_entry(ctx.guild.id, last_date, copy_date)
        await self.view.db(ctx)

    @commands.command()
    async def re(self, ctx, args):
        print(args)
        await self.view.print(ctx, args)

    @commands.command('exp')
    @commands.has_permissions(administrator=True)
    async def export(self, ctx, *args):
        self.model.export()
        await self.view.print(ctx, 'done')

    @commands.command('graph')
    async def plot(self, ctx):
        await self.view.graph(ctx)

    @commands.command('pie')
    async def pie(self, ctx):
        await self.view.pie(ctx)

    @commands.command()
    async def table(self, ctx):
        await self.view.table(ctx)
