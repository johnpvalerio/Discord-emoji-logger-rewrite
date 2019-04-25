from discord.ext import commands
import plotly.plotly as py
import plotly.graph_objs as go

class View(commands.Cog):
    def __init__(self, model, bot):
        self.model = model
        self.bot = bot

        print('View ON')

    async def print(self, ctx, msg):
        await ctx.send(msg)

    def db(self):
        print(self.model.db)
        for guild_ID,val in self.model.db.items():
            # print(guild_ID)
            # print(val)
            for date,val2 in self.model.db[guild_ID].items():
                # print(date)
                # print(val2)
                for emoji_ID,emoji_obj in self.model.db[guild_ID][date].items():
                    # print(emoji_ID)
                    # print(emoji_obj)
                    # print('\t', emoji_obj.instance_count, ' - ', emoji_obj.total_count)
                    print('\t', emoji_obj.emoji_obj.name, ': ', emoji_obj.instance_count, ' - ', emoji_obj.total_count)

    def graph(self, ctx):
        dates = []
        emoji_IDs = []
        emoji_list = []
        for date in self.model.db[ctx.guild.id]:
            dates.append(date)
        for emoji in ctx.guild.emojis:
            emoji_IDs.append(emoji.id)
        for date in dates:
            emoji_obj = self.model.db[ctx.guild.id][date][emoji_IDs[0]]
            print(emoji_obj.instance_count)
            emoji_list.append(emoji_obj.instance_count)
        data = [go.Scatter(x=dates, y=emoji_list)]
        py.iplot(data, filename='test')
