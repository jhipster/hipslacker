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
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and constants.AT_BOT in output['text']:
                return output['text'], output['channel'], output['user']
    return None, None, None


def run():
    """
        Main loop that reads messages mentioning the bot with a defined delay
    """
    if slack_client.rtm_connect(auto_reconnect=True):
        logger.info("Bot connected")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
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
