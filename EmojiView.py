import aiofiles as aiofiles
import aiohttp
import discord
import matplotlib.lines
import matplotlib.pyplot as plt
from discord.ext import commands
from matplotlib.image import BboxImage
from matplotlib.legend_handler import HandlerBase
from matplotlib.transforms import Bbox, TransformedBbox


def bottom_calc(list_items):
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
            print(date)
            for emoji_ID, emoji_obj in self.model.db[ctx.guild.id][date].items():
                print('\t', emoji_obj.emoji_obj.name, ': ', emoji_obj.instance_count, ' - ', emoji_obj.total_count)
            print('\t\t - - - -')
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
        # sort by instance count into list: (id, EmojiStat)
        sorted_emojis = self.sort(ctx, 'instance')
        await self.embed(ctx, sorted_emojis)

    # todo: more info like % increase, date, etc
    async def embed(self, ctx, msg):
        if type(msg) is list:
            output = ''
            embed = discord.Embed(title=ctx.guild.name + '\'s emoji stats')
            for i in range(len(msg)):
                emoji = msg[i]
                emoji_id = msg[i].emoji_obj.id
                last_date = list(self.model.db[ctx.guild.id])[-1]
                prior_date = list(self.model.db[ctx.guild.id])[-2]
                date_used = emoji.last_used
                inst_increase = emoji.instance_count - self.model.db[ctx.guild.id][prior_date][emoji_id].instance_count
                total_increase = emoji.total_count - self.model.db[ctx.guild.id][prior_date][emoji_id].total_count

                output += str(emoji.emoji_obj) + ' : ' + \
                          str(emoji.instance_count) + ' [ ' + str(inst_increase) + '↑] - ' + \
                          str(emoji.total_count) + ' [ ' + str(total_increase) + '↑]    (last used: ' + \
                          str(date_used) + ')\n'

                if i % 5 == 4:
                    embed.add_field(name=str(i - 3) + ' - ' + str(i + 1), value=output, inline=False)
                    output = ''
            if output is not '':
                embed.add_field(name=str(len(msg) - (len(msg) % 5) + 1) + ' - ' + str(len(msg)), value=output,
                                inline=False)
            embed.set_footer(text=str(prior_date) + ' to ' + str(last_date))
        else:
            embed = discord.Embed(title='Untitled')
            embed.add_field(name='Field 1', value=msg)
        await ctx.send(embed=embed)

    async def bar(self, ctx, sort_type='instance'):
        list_names = []  # x tick labels
        list_vals = []  # y values
        list_legend = []  # legend values
        temp = []  # list_vals temporary container
        width = 0.3  # bar width size
        y_max = 100  # y delimiter
        counter = 0  # legend counter

        last_date = list(self.model.db[ctx.guild.id])[-1]  # latest date
        reverse_dates = reversed(list(self.model.db[ctx.guild.id]))  # dates for stacks
        emote_size = len(self.model.db[ctx.guild.id][last_date])  # number of emojis
        ind = [x for x in range(emote_size)]  # list of ints to space graph

        # set emote font size
        if emote_size >= 70:
            text_size = 5
        elif emote_size >= 50:
            text_size = 6
        elif emote_size >= 30:
            text_size = 8
        else:
            text_size = 12

        # sort by desired type
        sorted_emojis = self.sort(ctx, sort_type)

        # add emoji names, x - values
        for emoji in sorted_emojis:
            list_names.append(emoji.emoji_obj.name)
            if y_max < emoji.instance_count:
                y_max = emoji.instance_count
        # add frequency, y - values
        for date in reverse_dates:
            for emoji in sorted_emojis:
                try:
                    if sort_type == 'instance':
                        temp.append(self.model.db[ctx.guild.id][date][emoji.emoji_obj.id].instance_count)
                    elif sort_type == 'total':
                        temp.append(self.model.db[ctx.guild.id][date][emoji.emoji_obj.id].total_count)
                    else:
                        temp.append(self.model.db[ctx.guild.id][date][emoji.emoji_obj.id].instance_count)
                # if no entry at that date, add 0
                except KeyError:
                    temp.append(0)
            list_vals.append(temp)
            temp = []
            # add dates to legend, 5 entries
            if counter < 5:
                list_legend.append(date)
                counter += 1
        # add values into bar graph
        for i in range(len(list_vals)):
            plt.bar(ind, list_vals[i], width)

        plt.ylim([0, y_max + 10])  # y upper limit
        plt.xticks(ind, list_names, fontsize=text_size, rotation=90)  # x tick title values
        plt.xlabel('Emoji')  # x label
        plt.ylabel('Single instance count')  # y label
        plt.title("Bar graph of emote use in " + ctx.guild.name)  # title
        plt.legend(list_legend, loc=0)  # legend
        
        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('graph.png', bbox_inches='tight')
        await ctx.send(file=discord.File('graph.png'))

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
        dates = dates[-MAX_DATES:]

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
        @return: list (EmojiStat)
        """
        last_date = list(self.model.db[ctx.guild.id])[-1]
        list_emojis = []
        for x, y in self.model.db[ctx.guild.id][last_date].items():
            list_emojis.append(y)

        # sort by instance count into list: EmojiStat
        if sort_type == 'instance':
            sorted_emojis = sorted(list_emojis,
                                   key=lambda kv: getattr(kv, 'instance_count'),
                                   reverse=True)
        # sort by total_count descending order
        elif sort_type == 'total':
            # sort by instance count into list: (id, EmojiStat)
            sorted_emojis = sorted(list_emojis,
                                   key=lambda kv: getattr(kv, 'total_count'),
                                   reverse=True)
        # sort by emoji's name alphabetical order
        elif sort_type == 'alpha':
            sorted_emojis = sorted(list_emojis,
                                   key=lambda kv: getattr(kv.emoji_obj, 'name'),
                                   reverse=False)
        # default to sorting by instance
        else:
            sorted_emojis = sorted(list_emojis,
                                   key=lambda kv: getattr(kv, 'instance_count'),
                                   reverse=True)
        return sorted_emojis


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
