# HipSlacker

HipSlacker is a [Slack bot](https://slack.com/) that will generate a JHipster application using [JHipster Online](https://start.jhipster.tech/).

# Requirements

Start by creating your bot in [Slack](https://api.slack.com/apps?new_app=1).
Once your bot is created, retrieve the `bot_user_id` and `bot_access_token`. You can find help on this [page](https://api.slack.com/bot-users#retrieving_your_bot_user_token).

Create an account on [JHipster Online](https://start.jhipster.tech/) and link it with the GitHub account you want to use.

You will need python 3.7 and pipenv to run the bot.

# Configuration and start

Edit the file `.env` with the correct values.

```INI
BOT_ID=<Bot ID of your bot>
SLACK_BOT_TOKEN=<Bot token of your bot>
JHIPSTER_ONLINE_USER=<User for JHipster Online>
JHIPSTER_ONLINE_PWD=<Password for JHipster Online>
```

And then run the following commands to run the bot.

```shell
pipenv install
pipenv shell
python hipslacker.py
```

# Usage

To create a JHipster application named `my-awesome-app`, simply send a message starting with `generate` to your bot.

For example: `@hipslacker generate named my-awesome-app`.