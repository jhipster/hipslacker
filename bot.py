"""
    Copyright 2018 the original author or authors from the Hipslacker project.

    This file is part of the JHipster project, see https://www.jhipster.tech/
    for more information.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import os
import logging
import time
import constants
from logging.handlers import RotatingFileHandler
from slackclient import SlackClient
from hipslacker import HipSlacker

# create Slack client
slack_client = SlackClient(constants.SLACK_BOT_TOKEN)


def handle_command(command, channel, user):
    """
        Handle the command sent to the bot and process it
    """
    logger.info(f"Processing command: {command}")
    hipslacker = HipSlacker(slack_client, command, channel, user)
    hipslacker.process_command()


def parse_slack_output(slack_rtm_output):
    """
        Each messages are parsed
        The method 'handle_command' is called if a message is directed to the Bot
    """
    if slack_rtm_output and len(slack_rtm_output) > 0:
        for output in slack_rtm_output:
            if output and 'text' in output and constants.AT_BOT in output['text'] and output['user'] != constants.BOT_ID:
                handle_command(output['text'], output['channel'], output['user'])


def run():
    """
        Main loop, messages are read with a given interval
    """
    if slack_client.rtm_connect(auto_reconnect=True):
        logger.info("Bot connected")
        while True:
            parse_slack_output(slack_client.rtm_read())
            time.sleep(constants.READ_WEBSOCKET_DELAY)
    else:
        logger.error("Connection failed")


if __name__ == '__main__':
    # configure logger
    logger = logging.getLogger('hipslacker')
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler('bot.log', mode='a', maxBytes=5 * 1024 * 1024, backupCount=1, encoding=None, delay=0)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(constants.LOGGER_FORMAT))
    logger.addHandler(fh)

    run()
