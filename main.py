# Haddock telegram bot
# Copyright (C) 2020 Yoann Pietri

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Haddock Telegram Bot.
Usage:
  main.py (start|stop|restart)
  main.py exec
  main.py debug
  main.py (-h | --help)
  main.py --version
Options:
  start         Start the daemon
  stop          Stop the daemon
  restart       Restart the daemon
  exec          Laucnh bot in blocking mode
  debug         Launch bot in blocking mode with debug info
  -h --help     Show this screen.
  --version     Show version.
"""

import configparser
import json
import logging
import os
import re
import requests
import sys
import random
import time

import telegram
from docopt import docopt
from telegram.ext import CommandHandler, Updater, Filters, MessageHandler


class Bot:
    """"
    Define a wrapper for haddock-telegram-bot. Defines handlers for commands.
    """

    def __init__(self, directory=None):
        """Initilise the bot
        
        Args:
            directory (string, optional): Where to find list.json and config.ini files. Defaults to None.
        """
        if directory:
            self.directory = directory
        else:
            self.directory = os.path.dirname(os.path.realpath(__file__))

        self.load_config()

        try:
            self.updater = Updater(token=self.token, use_context=True)
            logging.info("Bot {} grabbed.".format(self.updater.bot.username))
        except:
            logging.error("Unable to grab bot.")
            sys.exit()

        self.dispatcher = self.updater.dispatcher

        self.start_handler = CommandHandler("start", self.start)
        self.nanoy_handler = CommandHandler("vocabulaire", self.vocabulary)
        self.jmentape_handler = CommandHandler("insultes", self.insults)
        self.help_handler = CommandHandler("help", self.help)

        self.dispatcher.add_handler(self.start_handler)
        self.dispatcher.add_handler(self.nanoy_handler)
        self.dispatcher.add_handler(self.jmentape_handler)
        self.dispatcher.add_handler(self.help_handler)

    def load_config(self):
        """Load configuration file. The configuration file is the config.ini file in code directory.
        """
        config = configparser.ConfigParser()
        try:
            config.read("{}/config.ini".format(self.directory))
        except Exception as e:
            logging.error("Unable to read config : {}".format(str(e)))
            sys.exit()
        try:
            self.token = config.get("Global", "token")
        except:
            logging.error("Unable to find 'token' parameter in section 'Global'.")
            sys.exit()
        logging.info("Configuration loaded")

    def start(self, update, context):
        """start command handler.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Bonjour je suis Haddock, capitaine de ce navire.",
        )

    def vocabulary(self, update, context):
        """vocabulaire command handler.
        This command send word from /api/vocabulaire.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        resp = requests.get(url="https://haddock.nanoy.fr/api/vocabulaire")
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=resp.json()["msg"]
        )

    def insults(self, update, context):
        """insultes command handler.
        This command send word from /api/insultes.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        resp = requests.get(url="https://haddock.nanoy.fr/api/insultes")
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=resp.json()["msg"]
        )

    def help(self, update, context):
        """help command handler.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Bonjour je suis Haddock, capitaine de ce navire. Utilisez les commandes /vocabulaire et /insultes.",
        )

    def start_bot(self):
        """Start the bot.
        """
        self.updater.start_polling()


if __name__ == "__main__":
    arguments = docopt(__doc__, version="Haddock Telegram Bot 0.9")
    daemon = arguments["start"] or arguments["stop"] or arguments["restart"]
    debug = arguments["debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logfile = os.path.join(os.getcwd(), "haddock-telegram-bot.log")
        logging.basicConfig(filename=logfile, level=logging.WARNING)

    d = None

    if daemon:
        from daemons.prefab import run

        class ListBotDaemon(run.RunDaemon):
            def __init__(self, directory, *args, **kwargs):
                """Initialise the daemon
                
                Args:
                    directory (string): directory to pass to the bot
                """
                self.directory = directory
                super().__init__(*args, **kwargs)

            def run(self):
                """Run method (called when daemon starts).
                """
                bot = Bot(self.directory)
                bot.start_bot()

        pidfile = "/tmp/haddock-telegram-bot.pid"
        d = ListBotDaemon(os.path.dirname(os.path.realpath(__file__)), pidfile=pidfile)

    if arguments["start"]:
        d.start()
    elif arguments["stop"]:
        d.stop()
    elif arguments["restart"]:
        d.restart()
    else:
        bot = Bot()
        bot.start_bot()
