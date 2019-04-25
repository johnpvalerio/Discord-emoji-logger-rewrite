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
        # await ctx.send(str_output)

    @commands.command()
    async def log(self, ctx):
        print("\n--------------------------")
        print('[COMMAND] - log()')
        print("--------------------------")
        for current_channel in list(filter(lambda channel:
                                           channel.permissions_for(ctx.guild.me).read_messages,
                                           ctx.guild.text_channels)):
            # print(current_channel)
            await self.model.log_channel(current_channel)
        # self.view.db()

    @commands.command()
    async def re(self, ctx, args):
        print(args)
        await self.view.print(ctx,args)

    @commands.command('exp')
    async def export(self, ctx, *args):
        self.model.export()

    @commands.command('graph')
    async def plot(self, ctx):
        self.view.graph(ctx)