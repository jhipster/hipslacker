import os
from dotenv import load_dotenv
from pathlib import Path

# load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
BOT_ID = os.getenv('BOT_ID', '')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
JHIPSTER_ONLINE_USER = os.getenv('JHIPSTER_ONLINE_USER', '')
JHIPSTER_ONLINE_PWD = os.getenv('JHIPSTER_ONLINE_PWD', '')
LOGGER_FORMAT = os.getenv('LOGGER_FORMAT', '')
READ_WEBSOCKET_DELAY = int(os.getenv('READ_WEBSOCKET_DELAY', ''))
AT_BOT = os.getenv('AT_BOT', '')
