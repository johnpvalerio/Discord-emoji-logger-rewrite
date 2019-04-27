import json
import re

from discord.ext import commands
import EmojiStat
import datetime


class Model(commands.Cog):
    def __init__(self, bot):
        self.db = {}
        self.bot = bot
        print('Model ON')

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.db[guild.id] = {}
            date_list = await self.compile_dates(guild)
            for date in date_list:
                # print(type(date))
                server_emoji = await self.compile_emoji()
                # self.db[guild.id][date.strftime('%Y-%m-%d %H:%M:%S.%f')] = server_emoji
                self.db[guild.id][date] = server_emoji
        print(self.db)
        print('Ready')

    async def log_channel(self, channel):
        date_list = []
        print('created: ', channel.guild.created_at)
        for date in self.db[channel.guild.id]:
            date_list.append(date)
        # print(date_list)
        await self.log_emoji(channel, channel.created_at, datetime.datetime.now(), date_list)
        print(channel)

    # update current with last: [ ]
    # current date: > <
    async def log_emoji(self, channel, date_after, date_stop, date_list):
        print(channel.name)
        date_index = 0
        date_max_index = len(date_list) - 1
        async for message in channel.history(limit=None, before=date_stop, after=date_after):

            # move date to next closest
            while message.created_at >= date_list[date_index]:
                date_index = date_index + 1
                if date_max_index == date_index:
                    return
            # skip if message from the bot
            if message.author.bot:
                continue

            # find emojis
            emoji_found = re.findall(r'<a?:\w*:\d*>', message.content)

            # skip if no emojis found
            if not emoji_found:
                continue

            # remove emojis not from guild
            emoji_found = list(
                filter(lambda emoji:
                       emoji in list(str(emoji_server)
                                     for emoji_server in channel.guild.emojis
                                     if not emoji_server.managed),
                       emoji_found))

            # update emoji counts
            for emoji in set(emoji_found):
                emoji_count = emoji_found.count(emoji)
                self.update_data(channel_id=channel.guild.id, date_index=date_index, date_list=date_list,
                                 emoji_ID=int(emoji[-19:-1]), inst_inc=1, total_inc=emoji_count)

    # update stats for given emoji in upcoming dates
    def update_data(self, channel_id, date_index, date_list, emoji_ID, inst_inc, total_inc):
        next_dates = []
        for i in range(date_index, len(date_list)):
            print('\t\t',i)
            next_dates.append(date_list[i])
        for date in next_dates:
            print(date)
            self.db[channel_id][date][emoji_ID].instance_count += inst_inc
            self.db[channel_id][date][emoji_ID].total_count += total_inc

    async def compile_dates(self, guild):
        date_list = []
        cur_date = guild.created_at
        cur_date = cur_date.replace(month=cur_date.month + 1, day=1)
        while cur_date < datetime.datetime.now():
            date_list.append(cur_date)
            if cur_date.month == 12:
                cur_date = cur_date.replace(year=cur_date.year + 1, month=1)
            else:
                cur_date = cur_date.replace(month=cur_date.month + 1)
        return date_list

    async def compile_emoji(self):
        emojis = self.bot.emojis
        emoji_dict = {}
        for current_emoji in emojis:
            emoji_dict[current_emoji.id] = EmojiStat.EmojiStat(current_emoji)
        return emoji_dict

    def export(self):
        print('Saving JSON file...')
        temp_db = {}
        for guild_ID, date_key in self.db.items():
            temp_db[guild_ID] = {}
            for date in self.db[guild_ID]:
                temp_db[guild_ID][date.strftime('%Y-%m-%d %H:%M:%S.%f')] = self.db[guild_ID][date]
        # print(temp_db)
        with open('emoji_data.json', 'w') as write_file:
            json.dump(temp_db, write_file, indent=4, default=encoder_json)


def encoder_json(file_object):
    print(str(file_object), ' - ', type(file_object))
    if isinstance(file_object, EmojiStat.EmojiStat):
        return file_object.instance_count, file_object.total_count
    if isinstance(file_object, datetime.datetime):
        return file_object.__str__()
    return None
