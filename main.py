import configparser

from discord.ext import commands

import EmojiController
import EmojiModel
import EmojiView


def main():
    print('AegisBot Initializing')
    bot = commands.Bot(command_prefix='!')

    model = EmojiModel.Model(bot)
    view = EmojiView.View(model, bot)
    controller = EmojiController.Controller(model, view, bot)

    bot.add_cog(model)
    bot.add_cog(view)
    bot.add_cog(controller)

    config = configparser.ConfigParser()
    config.read('configs/config.ini')
    bot.run(config['DEFAULT']['Discord_key'], bot=True)


if __name__ == '__main__':
    main()
