import os
import time
import requests
import json
import datetime
import logging
import re
from logging.handlers import RotatingFileHandler
from slackclient import SlackClient

# hipslacker's ID as an environment variable
BOT_ID = os.environ.get('BOT_ID', '')
BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')

# constants
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
AT_BOT = '<@' + BOT_ID + '>'
READ_WEBSOCKET_DELAY = 1

# instantiate Slack
slack_client = SlackClient(BOT_TOKEN)


def handle_command(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    logger.info("Processing req " + command)
    if(command.startswith("generate ")):
        genapp(command.split('generate ', 1)[1], channel)
        return
    username = user
    try:
        # get username from Slack's API
        username = requests.get('https://slack.com/api/users.info', params={'token': BOT_TOKEN, 'user': username}).json()['user']['name']
    except Exception as e:
        logger.error('Unable to get username : ' + str(e))

    response = "Yo hipster, to get started give me a make command." 

    # post bot's message
    slack_client.api_call('chat.postMessage', channel=channel,
                          text=response, as_user=True)

def genapp(command, channel):
    commandList = re.split("\s+", command)
    print("with commands: ")
    print(*commandList, sep="\n")
    apptype = commandList[0]
    response = f"I got your request to create a {apptype} application."
    payload = generate_payload()
    d = payload["generator-jhipster"]
    
    for i in range(len(commandList)):
        key = commandList[i]
        print(f"processing {key}")
        cmdswitch = {
            "microservice": ["applicationType", key], 
            "monolith": ["applicationType", key],
            "angular": ["clientFramework", "angularX"],
            "react": ["clientFramework", "react"],
            "named": ["baseName", commandList[i+1]] if i < len(commandList)-1 else ["baseName", "test"],
            "mysql": dbUpdate(d, "sql", "h2Disk", "mysql"),
            "mongo": dbUpdate(d, "mongodb", "mongodb", "mongodb"),
            "cassandra": dbUpdate(d, "cassandra", "cassandra", "cassandra")
        }
        print("get switch")
        rslt = cmdswitch.get(key, ["nomatch"])
        print("result received")
        if(len(rslt) ==2):
            d[rslt[0]] = rslt[1]
    
    print("\n\npayload is" + json.dumps(d, indent=4))
    generate_application(payload, channel)
    # print json.dumps(d, indent=4)
    slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

def dbUpdate(dictionary, dbtype, dev, prod):
    dictionary["databaseType"]= dbtype
    dictionary["devDatabaseType"]= dev
    dictionary["prodDatabaseType"]= prod
    return ["already processed"]

def generate_payload():
    return {
        "generator-jhipster": {
            "applicationType": "monolith",
            "gitHubOrganization": "hipslacker",
            "baseName": "test",
            "packageName": "io.github.hipslacker.application",
            "packageFolder": "io/github/hipslacker/application",
            "serverPort": 8080,
            "serviceDiscoveryType": False,
            "authenticationType": "jwt",
            "uaaBaseName": "../uaa",
            "cacheProvider": "ehcache",
            "enableHibernateCache": True,
            "websocket": False,
            "databaseType": "sql",
            "devDatabaseType": "h2Disk",
            "prodDatabaseType": "mysql",
            "searchEngine": False,
            "enableSwaggerCodegen": False,
            "messageBroker": False,
            "buildTool": "maven",
            "useSass": False,
            "clientPackageManager": "yarn",
            "testFrameworks": [],
            "enableTranslation": False,
            "nativeLanguage": "en",
            "languages": [
                "en"
            ],
            "clientFramework": "react",
            "jhiPrefix": "jhi"
        }
    }

def generate_application(channel, payload):
    token = get_token()
    if token is None:
        return "An error occured while getting the token :sadpanda:"
    headers = {"Authorization": "Bearer {}".format(token)}
    r = requests.post("https://start.jhipster.tech/api/generate-application", data=json.dumps(payload), headers=headers)
    if r.status_code != 201:
        logger.error("Error while generating! status: {}, text: {}".format(r.status_code, r.text))
        return "An error occured while generating the application :sadpanda:"
    else:
        timeout = time.time() + 60
        app_id = r.text
        while True:
            # get status of generation
            r = requests.get("https://start.jhipster.tech/api/generate-application/{}".format(app_id), headers=headers)
            if r.status_code == 200:
                # post status of generation
                slack_client.api_call('chat.postMessage', channel=channel, text=r.text, as_user=True)
                if "Generation finished" in r.text:
                    return "Link of your application: https://github.com/hipslacker/{}".format(payload['generator-jhipster']['baseName'])
            else:
                logger.error("Error while getting status of generation! status: {}, text: {}".format(r.status_code, r.text))
                return "An error occured while getting status of generation :sadpanda:"
            time.sleep(0.5)

            # break the loop after 1min
            if time.time() > timeout:
                logger.error("Timeout while waiting for generation! status: {}, text: {}".format(r.status_code, r.text))
                return "Timeout while waiting for generation :sadpanda:"


def get_token():
    url = "https://start.jhipster.tech/api/authenticate"
    data = {"password": os.environ.get('JHIP_PASS'), "username": "hipslacker"}
    r = requests.post(url, json=data)
    if r.status_code != 200:
        logger.error("Error while getting the token! status: {}, text: {}".format(r.status_code, r.text))
        return None
    else:
        return r.json()['id_token']


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            logger.info("Parsing " + json.dumps(output))
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                    output['channel'], output['user']
    return None, None, None


def auto_reconnect(running):
    """Validates the connection boolean returned via `SlackClient.rtm_connect()`
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
                logger.info(
                    "Attempting reconnection %s of %s in %s seconds...",
                    retries,
                    max_retries,
                    current_delay
                )
                time.sleep(current_delay)
                running = slack_client.rtm_connect()
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                break
        else:
            logger.error("Max retries exceeded")
            break
    logger.info("Bot started.")
    return running


def run():
    """Passes the `SlackClient.rtm_connect()` method into `self._auto_reconnect()` for validation
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
            if command and channel and user:
                handle_command(command, channel, user)
            elif channel and user:
                show_dialog(user, channel, "testtrig")
            time.sleep(READ_WEBSOCKET_DELAY)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received.")
            running = False
        except Exception as e:
            logger.exception(e)
            running = auto_reconnect(slack_client.rtm_connect())


if __name__ == '__main__':
    # configure loggin
    logger = logging.getLogger('hipslacker')
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler('bot.log', mode='a', maxBytes=5 * 1024 * 1024,
                             backupCount=1, encoding=None, delay=0)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(fh)

    run()
