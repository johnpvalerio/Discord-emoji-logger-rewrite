import json
import re

from discord.ext import commands
import EmojiStat
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


class Model(commands.Cog):

    def __init__(self, bot):
        self.db = {}
        self.bot = bot
        print('Model ON')

    @commands.Cog.listener()
    async def on_ready(self):
        cred = credentials.Certificate('firebase_admin.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://discord-emoji-stat.firebaseio.com/'})
        ref = db.reference('')
        self.db = self.fix_db(ref.get())

        # if empty
        if self.db == {}:
            for guild in self.bot.guilds:
                self.db[guild.id] = {}
                await self.prepare_db(guild.id)
        print(self.db)
        print('Ready')

    # def prepare_db(self, guild_ID, date_list = None):
    async def prepare_db(self, guild_ID, start_date= None):
        # start from beginning
        if start_date is None:
            date_list = await self.next_dates(self.bot.get_guild(guild_ID).created_at)
        else:
            date_list = await self.next_dates(start_date)
            # ignore first entry (last processed date)
            date_list = date_list[1:]
        for date in date_list:
            server_emoji = await self.compile_emoji(guild_ID)
            self.db[guild_ID][date] = server_emoji

    async def log_channel(self, channel, start_date=None):
        date_list = []
        if start_date is None:
            start_date = channel.created_at
        for date in self.db[channel.guild.id]:
            date_list.append(date)
        await self.log_emoji(channel, start_date, datetime.datetime.now(), date_list)
        print(channel)

    # date_list might be able to mitigate it?
    # compile emoji in all channels between given dates
    async def log_emoji(self, channel, date_after, date_stop, date_list):
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
            next_dates.append(date_list[i])
        for date in next_dates:
            self.db[channel_id][date][emoji_ID].instance_count += inst_inc
            self.db[channel_id][date][emoji_ID].total_count += total_inc

    async def next_dates(self, start_date):
        """
        Creates list of dates not yet processed, from last entered to now
        @param start_date: starting datetime date
        @return: list of datetime
        """
        date_list = []

        # set dates from start to now
        while start_date < datetime.datetime.now():
            start_date = self.format_date(start_date)
            date_list.append(start_date)
        return date_list

    def format_date(self, date):
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1)
        else:
            return date.replace(month=date.month + 1)

    async def compile_emoji(self, guild_ID):
        emojis = self.bot.get_guild(guild_ID).emojis
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
                temp_db[guild_ID][date.strftime('%Y-%m-%d %H:%M:%S')] = self.db[guild_ID][date]
        # print(temp_db)
        with open('emoji-data.json', 'w', encoding='utf-8') as write_file:
            json.dump(temp_db, write_file, indent=2, default=encoder_json)

    def fix_db(self, database):
        """
        Converts FireBase file content into proper manageable objects (datetime & EmojiStat)
        @param database: Dictionary FireBase content
        @return: Dictionary of FireBase content into proper objects
        """
        temp_db = {}
        for guild in database:
            temp_date = {}
            for date in database[guild]:
                temp_emoji = {}
                for emoji_ID in database[guild][date]:
                    emoji_val = []
                    for word, val in database[guild][date][emoji_ID].items():
                        emoji_val.append(val)
                    temp_emoji[int(emoji_ID)] = EmojiStat.EmojiStat(self.bot.get_emoji(int(emoji_ID)), emoji_val[0],
                                                                    emoji_val[1])
                date_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                temp_date[date_obj] = temp_emoji
            temp_db[int(guild)] = temp_date

        return temp_db


def encoder_json(file_object):
    print(str(file_object), ' - ', type(file_object))
    if isinstance(file_object, EmojiStat.EmojiStat):
        return {'instance_count': file_object.instance_count, 'total_count': file_object.total_count}
    if isinstance(file_object, datetime.datetime):
        return file_object.__str__()
    return None
