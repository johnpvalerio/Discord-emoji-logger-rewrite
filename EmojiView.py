from discord.ext import commands
import matplotlib.pyplot as plt
import discord

class View(commands.Cog):
    def __init__(self, model, bot):
        self.model = model
        self.bot = bot

        print('View ON')

    async def print(self, ctx, msg):
        await ctx.send(msg)

    async def db(self, ctx):
        print(self.model.db)

        for date, val2 in self.model.db[ctx.guild.id].items():
            for emoji_ID, emoji_obj in self.model.db[ctx.guild.id][date].items():
                print('\t', emoji_obj.emoji_obj.name, ': ', emoji_obj.instance_count, ' - ', emoji_obj.total_count)
            print('\t\t - - - -')
            print(date)
        await ctx.send('complete')

    async def graph(self, ctx):
        dates = []
        emoji_IDs = []
        emoji_list = []
        # dates: x
        for date in self.model.db[ctx.guild.id]:
            dates.append(date)
        # emoji ID
        for emoji in ctx.guild.emojis:
            emoji_IDs.append(emoji.id)
        # emoji
        for id in emoji_IDs:
            for date in dates:
                emoji_obj = self.model.db[ctx.guild.id][date][id]
                emoji_list.append(emoji_obj.instance_count)
            plt.plot(dates, emoji_list)
            emoji_list = []
        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('graph.png', bbox_inches='tight')
        await ctx.send(file=discord.File('graph.png'))
