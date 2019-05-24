# import copy

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

    # todo: legend ordering
    # do last 3 months graph data
    # ignore 0's (twitch emotes)
    async def graph(self, ctx):
        dates = []  # dates
        list_graph_emoji = []  # emoji object (line)
        url = []  # emoji URL
        lines = []  # graph lines
        img = []
        temp = {}

        counter = 0
        LEGEND_COUNT = 10

        # dates: x
        # last 3 dates
        for date in self.model.db[ctx.guild.id]:
            dates.append(date)
        dates = dates[-4:-1]

        # emoji
        # todo: fix for large values
        # plot lines: dates & list_graph_emoji (inst_count)

        # for id in self.model.db[ctx.guild.id][dates]:
        #     for date in dates:
        #         emoji_obj = self.model.db[ctx.guild.id][date][id]
        #         list_graph_emoji.append(emoji_obj.instance_count)
        #     if counter < LEGEND_COUNT:
        #         line, = plt.plot(dates, list_graph_emoji, label=' - ' + emoji_obj.emoji_obj.name)
        #     else:
        #         line, = plt.plot(dates, list_graph_emoji)
        #     lines.append(line)
        #     url.append(str(emoji_obj.emoji_obj.url))
        #     list_graph_emoji = []
        #     counter += 1

        # temp holds list of date & instance count keyed by emoji ID
        for date in dates:
            for emoji_id in self.model.db[ctx.guild.id][date]:
                # if emoji not yet processed
                if emoji_id not in temp.keys():
                    temp[emoji_id] = {'date': [], 'count': []}
                # todo: if no data for that date, next
                temp[emoji_id]['count'].append(self.model.db[ctx.guild.id][date][emoji_id].instance_count)
                temp[emoji_id]['date'].append(date)

        # todo: create lines
        print(temp)
        for emoji, y in temp.items():
            # print(y['date'], ' - ', y['count'])
            line, = plt.plot(y['date'], y['count'], label=emoji, marker='>')
            if not lines:
                print('LINES')
                print(y['date'])
                for i in y['date']:
                    print(i)
                # line, = plt.plot(y['date'], y['count'], label=emoji, marker='>')
                print(y['date'])
                print(y['count'])
                # lines.append(line)
            else:
                print('NO')



        # adding images in the legend
        # for i in range(len(url)):
        #     async with aiohttp.ClientSession() as session:
        #         url_link = url[i]
        #         async with session.get(url_link) as resp:
        #             if resp.status == 200:
        #                 f = await aiofiles.open('emoji.png', mode='wb')
        #                 await f.write(await resp.read())
        #                 await f.close()
        #                 img.append(HandlerLineImage('emoji.png'))
        # legend_obj = dict(zip(lines, img))
        #
        # # plt.legend(handler_map=legend_obj, ncol=math.ceil(len(lines) / 10))
        # plt.legend(handler_map=legend_obj)
        plt.grid(True)
        plt.title("Time series of emote use in " + ctx.guild.name)

        fig = plt.gcf()
        fig.autofmt_xdate()
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
