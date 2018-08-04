import os
from dotenv import load_dotenv

# load environment variables
load_dotenv()
BOT_ID = os.getenv('BOT_ID', '')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
JHIPSTER_ONLINE_USER = os.getenv('JHIPSTER_ONLINE_USER', '')
JHIPSTER_ONLINE_PWD = os.getenv('JHIPSTER_ONLINE_PWD', '')
