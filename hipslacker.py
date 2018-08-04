import logging
import re
import json
import time
import constants
import requests


class HipSlacker:

    def __init__(self, slack_client, command, channel, user):
        self.slack_client = slack_client
        self.command = command
        self.channel = channel
        self.user = user

        # get logger
        self.logger = logging.getLogger("hipslacker")

        # split command to commands using spaces as delimiter
        self.commands = re.split("\s+", command)

        # init payload with default values
        self.payload = {
            "generator-jhipster": {
                "applicationType": "monolith",
                "baseName": "my-awesome-app",
                "packageName": "io.github.hipslacker",
                "packageFolder": "io/github/hipslacker/",
                "serverPort": 8080,
                "serviceDiscoveryType": "eureka",
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
            },
            "git-provider": "GitHub",
            "git-company": constants.JHIPSTER_ONLINE_USER,
            "repository-name": "my-awesome-app"
        }
        self.payload_generator = self.payload["generator-jhipster"]

    def process_command(self):
        # get username from Slack's API
        try:
            self.username = requests.get('https://slack.com/api/users.info', params={'token': constants.SLACK_BOT_TOKEN, 'user': self.user}).json()['user']['name']
        except Exception as e:
            self.logger.error("Unable to get username: %s", str(e))
            self.post_message("I was unable to get your username :boom:")
            return

        # generate command
        if(self.command.startswith("generate ")):
            self.post_with_username("I got your request to generate an application")
            self.generate_application()
            return

        # post default message
        self.post_with_username("to get started give me a generate command (ex: `@hipslacker generate a microservice with mongodb named my-awesome-app`)")

    def generate_application(self):
        self.generate_payload()

        # get token
        token = self.get_token()
        if token:
            # start generation
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.post("https://start.jhipster.tech/api/generate-application", data=json.dumps(self.payload), headers=headers)

            # post error if generation failed
            if r.status_code != 201:
                self.log_request("Generation error", r)
                self.post_generation_failed()
                return

            self.post_generation_status(r.text, token)
        else:
            self.post_generation_failed()

    def generate_payload(self):
        for command in self.commands:
            # application type
            if(command in ["monolith", "microservice", "gateway", "uaa"]):
                self.set_application_type(command)

            # base name
            if(command == "named"):
                self.set_app_name()

            # sql database
            if(command in ["mysql", "mariadb", "postgresql", "oracle", "mssql"]):
                self.set_database("sql", "h2Disk", command)

            # nosql database
            if(command in ["mongodb", "cassandra"]):
                self.set_database(command, command, command)

            # port
            if(command == "port"):
                self.set_port()

        # repository name
        self.payload["repository-name"] = self.payload_generator["baseName"]

        self.logger.info("Payload: %s", self.payload)

    def set_application_type(self, value):
        self.payload_generator["applicationType"] = value

    def set_app_name(self):
        index = self.commands.index("named") + 1
        if index < len(self.commands):
            self.payload_generator["baseName"] = self.commands[index]

    def set_database(self, db_type, dev_type, prod_type):
        self.payload_generator["databaseType"] = db_type
        self.payload_generator["devDatabaseType"] = dev_type
        self.payload_generator["prodDatabaseType"] = prod_type

    def set_port(self):
        index = self.commands.index("port") + 1
        if index < len(self.commands):
            self.payload_generator["serverPort"] = int(self.commands[index])

    def get_token(self):
        """
            Get a JWT using credentials
        """
        data = {"password": constants.JHIPSTER_ONLINE_PWD, "username": constants.JHIPSTER_ONLINE_USER}
        r = requests.post("https://start.jhipster.tech/api/authenticate", json=data)
        if r.status_code != 200:
            self.log_request("Error while getting the token", r)
            return None
        else:
            return r.json()["id_token"]

    def post_generation_status(self, app_id, token):
        """
            Get status of generation every 500ms during 1min
        """
        timeout = time.time() + 60
        while True:
            # get status of generation
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"https://start.jhipster.tech/api/generate-application/{app_id}", headers=headers)

            # post error if getting status failed
            if r.status_code != 200:
                self.log_request("Unable to get generation's status", r)
                self.post_with_username("Error while getting status of generation :boom:")
                return

            # post status
            self.post_message(r.text)

            # post repository's link
            if "Generation finished" in r.text:
                self.post_with_username("Link of your application: https://github.com/hipslacker/" + self.payload["repository-name"])
                return

            # post error message
            if "Generation failed" in r.text:
                self.post_generation_failed()
                return

            # break the loop after a specific timeout
            if time.time() > timeout:
                self.post_with_username("The generation timed out :boom:")
                return

            time.sleep(0.5)

    def post_generation_failed(self):
        self.post_with_username("I was not able to generate the application :boom:")

    def post_with_username(self, msg):
        self.post_message(f"Yo <@{self.username}>, " + msg)

    def post_message(self, msg):
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text=msg, as_user=True)

    def log_request(self, msg, r):
        self.logger.error(f"{msg}, status: {r.status_code}, text: {r.text}")
