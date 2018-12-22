import datetime
import json
import os
import asyncio
import re

import discord
from discord.ext import commands

from EmojiStat import EmojiStat

# client = discord.Client()
bot = commands.Bot(command_prefix="!")
dict_emoji = {}
os.chdir(os.path.dirname(__file__))  # change working directory to file location


@bot.event
async def on_ready():
    print("--------------------------")
    print('Logged in as:')
    print('name: ', bot.user.name)
    print('name: ', bot.user.id)
    print("--------------------------\n")

    initialize_emojis()


def initialize_server_emoji(server):
    dict_output = {}
    print("\n--------------------------")
    print('[Emoji]')
    print("--------------------------")
    for current_emoji in server.emojis:
        print('emoji: ', str(current_emoji))
        if current_emoji.managed:
            print('\tError: managed emoji (Twitch)')
            continue
        elif str(current_emoji) in server.emojis:
            print('\tError: Error: duplicate found')
            continue
        else:
            print('\tAdding into dict')
            dict_output[current_emoji.id] = EmojiStat(current_emoji)

    for key, value in dict_output.items():
        print(str(value.emoji_obj))

    dict_output['date'] = server.created_at
    return dict_output


def initialize_emojis():
    global dict_emoji
    print("\n--------------------------")
    print('[Initialize]')
    print("--------------------------")

    for current_server in bot.guilds:
        print(current_server)
        # dict_emoji[current_server.id] = initialize_server_emoji(current_server)
        print('\t', type(current_server.id))
        dict_emoji[current_server.id] = initialize_server_emoji(current_server)
    print('Master emoji:')
    print(dict_emoji)
    file_load()


# JSON encoder - unserializable objects coverted
#     EmojiLogger : list[instance count , total count]
#     datetime : string(date)
def encoder_json(file_object):
    print(str(file_object), ' - ', type(file_object))
    if isinstance(file_object, EmojiStat):
        return file_object.instance_count, file_object.total_count
    if isinstance(file_object, datetime.datetime):
        return file_object.__str__()
    return None


def file_save():
    print("\n--------------------------")
    print('[File Save]')
    print("--------------------------")
    with open('emoji_data.json', 'w') as write_file:
        print('Saving JSON file...')
        json.dump(dict_emoji, write_file, indent=4, default=encoder_json)


def file_load():
    global dict_emoji
    print("\n--------------------------")
    print('[File Load]')
    print("--------------------------")
    try:
        with open('emoji_data.json', 'r') as read_file:
            print('Opening JSON file...')
            dict_temp = json.load(read_file)
            print('temp: ')
            print(dict_temp)

            for server_id, emoji in dict_temp.items():
                for emoji_id, emoji_stats in emoji.items():
                    print(emoji_id)
                    if emoji_id == 'date':
                        dict_emoji[int(server_id)][emoji_id] = datetime.datetime.strptime(emoji_stats, '%Y-%m-%d '
                                                                                                       '%H:%M:%S.%f')
                        continue
                    try:
                        dict_emoji[int(server_id)][int(emoji_id)].instance_count = emoji_stats[0]
                        dict_emoji[int(server_id)][int(emoji_id)].total_count = emoji_stats[1]
                    except KeyError:
                        # data stored no longer active in server or invalid key
                        print('Error: key error')
    except FileNotFoundError:
        print('Error: file not found')
        print('Creating new file:')
        file_save()
    print('Output: ')
    print(dict_emoji)


def reset_counts(guild):
    print(guild)
    for emoji_id, emoji_obj in dict_emoji[guild].items():
        try:
            # print(emoji_obj.emoji_obj.name, emoji_obj.instance_increase, ' ', emoji_obj.total_increase)
            setattr(emoji_obj, 'instance_increase', 0)
            setattr(emoji_obj, 'total_increase', 0)
            # print(emoji_obj.emoji_obj.name, emoji_obj.instance_increase, ' ', emoji_obj.total_increase)
        except AttributeError:
            print('\tObject does not have attribute')


async def log_channel(ctx, channel, date_after, date_stop):
    global dict_emoji
    print('\tdate: ', date_after, ' - ', date_stop)

    async for message in channel.history(limit=None, before=date_stop, after=date_after):
        # skip if message from the bot
        if message.author == bot.user:
            continue
        emoji_found = re.findall(r'<a?:\w*:\d*>', message.content)
        # skip if no emojis found
        if not emoji_found:
            continue
        print('Emojis found: ', emoji_found)

        emoji_found = list(
            filter(lambda emoji:
                   emoji in list(str(emoji_server)
                                 for emoji_server in ctx.guild.emojis
                                 if not emoji_server.managed),
                   emoji_found))
        for emoji in set(emoji_found):
            emoji_count = emoji_found.count(emoji)

            dict_emoji[ctx.guild.id][int(emoji[-19:-1])].instance_count += 1
            dict_emoji[ctx.guild.id][int(emoji[-19:-1])].instance_increase += 1

            dict_emoji[ctx.guild.id][int(emoji[-19:-1])].total_count += emoji_count
            dict_emoji[ctx.guild.id][int(emoji[-19:-1])].total_increase += emoji_count


@bot.command(aliases=['history', 'compile', 'logs'])
async def log(ctx):
    print("\n--------------------------")
    print('[COMMAND] - log()')
    print("--------------------------")
    reset_counts(ctx.guild.id)
    for current_channel in list(filter(lambda channel:
                                       channel.permissions_for(ctx.guild.me).read_messages,
                                       ctx.guild.text_channels)):
        print(current_channel)
        if current_channel.created_at > dict_emoji[ctx.guild.id]['date']:
            await log_channel(ctx,
                              channel=current_channel,
                              date_after=current_channel.created_at,
                              date_stop=ctx.message.created_at)
        else:
            await log_channel(ctx,
                              channel=current_channel,
                              date_after=dict_emoji[ctx.guild.id]['date'],
                              date_stop=ctx.message.created_at)
    await ctx.send('Logging complete')


@bot.command()
async def file(ctx, arg):
    print("\n--------------------------")
    print('[COMMAND] - file()')
    print("--------------------------")
    if arg == 'save':
        file_save()
        await ctx.send('Save complete')
    elif arg == 'load':
        file_load()
        await ctx.send('Load complete')


@bot.command()
async def hello(ctx):
    print("\n--------------------------")
    print('[COMMAND] - hello()')
    print("--------------------------")
    await ctx.send('hello')


@bot.command()
async def show(ctx):
    print("\n--------------------------")
    print('[COMMAND] - map()')
    print("--------------------------")
    for key, value in dict_emoji[ctx.guild.id].items():
        if key == 'date':
            continue
        print(value.emoji_obj.name, ' - ', value.instance_count, ' ', value.total_count)


@bot.command(aliases=['echo', 'repeat'])
async def me(ctx, *args):
    print("\n--------------------------")
    print('[COMMAND] - me()')
    print("--------------------------")
    str_output = ''
    for word in args:
        str_output += word + ' '
    print(str_output)
    await ctx.send(str_output)


# doesnt work yet
@bot.command(aliases=['exit', 'bye'])
async def close(ctx):
    print("\n--------------------------")
    print('[COMMAND] - exit()')
    print("--------------------------")
    await ctx.send('Shutting down')
    await bot.logout()
    # await client.logout()
    print(quit)


bot.run('', bot=True)
