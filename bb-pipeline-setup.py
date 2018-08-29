
import argparse
import requests
import yaml
import json
import os
import pprint
import logging
import jinja2


class repo:

    def __init__(self, logger, repo_slug, repo_owner, project_key):
        self.logger = logger
        self.repo_slug = repo_slug
        self.repo_owner = repo_owner
        self.project_key = project_key
        self.pipeline_variables = None

        self.check_environment()

        self.api_endpoint_base = 'https://api.bitbucket.org/2.0/repositories/' + self.repo_owner + '/' + self.repo_slug
        self.logger.info("API Endpoint URL is " + self.api_endpoint_base)

    def check_environment(self):
        if os.environ.has_key('BB_USER') and os.environ.has_key('BB_APP_PASSWD'):
            self.bb_user = os.environ.get('BB_USER')
            self.bb_app_passwd = os.environ.get('BB_APP_PASSWD')
        else:
            self.logger.error('One of BB_USER or BB_APP_PASSWD is not defined')
            raise ValueError('One of BB_USER or BB_APP_PASSWD is not defined')

    def repo_exists(self):
        response = requests.get(self.api_endpoint_base, auth=(self.bb_user, self.bb_app_passwd))
        dictresponse = json.loads(response.content)
        if response.status_code != 200:
            self.logger.error("Repo does not exist.")
            self.logger.error(dictresponse)
            return False
        else:
            self.logger.info('Repo exists')
            return True

    def repo_create(self):
        headers = {'Content-type': 'application/json'}
        if self.project_key is None:
            payload = { "scm": "git", "is_private": "true" }
        else:
            payload = { "scm": "git", "is_private": "true", "project": { "key": self.project_key } }

        response = requests.put(self.api_endpoint_base, auth=(self.bb_user, self.bb_app_passwd), data=json.dumps(payload), headers=headers)
        dictresponse = json.loads(response.content)
        if response.status_code != 200:
            self.logger.error("Error creating repo: {}".format(response.status_code))
            self.logger.error("{}".format(json.dumps(payload)))
            self.logger.error(dictresponse)
            return False
        else:
            self.logger.info("Repo successfully created")
            return True

    def is_pipeline_enabled(self):
        if self.repo_exists():
            response = requests.get(self.api_endpoint_base + '/pipelines_config', auth=(self.bb_user, self.bb_app_passwd))
            dictresponse = json.loads(response.content)
            if response.status_code != 200:
                self.logger.error("Repo exists, but no pipeline is configured")
                self.logger.error(dictresponse)
                return False
            else:
                self.logger.info("Pipeline enabled is %s" % dictresponse['enabled'])
                return dictresponse['enabled']
        else:
            self.logger.warning('Repository does not exist.')
            return False

    def enable_pipeline(self):
        payload = { "enabled" : "true" }
        headers = {'Content-type': 'application/json'}

        response = requests.put(self.api_endpoint_base + '/pipelines_config', auth=(self.bb_user, self.bb_app_passwd), data=json.dumps(payload), headers=headers)
        dictresponse = json.loads(response.content)

        if response.status_code != 200:
            self.logger.error("Enabling pipeline failed")
            self.logger.error(response.status_code)
            self.logger.error(dictresponse)
            return False
        else:
            self.logger.info("Pipeline successfully enabled")
            return True

    def has_pipelinefile(self):
        response = requests.get(self.api_endpoint_base + '/src', auth=(self.bb_user, self.bb_app_passwd))
        self.logger.debug(response.status_code)
        self.logger.debug(response.content)
        dictresponse = json.loads(response.content)
        ### Search for path equals bitbucket-pipelines.yml in the list dictresponse['values']
        if 'values' not in dictresponse.keys() or next((item for item in dictresponse['values'] if item["path"] == "bitbucket-pipelines.yml"), None) is None:
            self.logger.info('No bitbucket-pipelines.yml found in repository')
            return False
        else:
            self.logger.info('bitbucket-pipelines.yml found in repository')
            return True

    def create_pipeline_file(self, pipelinefilestring):
        files = {'bitbucket-pipelines.yml': pipelinefilestring}
        response = requests.post(self.api_endpoint_base + '/src', auth=(self.bb_user, self.bb_app_passwd), files=files)
        self.logger.debug(response.status_code)

        return True

    def add_or_update_pipeline_variable(self, name, value, is_secret):
        self.get_pipeline_variables()
        if not self.pipeline_variable_exists(name):
            self.create_pipeline_variable(name, value, is_secret)
        else:
            self.update_pipeline_variable(name, value, is_secret)

    def get_pipeline_variables(self):
        if self.pipeline_variables is None:
            response = requests.get(self.api_endpoint_base + '/pipelines_config/variables/?pagelen=99',
                                    auth=(self.bb_user, self.bb_app_passwd))
            self.logger.debug(response.status_code)
            self.logger.debug(response.content)
            dictresponse = json.loads(response.content)
            self.pipeline_variables = dictresponse['values']


    def pipeline_variable_exists(self, name):
        for var in self.pipeline_variables:
            if var['key'] == name:
                self.logger.info("Pipeline variable %s does exist." % name)
                return True

        self.logger.info("Pipeline variable %s does not exist." % name)
        return False

    def update_pipeline_variable(self, name, value, is_secret):
        for var in self.pipeline_variables:
            if var['key'] == name:
                # This is the one to update!!!
                payload = {"key": name, "value": value, "secured": is_secret, "uuid": var['uuid']}
                headers = {'Content-type': 'application/json'}
                response = requests.put(self.api_endpoint_base + '/pipelines_config/variables/' + var['uuid'],
                                         auth=(self.bb_user, self.bb_app_passwd),
                                         data=json.dumps(payload),
                                         headers=headers)
                self.logger.debug('update_pipeline_variable: %i' % response.status_code)
                self.logger.debug('update_pipeline_variable: %s' % response.content)


    def create_pipeline_variable(self, name, value, is_secret):
        payload = { "key": name, "value": value, "secured": is_secret }
        headers = {'Content-type': 'application/json'}
        response = requests.post(self.api_endpoint_base + '/pipelines_config/variables/',
                                 auth=(self.bb_user, self.bb_app_passwd),
                                 data=json.dumps(payload),
                                 headers=headers)
        self.logger.debug('create_pipeline_variable: %i' % response.status_code)
        self.logger.debug('create_pipeline_variable: %s' % response.content)

    def ssh_add_keypair(self, private, public):
        payload = { "private_key": private, "public_key": public }
        headers = {'Content-type': 'application/json'}
        response = requests.put(self.api_endpoint_base + '/pipelines_config/ssh/key_pair',
                                auth=(self.bb_user, self.bb_app_passwd),
                                data=json.dumps(payload),
                                headers=headers)
        self.logger.debug('ssh_add_keypair: %i' % response.status_code)
        self.logger.debug('ssh_add_keypair: %s' % response.content)

class bb_pipeline_config:

    def __init__(self):
        self.name = 'bb-pipeline-setup'

        self.setup_logger()
        self.logger.info('Starting bb-pipeline-setup')
        self.parse_cli_args()
        self.read_config()

        if self.args.verbose:
            self.logger.setLevel(logging.DEBUG)

        if 'repo' in self.config and 'project_key' in self.config['repo']:
            self.repo = repo(self.logger, self.config['repo']['slug'], self.config['repo']['owner'], self.config['repo']['project_key'])
        else:
            self.repo = repo(self.logger, self.config['repo']['slug'], self.config['repo']['owner'], None)

        if not self.repo.repo_exists():
            if not self.repo.repo_create():
                self.logger.error("Error creating repo - giving up")
                exit(1)
            else:
                self.logger.info("Repo successfully created")

        if 'pipeline_template' in self.config:
            if not self.repo.has_pipelinefile():
                self.repo.create_pipeline_file(self.create_bb_file_from_template(self.config['pipeline_template']))
            if not self.repo.is_pipeline_enabled():
                self.repo.enable_pipeline()
        else:
            self.logger.info("No pipeline_template in config - skipping pipeline config")

        self.add_pipeline_variables()
        self.ssh_add_keypair()


    def create_bb_file_from_template(self, template):
        templateLoader = jinja2.FileSystemLoader(searchpath="./pipeline_templates")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(template)
        return(template.render(repo_slug=self.config['repo']['slug'], repo_owner=self.config['repo']['owner']))


    def ssh_add_keypair(self):
        self.logger.info("Verifying if ssh keypair needs to be added and add it")
        if 'ssh' in self.config and 'privatekey' in self.config['ssh'] and 'publickey' in self.config['ssh']:
            self.logger.info("Configuration contains private and public key, continue to add the key to the pipeline config")
            self.repo.ssh_add_keypair(self.config['ssh']['privatekey'], self.config['ssh']['publickey'])
        else:
            self.logger.info("Configuration does not contain private or public key, skip adding ssh keypair")

    def add_pipeline_variables(self):
        if 'variables' in self.config:
            for variable in self.config['variables']:
                if variable['secret']:
                    self.logger.info("Verifying variable %s with value xxxxxxxxxx" % variable['name'])
                else:
                    self.logger.info("Verifying variable %s with value %s" % (variable['name'], variable['value']))
    
                self.repo.add_or_update_pipeline_variable(variable['name'], variable['value'], variable['secret'])
        else:
            self.logger.info("No variables in config - skipping variables config")

    def read_config(self):
        with open(self.args.configfile, 'r') as stream:
            try:
                self.config = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self.logger.info("Configuration dump")
        self.logger.info(self.config)

    def setup_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler('./' + self.name + '.log')
        ch = logging.StreamHandler()

        formatter_file = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter_stderr = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fh.setFormatter(formatter_file)
        fh.setLevel(logging.DEBUG)

        ch.setFormatter(formatter_stderr)
        ch.setLevel(logging.DEBUG)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def parse_cli_args(self):
        """ Command line argument processing """
        help = {'verbose': 'More verbose output',
                'configfile': 'The configuration file',
                }

        parser = argparse.ArgumentParser(prog='bb-pipeline-setup',
                                         description='Configure the BB pipeline setup for a project')

        parser.add_argument('-v', '--verbose', action='store_true', default=False, help=help['verbose'])
        parser.add_argument('-f', '--configfile', action='store', required=True, help=help['configfile'])

        self.args = parser.parse_args()

bb_pipeline_config()
