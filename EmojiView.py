import aiofiles as aiofiles
import aiohttp
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
        """
        Create and display a pie chart of latest emoji stats
        @param ctx: discord context
        @return: None
        """
        labels = []
        values = []

        # sort by instance count into list: (id, EmojiStat)
        sorted_emojis = self.sort(ctx, 'instance')

        for emoji in sorted_emojis:
            labels.append(emoji[1].emoji_obj.name)
            values.append(emoji[1].instance_count)

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.axis('equal')
        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('pie.png')
        await ctx.send(file=discord.File('pie.png'))

    async def table(self, ctx):
        str_output = ''

        # sort by instance count into list: (id, EmojiStat)
        sorted_emojis = self.sort(ctx, 'instance')
        # create output string
        # emoji: (id, EmojiStat)
        for emoji in sorted_emojis:
            # print(emoji[0], ' - ', emoji[1].instance_count)
            emoji_id = emoji[1].emoji_obj.id
            str_output += str(ctx.bot.get_emoji(emoji_id)) + \
                          ' - ' + str(emoji[1].instance_count) + \
                          '\n'

        # await self.print(ctx, str_output)
        await self.embed(ctx, sorted_emojis)

    # todo: more info like % increase, date, etc
    async def embed(self, ctx, msg):
        if type(msg) is list:
            print('ey')
            output = ''
            embed = discord.Embed(title=ctx.guild.name + '\'s emoji stats')
            for i in range(len(msg)):
                print(msg[i])
                output += str(msg[i][1].emoji_obj) + ' - ' + str(msg[i][1].instance_count) + '\n'

                if i % 5 == 4:
                    embed.add_field(name=str(i - 3) + ' - ' + str(i + 1), value=output, inline=True)
                    output = ''
            embed.add_field(name=str(len(msg) - (len(msg) % 5) + 1) + ' - ' + str(len(msg)), value=output)
        else:
            embed = discord.Embed(title='Untitled')
            embed.add_field(name='Field 1', value=msg)
        await ctx.send(embed=embed)

    # todo: sort by alphabetical order
    async def bar(self, ctx):
        list_names = []
        list_vals = []
        width = 0.3
        y_max = 100
        last_date = list(self.model.db[ctx.guild.id])[-1]
        emote_size = len(self.model.db[ctx.guild.id][last_date])
        ind = [x for x in range(emote_size)]

        if emote_size >= 70:
            text_size = 5
        elif emote_size >= 50:
            text_size = 6
        elif emote_size >= 30:
            text_size = 8
        else:
            text_size = 12

        for emoji_id, emoji in self.model.db[ctx.guild.id][last_date].items():
            print(emoji)
            list_names.append(emoji.emoji_obj.name)
            list_vals.append(emoji.instance_count)
            if y_max < emoji.instance_count:
                y_max = emoji.instance_count

        plt.ylim([0, y_max])
        plt.bar(ind, list_vals, width)
        plt.xticks(ind, list_names, fontsize=text_size, rotation=90)
        plt.xlabel('Emoji')
        plt.ylabel('Single instance count')
        plt.title("Bar graph of emote use in " + ctx.guild.name)  # title
        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('graph.png', bbox_inches='tight')
        await ctx.send(file=discord.File('graph.png'))

    def bottom_calc(self, list_items):
        """
        Helper for bar graph creation, sets bottom attribute for bar stacking
        @param list_items: list of items to process
        @return: 0 default - list of ints matrix add
        """
        output = None
        # default: x axis floor
        if len(list_items) == 0:
            return 0
        # else: add all previous entries
        for x in list_items:
            if output is None:
                output = x
            else:
                output = [sum(y) for y in zip(output, x)]
        return output

    # todo: legend ordering
    # note: matplotlib creates x axis if not enough/too little distance from start/end
    # ignore 0's (twitch emotes)
    async def graph(self, ctx):
        dates = []  # dates
        url = []  # emoji URL
        lines = []  # graph lines
        img = []
        temp_db = {}
        legend_countr = 0
        MAX_LEGEND_COUNT = 10
        MAX_DATES = 5

        # last 3 dates
        for date in self.model.db[ctx.guild.id]:
            dates.append(date)
        dates = dates[-(MAX_DATES + 1):-1]

        print(dates)

        # emoji
        # todo: fix for large values
        # plot lines: dates & list_graph_emoji (inst_count)

        # temp_db holds list of date & instance count keyed by emoji ID
        for date in dates:
            print(date)
            for emoji_id in self.model.db[ctx.guild.id][date]:
                # if emoji not yet processed
                if emoji_id not in temp_db.keys():
                    temp_db[emoji_id] = {'date': [], 'count': []}
                print(emoji_id, ' - ', self.model.db[ctx.guild.id][date][emoji_id].instance_count)

                # if no entry of emoji on that date (newly added emojis)
                # todo: skipping makes url order incorrect
                # if emoji_id not in self.model.db[ctx.guild.id][date] or self.model.db[ctx.guild.id][date][emoji_id].instance_count == 0:
                #     print('\tSKIP')
                #     continue

                temp_db[emoji_id]['count'].append(self.model.db[ctx.guild.id][date][emoji_id].instance_count)
                temp_db[emoji_id]['date'].append(date)
                url.append(str(self.model.db[ctx.guild.id][date][emoji_id].emoji_obj.url))
            print()
        print(temp_db)

        for emoji, db_content in temp_db.items():
            if legend_countr < MAX_LEGEND_COUNT:
                line, = plt.plot(db_content['date'], db_content['count'], marker='.',
                                 label=' - ' + ctx.bot.get_emoji(emoji).name)
            else:
                line, = plt.plot(db_content['date'], db_content['count'], marker='.')
            lines.append(line)
            legend_countr += 1

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

        # makes columns of size 10
        # plt.legend(handler_map=legend_obj, ncol=math.ceil(len(lines) / 10))
        plt.legend(handler_map=legend_obj)  # legend

        plt.grid(True)  # grid lines
        plt.title("Time series of emote use in " + ctx.guild.name)  # title
        plt.xticks(ticks=dates)  # display only given dates

        fig = plt.gcf()
        fig.autofmt_xdate()  # might delete
        plt.show()
        plt.draw()
        fig.savefig('graph.png', bbox_inches='tight')
        await ctx.send(file=discord.File('graph.png'))

    def sort(self, ctx, sort_type):
        """
        Creates a sorted copy of the data of the latest date as a list
        @param ctx: Discord context
        @param sort_type: string sorting type: 'instance', 'total', 'alpha'
        @return: list (id, EmojiStat)
        """
        # sort by instance_count descending order
        if sort_type == 'instance':
            last_date = list(self.model.db[ctx.guild.id])[-1]
            dict_emojis = {}

            for x, y in self.model.db[ctx.guild.id][last_date].items():
                dict_emojis[x] = y
            # sort by instance count into list: (id, EmojiStat)
            sorted_emojis = sorted(dict_emojis.items(),
                                   key=lambda kv: getattr(kv[1], 'instance_count'),
                                   reverse=True)
            return sorted_emojis
        # sort by total_count descending order
        elif sort_type == 'total':
            last_date = list(self.model.db[ctx.guild.id])[-1]
            dict_emojis = {}

            for x, y in self.model.db[ctx.guild.id][last_date].items():
                dict_emojis[x] = y
            # sort by instance count into list: (id, EmojiStat)
            sorted_emojis = sorted(dict_emojis.items(),
                                   key=lambda kv: getattr(kv[1], 'total_count'),
                                   reverse=True)
            return sorted_emojis
        # todo: create alphabetical sort
        # sort by emoji's name alphabetical order
        elif sort_type == 'alpha':
            pass


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
