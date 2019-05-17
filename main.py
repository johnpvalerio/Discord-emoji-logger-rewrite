from discord.ext.commands import bot

import EmojiController
import EmojiModel
import EmojiView
from discord.ext import commands


def main():
    print('AegisBot Initializing')
    bot = commands.Bot(command_prefix='!')

    model = EmojiModel.Model(bot)
    view = EmojiView.View(model, bot)
    controller = EmojiController.Controller(model, view, bot)

    bot.add_cog(model)
    bot.add_cog(view)
    bot.add_cog(controller)

    f = open('Discord_key.txt', 'r')
    bot.run(f.read(), bot=True)


if __name__ == '__main__':
    main()
