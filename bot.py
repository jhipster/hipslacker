import os
import logging
import time
import constants
from logging.handlers import RotatingFileHandler
from slackclient import SlackClient
from hipslacker import HipSlacker

# constants
LOGGER_FORMAT = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
AT_BOT = '<@' + constants.BOT_ID + '>'
READ_WEBSOCKET_DELAY = 1

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
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), output['channel'], output['user']
    return None, None, None


def auto_reconnect(running):
    """
        Validates the connection boolean returned via `SlackClient.rtm_connect()`
        if running is False:
            * Attempt to auto reconnect a max of 5 times
            * For every attempt, delay reconnection (F_n)*5, where n = num of retries
        Parameters
        -----------
        running : bool
            The boolean value returned via `SlackClient.rtm_connect()`
        Returns
        --------
        running : bool
            The validated boolean value returned via `SlackClient.rtm_connect()`
    """
    retries = 0
    max_retries = 5
    while not running:
        if retries < max_retries:
            retries += 1
            try:
                # delay for longer and longer each retry in case of extended outages
                current_delay = (retries + (retries - 1)) * 5  # fibonacci, bro
                logger.info("Attempting reconnection %s of %s in %s seconds...", retries, max_retries, current_delay)
                time.sleep(current_delay)
                running = slack_client.rtm_connect()
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received")
                break
        else:
            logger.error("Max retries exceeded")
            break
    logger.info("Bot started")
    return running


def run():
    """
        Passes the `SlackClient.rtm_connect()` method into `self._auto_reconnect()` for validation
        if running:
            * Capture and parse events via `Slacker.process_events()` every second
            * Close gracefully on KeyboardInterrupt (for testing)
            * log any Exceptions and try to reconnect if needed
        Parameters
        -----------
        n/a
        Returns
        --------
        n/a
    """
    running = auto_reconnect(slack_client.rtm_connect())
    while running:
        try:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")
            running = False
        except Exception as e:
            logger.exception(e)
            running = auto_reconnect(slack_client.rtm_connect())


if __name__ == '__main__':
    # configure logger
    logger = logging.getLogger('hipslacker')
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler('bot.log', mode='a', maxBytes=5 * 1024 * 1024, backupCount=1, encoding=None, delay=0)
    fh.setLevel(logging.INFO)
    fh.setFormatter(LOGGER_FORMAT)
    logger.addHandler(fh)

    run()
