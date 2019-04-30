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
    @commands.has_permissions(administrator=True)
    async def log(self, ctx, *args):
        print("\n--------------------------")
        print('[COMMAND] - log()')
        print("--------------------------")
        if args == ():
            args = ''
            cur_date = list(self.model.db[ctx.guild.id])[-1]
            await self.model.prepare_db(ctx.guild.id, cur_date)
        for current_channel in list(filter(lambda channel:
                                           channel.permissions_for(ctx.guild.me).read_messages,
                                           ctx.guild.text_channels)):
            if args in ['n', 'new']:
                await self.model.log_channel(current_channel)
            else:
                # log from last saved
                await self.model.log_channel(current_channel, cur_date)
                print('continue')
        # todo: if continue, add missing data from last iteration
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
