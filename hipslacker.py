"""
    Copyright 2018-2021 the original author or authors from the JHipster project.

    This file is part of the JHipster project, see https:
        //www.jhipster.tech/
    for more information.

    Licensed under the Apache License, Version 2.0 (the "License")
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http:
            //www.apache.org / licenses / LICENSE - 2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging
import re
import json
import time
import constants
import requests


class HipSlacker:

    def __init__(self, slack_client, command, channel, user):
        self.slack_client = slack_client
        # take the command after bot's name
        self.command = command.split(constants.AT_BOT)[1].strip().lower()
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
            "git-company": constants.JHIPSTER_ONLINE_USER,
            "repository-name": "my-awesome-app"
        }
        self.payload_generator = self.payload["generator-jhipster"]
        self.git_provider = "github"

    def process_command(self):
        # get username from Slack's API
        try:
            self.username = requests.get('https://slack.com/api/users.info', params={'token': constants.SLACK_BOT_TOKEN, 'user': self.user}).json()['user']['name']
        except Exception as e:
            self.logger.error("Unable to get username: %s", str(e))
            self.post_msg("I was unable to get your username :boom:")
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
                self.log_http("Generation error", r)
                self.post_fail_msg()
                return

            self.post_generation_status(r.text, token)
        else:
            self.post_fail_msg()

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

            # gitlab
            if(command == "gitlab"):
                self.git_provider = "gitlab"

        # repository name
        self.payload["repository-name"] = self.payload_generator["baseName"]

        # git provider
        self.payload["git-provider"] = self.git_provider
        self.payload_generator["packageName"] = f"io.{self.git_provider}.{constants.JHIPSTER_ONLINE_USER}"
        self.payload_generator["packageFolder"] = f"io/{self.git_provider}/{constants.JHIPSTER_ONLINE_USER}/"

        self.logger.info("Payload: %s", json.dumps(self.payload, indent=4))

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
            self.log_http("Error while getting the token", r)
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
                self.log_http("Unable to get generation's status", r)
                self.post_with_username("error while getting generation's status :boom:")
                return

            # post status
            self.post_msg(r.text)

            # post repository's link
            if "Generation finished" in r.text:
                self.logger.info("Generation finished")
                self.post_with_username(f"here the link of your application: https://{self.git_provider}.com/{constants.JHIPSTER_ONLINE_USER}/{self.payload_generator['baseName']}")
                return

            # post error message
            if "Generation failed" in r.text:
                self.logger.info("Generation failed")
                self.post_fail_msg()
                return

            # break the loop after a specific timeout
            if time.time() > timeout:
                self.post_with_username("the generation timed out :boom:")
                return

            time.sleep(0.5)

    def post_fail_msg(self):
        self.post_with_username("I was not able to generate the application :boom:")

    def post_with_username(self, msg):
        self.post_msg(f"Yo <@{self.username}>, {msg}")

    def post_msg(self, msg):
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text=msg, as_user=True)

    def log_http(self, msg, r):
        self.logger.error(f"{msg}, status: {r.status_code}, text: {r.text}")
