import asyncio
import logging
from datetime import datetime

import aiofiles
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


def perc(val, total):
    if total == 0:
        return 0
    return round(val / total * 100, 2)


def format_value(emoji, count, total):
    return str(emoji.emoji_obj) + ': **' + str(count) + '** (' + str(perc(count, total)) + '%) | ' + \
           emoji.emoji_obj.created_at.strftime('%Y-%m-%d') + \
           ' (' + str((datetime.now() - emoji.emoji_obj.created_at).days) + ' days)'


class View(commands.Cog):
    def __init__(self, model, bot):
        self.model = model
        self.bot = bot
        self.logger = logging.getLogger('bot_logs')
        self.logger.info('View ON')

    async def print(self, ctx, msg):
        """
        Sends string message to discord user
        @param ctx: Discord context
        @param msg: string message
        @return: None
        """
        await ctx.send(msg)

    async def db(self, ctx):
        """
        Prints all contents of data values ordered by dates
        @param ctx: Discord context
        @return: None
        """
        for date, val2 in self.model.db[ctx.guild.id].items():
            print(date)
            for emoji_ID, emoji_obj in self.model.db[ctx.guild.id][date].items():
                print('\t', emoji_obj.emoji_obj.name, ': ', emoji_obj.instance_count, ' - ', emoji_obj.total_count)
            print('\t\t - - - -')
        await ctx.send('complete')

    # todo: overlap problems
    async def pie(self, ctx, sort_type="instance_count"):
        """
        Create and display a pie chart of latest emoji stats
        @param sort_type: String of type (instance, total)
        @param ctx: discord context
        @return: None
        """
        labels = []
        values = []

        # sort into list
        sorted_emojis = self.emoji_sort(ctx, sort_type, list(self.model.db[ctx.guild.id])[-1])

        # add labels and values
        for emoji in sorted_emojis:
            emote, count = emoji
            labels.append(emote.emoji_obj.name)  # emoji name
            values.append(count)  # emoji frequency

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.axis('equal')
        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('resources/pie.png')
        await ctx.send(file=discord.File('resources/pie.png'))

    async def bar(self, ctx, sort_type='instance_count', is_delta=False):
        """
        Creates and sends bar graph of data in descending order
        @param is_delta: Boolean for frequency change option
        @param ctx: Discord context
        @param sort_type: String of type (instance, total)
        @return: None
        """
        list_names = []  # x tick labels
        list_vals = []  # y values
        list_legend = []  # legend values
        temp = []  # list_vals temporary container
        WIDTH = 0.3  # bar width size
        Y_MAX = 50  # y delimiter
        is_over_max = False
        counter = 0  # legend counter
        NB_ENTRIES = 5  # nb of date entries

        curr_date = list(self.model.db[ctx.guild.id])[-1]  # latest date
        emote_size = len(self.model.db[ctx.guild.id][curr_date])  # number of emojis
        ind = [x for x in range(emote_size)]  # list of ints to space graph

        # switch for delta option
        if is_delta:
            reverse_dates = [curr_date]
            past_date = list(self.model.db[ctx.guild.id])[-2]
            sorted_emojis = self.emoji_sort(ctx, sort_type, curr_date, past_date)

        else:
            reverse_dates = reversed(list(self.model.db[ctx.guild.id]))  # dates for stacks
            sorted_emojis = self.emoji_sort(ctx, sort_type, curr_date)

        # set emote font size
        if emote_size >= 70:
            text_size = 5
        elif emote_size >= 50:
            text_size = 6
        elif emote_size >= 30:
            text_size = 8
        else:
            text_size = 12

        # add emoji names, x - values
        for emoji in sorted_emojis:
            emote, count = emoji
            # list_names.append(emoji[1])
            list_names.append(emote.emoji_obj.name)
            if Y_MAX < count:
                Y_MAX = count
        # add frequency, y - values
        for date in reverse_dates:
            for emoji in sorted_emojis:
                emote, count = emoji
                try:
                    if is_delta:
                        temp.append(count)
                    else:
                        temp.append(getattr(self.model.db[ctx.guild.id][date][emote.emoji_obj.name], sort_type))
                    if temp[-1] > Y_MAX:
                        is_over_max = True
                # if no entry at that date, add 0
                # e is the name of the emoji
                except KeyError as e:
                    temp.append(0)
            # add dates to legend, 5 entries
            if counter < NB_ENTRIES:
                list_legend.append(date.strftime('%Y-%m-%d'))
                list_vals.append(temp)
                temp = []
                counter += 1

        if not is_delta:
            # formats bar values such that only latest values are applied and not overwritten by old ones
            for list_index in reversed(range(len(list_vals))):
                for entry_index in range(len(list_vals[list_index])):
                    if list_vals[list_index][entry_index] == list_vals[list_index - 1][entry_index]:
                        list_vals[list_index][entry_index] = 0
        # add values into bar graph
        for i in range(len(list_vals)):
            plt.bar(ind, list_vals[i], WIDTH, bottom=0)

        if is_over_max:
            plt.ylim([0, Y_MAX + 10])  # y upper limit
        plt.xticks(ind, list_names, fontsize=text_size, rotation=90)  # x tick title values
        plt.xlabel('Emoji')  # x label
        plt.ylabel(sort_type)  # y label
        plt.title("Bar graph of emote use in " + ctx.guild.name)  # title
        plt.legend(list_legend, loc=0)  # legend

        fig = plt.gcf()
        plt.show()
        plt.draw()
        fig.savefig('resources/graph.png', bbox_inches='tight', dpi=900)
        await ctx.send(file=discord.File('resources/graph.png'))

    async def graph(self, ctx):
        """
        Creates and sends line graph of data values
        @param ctx: Discord context
        @return: None
        note: note: matplotlib creates x axis if not enough/too little distance from start/end
        """
        dates = []  # dates
        url = []  # emoji URL
        lines = []  # graph lines
        img = []
        temp_db = {}
        legend_counter = 0
        MAX_LEGEND_COUNT = 10
        MAX_DATES = 5

        # last 3 dates
        for date in self.model.db[ctx.guild.id]:
            dates.append(date)
        dates = dates[-MAX_DATES:]

        # temp_db holds list of date & instance count keyed by emoji ID
        for date in dates:
            print(date)
            for emoji_id in self.model.db[ctx.guild.id][date]:
                # if emoji not yet processed
                if emoji_id not in temp_db.keys():
                    temp_db[emoji_id] = {'date': [], 'count': []}
                print(emoji_id, ' - ', self.model.db[ctx.guild.id][date][emoji_id].instance_count)

                temp_db[emoji_id]['count'].append(self.model.db[ctx.guild.id][date][emoji_id].instance_count)
                temp_db[emoji_id]['date'].append(date)
                url.append(str(self.model.db[ctx.guild.id][date][emoji_id].emoji_obj.url))
            print()
        print(temp_db)

        for emoji, db_content in temp_db.items():
            if legend_counter < MAX_LEGEND_COUNT:
                line, = plt.plot(db_content['date'], db_content['count'], marker='.',
                                 label=' - ' + ctx.bot.get_emoji(emoji).name)
            else:
                line, = plt.plot(db_content['date'], db_content['count'], marker='.')
            lines.append(line)
            legend_counter += 1

        # adding images in the legend
        for i in range(len(url)):
            async with aiohttp.ClientSession() as session:
                url_link = url[i]
                async with session.get(url_link) as resp:
                    if resp.status == 200:
                        f = await aiofiles.open('resources/emoji.png', mode='wb')
                        await f.write(await resp.read())
                        await f.close()
                        img.append(HandlerLineImage('resources/emoji.png'))
        legend_obj = dict(zip(lines, img))

        plt.legend(handler_map=legend_obj)  # legend

        plt.grid(True)  # grid lines
        plt.title("Time series of emote use in " + ctx.guild.name)  # title
        plt.xticks(ticks=dates)  # display only given dates

        fig = plt.gcf()
        fig.autofmt_xdate()  # might delete
        plt.show()
        plt.draw()
        fig.savefig('resources/graph.png', bbox_inches='tight')
        await ctx.send(file=discord.File('resources/graph.png'))

    def emoji_sort(self, ctx, sort_type, cur_date, old_date=None):
        """
        Sorts db entries at given date by sort type
        @param ctx: Discord context
        @param sort_type: String "instance_count", "total_count"
        @param cur_date: Datetime of latest date
        @param old_date: Datetime of past date
        @return: list (Emoji object, count)
        """
        sorted_emojis = []
        cur_emojis = self.model.db[ctx.guild.id][cur_date]
        for emoji in cur_emojis.values():
            if old_date is not None:
                sorted_emojis.append((emoji, getattr(emoji, sort_type) -
                                      getattr(self.model.db[ctx.guild.id][old_date][emoji.emoji_obj.id], sort_type)))
            else:
                sorted_emojis.append((emoji, getattr(emoji, sort_type)))
        sorted_emojis = sorted(sorted_emojis, key=lambda kv: kv[1], reverse=True)
        return sorted_emojis

    async def table(self, ctx, sort_type='instance_count', page=0, msg=None):
        """
        Creates an embed of emoji info then sends it
        waits for emoji reaction response to change page
        @param sort_type: String "instance_count", "total_count"
        @param ctx: Discord context object
        @param page: page to display
        @param msg: Discord Message object for page switching - edit if present
                    None - no Message object made
        @return: None
        """
        PAGE_LEN = 10  # how many total entries from all groups
        GROUP_LEN = 5  # how many entries per group
        TIMEOUT_WAIT = 10  # timer for how long to wait for reaction

        sorted_emojis = self.emoji_sort(ctx, sort_type, list(self.model.db[ctx.guild.id])[-1])
        total_count = sum([x[1] for x in sorted_emojis])

        def embed_maker(_page=0):
            """
            Creates a Discord embed object
            Formats as a table with number of entries given
            @param _page: Int current page
            @return: Discord embed object
            """
            val = ''

            embed = discord.Embed(title=ctx.guild.name + '\'s emoji stats')
            embed.set_thumbnail(url=str(ctx.guild.icon_url))
            embed.set_footer(text='page ' + str(_page + 1) + '/ ' + str(int(len(sorted_emojis) / PAGE_LEN) + 1))

            MAX_RANGE = PAGE_LEN \
                if (PAGE_LEN * int(_page) + PAGE_LEN <= len(sorted_emojis)) \
                else len(sorted_emojis) - PAGE_LEN * int(_page)

            if MAX_RANGE < 0 or _page < 0:
                return

            for i in range(MAX_RANGE):
                emoji, count = sorted_emojis[i + int(_page) * PAGE_LEN]  # get emoji and count info

                val += format_value(emoji, count, total_count) + '\n'  # get value to display
                if i % GROUP_LEN != GROUP_LEN - 1 and \
                        i != MAX_RANGE - 1:  # keep going until GROUP_LEN number of entries per field
                    continue  # or last entry

                # add into field
                str_title = str(i + 1 - i % GROUP_LEN + int(_page) * PAGE_LEN) + '-' + str(
                    i + 1 + int(_page) * PAGE_LEN)
                embed.add_field(name=str_title, value=val, inline=False)
                val = ''
            return embed

        # send new embed message
        if msg is None:
            msg = await ctx.send(embed=embed_maker(page))
        # edit current embed message
        else:
            await msg.edit(embed=embed_maker(page))

        # add reaction buttons
        if page != 0:
            await msg.add_reaction('\u23ea')  # <<
        if page != int(len(sorted_emojis) / PAGE_LEN):
            await msg.add_reaction('\u23e9')  # >>

        async def clear():
            """
            removes all reactions
            @return: None
            """
            await msg.clear_reactions()

        # waiting for reaction << or >>
        def react(reaction_, user_):
            return (str(reaction_.emoji) == '\u23ea' or str(reaction_.emoji) == '\u23e9') and user_ == ctx.author

        # get reaction
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=TIMEOUT_WAIT, check=react)
        except asyncio.TimeoutError:  # false - no valid emoji [<<, >>]
            await clear()
        else:  # true
            await clear()
            if reaction.emoji == u'\u23ea':  # next page
                await self.table(ctx, sort_type, page - 1, msg)
            elif reaction.emoji == u'\u23e9':  # previous page
                await self.table(ctx, sort_type, page + 1, msg)


class HandlerLineImage(HandlerBase):

    def __init__(self, path, space=15, offset=10):
        self.space = space
        self.offset = offset
        self.image_data = plt.imread(path, -1)
        super(HandlerLineImage, self).__init__()

    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):
        line = matplotlib.lines.Line2D([xdescent + self.offset, xdescent + (width - self.space) / 3. + self.offset],
                                       [ydescent + height / 2., ydescent + height / 2.])
        line.update_from(orig_handle)
        line.set_clip_on(False)
        line.set_transform(trans)

        bb = Bbox.from_bounds(xdescent + (width + self.space) / 3. + self.offset,
                              ydescent,
                              height * self.image_data.shape[1] / self.image_data.shape[0],
                              height)

        tbb = TransformedBbox(bb, trans)
        image = BboxImage(tbb)
        image.set_data(self.image_data)

        self.update_prop(image, orig_handle, legend)
        return [line, image]
