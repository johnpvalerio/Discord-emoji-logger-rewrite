import configparser
import logging

from discord.ext import commands

import EmojiController
import EmojiModel
import EmojiView


def main():
    # logging.basicConfig(filename='configs/bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    logger = logging.getLogger('bot_logs')
    stm_log = logging.StreamHandler()
    fh_log = logging.FileHandler("configs/bot.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stm_log.setFormatter(formatter)
    fh_log.setFormatter(formatter)
    logger.addHandler(stm_log)
    logger.addHandler(fh_log)
    logger.setLevel(logging.INFO)

    logger.info("AegisBot initializing")
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
