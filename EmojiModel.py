import datetime
import json
import re

import firebase_admin
from discord.ext import commands
from firebase_admin import credentials
from firebase_admin import db

import EmojiStat


def format_date(date):
    """
    Format date as first of every month
    @param date: datetime target date
    @return: datetime formatted
    """
    if date.month == 12:
        print('12')
        # return date.replace(year=date.year + 1, month=1, day=1)
        return date.replace(year=date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        print('add')
        # return date.replace(month=date.month + 1, day=1)
        return date.replace(month=date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def next_dates(start_date):
    """
    Creates list of dates not yet processed, from last entered to now
    @param start_date: starting datetime date
    @return: list of datetime
    """
    date_list = []
    # set dates from start to now
    while start_date < datetime.datetime.now():
        print('\t', start_date)
        start_date = format_date(start_date)
        print('now: ', datetime.datetime.now(), ' - current: ', start_date)
        date_list.append(start_date)

    print(date_list[:-1])
    return date_list[:-1]


class Model(commands.Cog):

    def __init__(self, bot):
        self.db = {}
        self.bot = bot
        print('Model ON')

    @commands.Cog.listener()
    async def on_ready(self):
        """
        sets up database on initialization
        @return: None
        """
        cred = credentials.Certificate('configs/firebase_admin.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://discord-emoji-stat.firebaseio.com/'})
        ref = db.reference('')

        if ref.get() is not None:
            self.db = self.fix_db(ref.get())

        for guild in self.bot.guilds:
            # new database or new guild
            if self.db == {} or guild.id not in self.db:
                await self.new_db(guild.id)

        print(self.db)
        print('Ready')

    async def new_db(self, guild_id):
        """
        creates new guild entry in database
        @param guild_id: int guild ID
        @return: None
        """
        # self.db[guild_id].clear()
        self.db[guild_id] = {}
        await self.prepare_db(guild_id)

    # note: emoji dates added isnt reflected in data logged
    async def prepare_db(self, guild_ID, start_date=None):
        """
        Sets database db to contain date & server emojis
        @param guild_ID: server guild ID integer
        @param start_date: starting date to initialize datetime
        @return: None
        """
        # start from beginning
        if start_date is None:
            date_list = next_dates(self.bot.get_guild(guild_ID).created_at)
        # start from date given
        else:
            date_list = next_dates(start_date)
        # add emojis
        for date in date_list:
            self.db[guild_ID][date] = await self.compile_emoji(guild_ID)

    async def log_channel(self, channel, start_date=None):
        """
        Main channel logging driver, sets up dates to use
        @param channel: Discordpy channel target channel
        @param start_date: datetime start date
        @return: None
        """
        date_list = []
        # default, start date from channel creation
        if start_date is None:
            start_date = channel.created_at
        # make list of dates
        for date in self.db[channel.guild.id]:
            date_list.append(date)
        print('\n', channel)
        # log emoji for channel
        await self.log_emoji(channel=channel, date_after=start_date,
                             date_stop=datetime.datetime.now(), date_list=date_list)

    # compile emoji in all channels between given dates
    async def log_emoji(self, channel, date_after, date_stop, date_list):
        """
        Compile emojis in given channel between given dates
        @param channel: Discordpy channel target channel
        @param date_after: datetime date target after date
        @param date_stop: datetime date target stop date
        @param date_list: datetime list of dates to go through
        @return: None
        """
        date_index = 0
        date_max_index = len(date_list) - 1
        # go through channel history
        async for message in channel.history(limit=None, before=date_stop, after=date_after):
            # move date to next closest
            while message.created_at >= date_list[date_index]:
                date_index = date_index + 1

                if date_index > date_max_index:
                    # print('STOP')
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

            if not emoji_found:
                continue

            # update emoji counts
            for emoji in set(emoji_found):
                emoji_count = emoji_found.count(emoji)
                self.update_data(guild_id=channel.guild.id, date_list=date_list[date_index:],
                                 emoji_id=int(emoji[-19:-1]), inst_inc=1, total_inc=emoji_count,
                                 date_used=message.created_at)

    def update_data(self, guild_id, date_list, emoji_id, inst_inc, total_inc, date_used):
        """
        update stats for given emoji in upcoming dates
        @param guild_id: int guild ID
        @param date_list: datetime list of all datetime to go through
        @param emoji_id: int emoji ID
        @param inst_inc: int instance count increase (default 1)
        @param total_inc: int total count increase
        @return: None
        """
        for date in date_list:
            self.db[guild_id][date][emoji_id].instance_count += inst_inc
            self.db[guild_id][date][emoji_id].total_count += total_inc
            self.db[guild_id][date][emoji_id].last_used = date_used

    def merge_entry(self, guild_id, date1, date2):
        """
        Merge data entry from dates for given guild, data1 = data1 + data2
        @param guild_id: int guild id
        @param date1: datetime target
        @param date2: datetime source
        @return: None
        """
        for emoji_id in self.db[guild_id][date1]:
            # print(emoji_id)
            try:
                self.db[guild_id][date1][emoji_id].instance_count += self.db[guild_id][date2][emoji_id].instance_count
                self.db[guild_id][date1][emoji_id].total_count += self.db[guild_id][date2][emoji_id].total_count
                # print(self.db[guild_id][date1][emoji_id].instance_count, ' + ',
                #       self.db[guild_id][date2][emoji_id].instance_count)
            except KeyError:
                print('no entry for emoji')

    async def compile_emoji(self, guild_ID):
        """
        Creates dictionary of emoji ID and emojiStat object
        @param guild_ID: guild ID integer
        @return: emoji_dict[emoji ID] = EmojiStat (object)
        """
        # emojis for current guild ID
        emojis = [x for x in self.bot.get_guild(guild_ID).emojis if x.managed is False]
        # emojis = self.bot.get_guild(guild_ID).emojis

        emoji_dict = {}
        # Add into dictionary newly created EmojiStat object
        for current_emoji in emojis:
            emoji_dict[current_emoji.id] = EmojiStat.EmojiStat(current_emoji)
        return emoji_dict

    def export(self, guild_id):
        print('Saving JSON file...')
        temp_db = {}
        for guild_ID, date_key in self.db.items():
            temp_db[guild_ID] = {}
            for date in self.db[guild_ID]:
                temp_db[guild_ID][date.strftime('%Y-%m-%d %H:%M:%S')] = self.db[guild_ID][date]
        with open('emoji-data.json', 'w', encoding='utf-8') as write_file:
            json.dump(temp_db, write_file, indent=2, default=encoder_json)
        # export to firebase
        with open('emoji-data.json', 'r', encoding='utf-8') as read_file:
            ref = db.reference(str(guild_id))
            ref.update(json.load(read_file)[str(guild_id)])

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
                for emoji_id in database[guild][date]:
                    inst = database[guild][date][emoji_id]['instance_count']
                    tot = database[guild][date][emoji_id]['total_count']
                    last = database[guild][date][emoji_id]['last_used']
                    last = datetime.datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f') if last != 'None' else None
                    temp_emoji[int(emoji_id)] = EmojiStat.EmojiStat(self.bot.get_emoji(int(emoji_id)),
                                                                    inst,
                                                                    tot,
                                                                    last)
                date_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                temp_date[date_obj] = temp_emoji
            temp_db[int(guild)] = temp_date

        return temp_db


def encoder_json(file_object):
    """
    JSON helper, encodes non native JSON objects
    @param file_object: obj
    @return: EmojiStat object: string, datetime: string
    """
    print(str(file_object), ' - ', type(file_object))
    if isinstance(file_object, EmojiStat.EmojiStat):
        return {'instance_count': file_object.instance_count,
                'total_count': file_object.total_count,
                'last_used': file_object.last_used.strftime(
                    '%Y-%m-%d %H:%M:%S.%f') if file_object.last_used is not None else 'None'}
    return None
