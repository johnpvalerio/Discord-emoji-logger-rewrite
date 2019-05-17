import aiofiles as aiofiles
import aiohttp
import math
from discord.ext import commands
import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.transforms import Bbox, TransformedBbox
from matplotlib.legend_handler import HandlerBase
from matplotlib.image import BboxImage
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

    # todo: overlap problems
    async def pie(self, ctx):
        labels = []
        values = []
        latest_date = list(self.model.db[ctx.guild.id])[-1]
        for emoji in self.model.db[ctx.guild.id][latest_date]:
            labels.append(self.model.db[ctx.guild.id][latest_date][emoji].emoji_obj.name)
            values.append(self.model.db[ctx.guild.id][latest_date][emoji].instance_count)
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.axis('equal')
        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('pie.png')
        await ctx.send(file=discord.File('pie.png'))

    #todo: legend ordering
    # do last 3 months graph data
    # ignore 0's (twitch emotes)
    async def graph(self, ctx):
        dates = []  # dates
        emoji_IDs = []  # emoji ID
        emoji_list = []  # emoji object (line)
        url = []  # emoji URL
        lines = []  # graph lines
        img = []

        counter = 0
        LEGEND_COUNT = 10

        # dates: x
        for date in self.model.db[ctx.guild.id]:
            dates.append(date)
        # emoji ID
        # todo: use db emojis, remove 0's
        for emoji in ctx.guild.emojis:
            emoji_IDs.append(emoji.id)
        # emoji
        # todo: fix for large values
        # for i in range(4):
        for id in emoji_IDs:
            for date in dates:
                emoji_obj = self.model.db[ctx.guild.id][date][id]
                emoji_list.append(emoji_obj.instance_count)
            if counter < LEGEND_COUNT:
                line, = plt.plot(dates, emoji_list, label=' - ' + emoji_obj.emoji_obj.name)
            else:
                line, = plt.plot(dates, emoji_list)
            lines.append(line)
            url.append(str(emoji_obj.emoji_obj.url))
            emoji_list = []
            counter += 1

        # adding images in the legend
        for i in range(len(url)):
            async with aiohttp.ClientSession() as session:
                url_link = url[i]
                async with session.get(url_link) as resp:
                    if resp.status == 200:
                        f = await aiofiles.open('emoji.png', mode='wb')
                        await f.write(await resp.read())
                        await f.close()
                        img.append(HandlerLineImage('emoji.png'))
        legend_obj = dict(zip(lines, img))
        # plt.legend(handler_map=legend_obj, ncol=math.ceil(len(lines) / 10))
        plt.legend(handler_map=legend_obj)
        plt.grid(True)
        plt.title("Time series of emote use in " + ctx.guild.name)

        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('graph.png', bbox_inches='tight')
        await ctx.send(file=discord.File('graph.png'))


class HandlerLineImage(HandlerBase):

    def __init__(self, path, space=15, offset=10):
        self.space = space
        self.offset = offset
        self.image_data = plt.imread(path, -1)
        super(HandlerLineImage, self).__init__()

    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):
        l = matplotlib.lines.Line2D([xdescent + self.offset, xdescent + (width - self.space) / 3. + self.offset],
                                    [ydescent + height / 2., ydescent + height / 2.])
        l.update_from(orig_handle)
        l.set_clip_on(False)
        l.set_transform(trans)

        bb = Bbox.from_bounds(xdescent + (width + self.space) / 3. + self.offset,
                              ydescent,
                              height * self.image_data.shape[1] / self.image_data.shape[0],
                              height)

        tbb = TransformedBbox(bb, trans)
        image = BboxImage(tbb)
        image.set_data(self.image_data)

        self.update_prop(image, orig_handle, legend)
        return [l, image]
