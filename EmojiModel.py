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
        print(self.db)
        print('Model ON')

    @commands.Cog.listener()
    async def on_ready(self):
        # todo: remove (kept to remember compile_dates use)

        # for guild in self.bot.guilds:
        #     self.db[guild.id] = {}
        #     print('guild: ', type(guild.id))
        #     date_list = await self.compile_dates(guild)
        #     for date in date_list:
        #         print(type(date))
        #         server_emoji = await self.compile_emoji()
        #         self.db[guild.id][date] = server_emoji

        # todo: update dates to be datetime type, update emoji values to be emoji_object type
        cred = credentials.Certificate('firebase_admin.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://discord-emoji-stat.firebaseio.com/'
        })
        ref = db.reference('')
        self.db = self.fix_db(ref.get())
        print(self.db)
        print('Ready')

    async def log_channel(self, channel):
        date_list = []
        for date in self.db[channel.guild.id]:
            date_list.append(date)
        await self.log_emoji(channel, channel.created_at, datetime.datetime.now(), date_list)
        print(channel)

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

    # creates list of dates not yet filled
    async def compile_dates(self, guild, cur_date):
        date_list = []
        if cur_date is None:
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
            print('id: ', type(current_emoji.id))
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
        temp_db = {}
        emoji_val = []
        for guild in database:
            print('guild:',guild)
            temp_date = {}
            for date in database[guild]:
                print('\tdate:', date)
                temp_emoji = {}
                for emoji_ID in database[guild][date]:
                    emoji_val = []
                    print('\t\temoji ID:', emoji_ID)
                    for word, val in database[guild][date][emoji_ID].items():
                        emoji_val.append(val)
                    temp_emoji[int(emoji_ID)] = EmojiStat.EmojiStat(self.bot.get_emoji(int(emoji_ID)), emoji_val[0], emoji_val[1])
                date_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                temp_date[date_obj] = temp_emoji
            temp_db[int(guild)] = temp_date

        return temp_db


def encoder_json(file_object):
    print(str(file_object), ' - ', type(file_object))
    if isinstance(file_object, EmojiStat.EmojiStat):
        # return file_object.instance_count, file_object.total_count
        return {'instance_count': file_object.instance_count, 'total_count': file_object.total_count}
    if isinstance(file_object, datetime.datetime):
        return file_object.__str__()
    return None
