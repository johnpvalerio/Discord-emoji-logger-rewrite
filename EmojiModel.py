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
        print(channel)
        date_list = []
        print('created: ', channel.guild.created_at)
        for date in self.db[channel.guild.id]:
            date_list.append(date)
        print(date_list)
        await self.log_emoji(channel, channel.created_at, datetime.datetime.now(), date_list)
        # self.log_emoji(channel, date_after, date_stop)

    async def log_emoji(self, channel, date_after, date_stop, date_list):
        print(channel.name)
        date_index = 0
        date_max_index = len(date_list) - 1
        # print(date_max_index)
        async for message in channel.history(limit=None, before=date_stop, after=date_after):

            # print('\t\tmsg date: ', message.created_at, ' - current date: ', date_list[date_index])
            while message.created_at > date_list[date_index]:
                if date_max_index == date_index:
                    return
                date_index = date_index + 1
                for guild_ID, val in self.db.items():
                    for date, val2 in self.db[guild_ID].items():
                        for emoji_ID, emoji_obj in self.db[guild_ID][date].items():
                            if self.db[guild_ID][date_list[date_index]][emoji_ID].instance_count < self.db[guild_ID][date_list[date_index-1]][emoji_ID].instance_count:
                                self.db[guild_ID][date_list[date_index]][emoji_ID].instance_count = self.db[guild_ID][date_list[date_index-1]][emoji_ID].instance_count
                            if self.db[guild_ID][date_list[date_index]][emoji_ID].instance_increase < self.db[guild_ID][date_list[date_index-1]][emoji_ID].instance_increase:
                                self.db[guild_ID][date_list[date_index]][emoji_ID].instance_increase = self.db[guild_ID][date_list[date_index-1]][emoji_ID].instance_increase
                            if self.db[guild_ID][date_list[date_index]][emoji_ID].total_count < self.db[guild_ID][date_list[date_index-1]][emoji_ID].total_count:
                                self.db[guild_ID][date_list[date_index]][emoji_ID].total_count = self.db[guild_ID][date_list[date_index-1]][emoji_ID].total_count
                            if self.db[guild_ID][date_list[date_index]][emoji_ID].total_increase < self.db[guild_ID][date_list[date_index-1]][emoji_ID].total_increase:
                                self.db[guild_ID][date_list[date_index]][emoji_ID].total_increase = self.db[guild_ID][date_list[date_index-1]][emoji_ID].total_increase

            # skip if message from the bot
            if message.author == self.bot.user:
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
                # print(emoji)
                emoji_count = emoji_found.count(emoji)

                self.db[channel.guild.id][date_list[date_index]][int(emoji[-19:-1])].instance_count += 1
                self.db[channel.guild.id][date_list[date_index]][int(emoji[-19:-1])].instance_increase += 1

                self.db[channel.guild.id][date_list[date_index]][int(emoji[-19:-1])].total_count += emoji_count
                self.db[channel.guild.id][date_list[date_index]][int(emoji[-19:-1])].total_increase += emoji_count

        for guild_ID, val in self.db.items():
            for date, val2 in self.db[guild_ID].items():
                for emoji_ID, emoji_obj in self.db[guild_ID][date].items():
                    print('\t', emoji_obj.emoji_obj.name, ': ', emoji_obj.instance_count, ' - ', emoji_obj.total_count)
                print('\t\t - - - -')
                print(date)
        print('\t\t . . . . . . .')

    async def compile_emoji(self):
        emojis = self.bot.emojis
        emoji_dict = {}
        for current_emoji in emojis:
            emoji_dict[current_emoji.id] = EmojiStat.EmojiStat(current_emoji)
        return emoji_dict

    async def compile_dates(self, guild):
        date_list = []
        cur_date = guild.created_at
        cur_date = cur_date.replace(month=cur_date.month + 1, day=1)
        # print(cur_date)

        while cur_date < datetime.datetime.now():
            date_list.append(cur_date)
            if cur_date.month == 12:
                cur_date = cur_date.replace(year=cur_date.year + 1, month=1)
            else:
                cur_date = cur_date.replace(month=cur_date.month + 1)
        return date_list

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

