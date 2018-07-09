# `bb-pipeline-setup`: Configure BB Pipelines without risking _Carpal Tunnel Syndrome_

## What this does

The repository contins a script that automatically configures a BB pipeline for a given repository, based on a simple configuration file you provide.

## The configuration file

Let's document the possibilities of the script by example.

```
repo:
  slug: aws-lambda-sns-to-google-chat
  owner: ixorcvba

pipeline_template: nodejs-lambda-template.yml

ssh:
  privatekey: |
    -----BEGIN RSA PRIVATE KEY-----
    rubbish
    -----END RSA PRIVATE KEY-----
  publickey: |
    ssh-rsa ...............

variables:
  - name: LAMBDA_RUNTIME
    description: Lambda Runtime, see https://docs.aws.amazon.com/lambda/latest/dg/API_CreateFunction.html#SSS-CreateFunction-request-Runtime for list
    required: true
    value: node8.10
    secret: false
  - name: LAMBDA_FUNCTION_NAME
    description: The name of the function, determines how the uploaded file is called
    required: true
    value: my-nodejs-lambda-function
    secret: false
  - name: S3_DEST_BUCKET
    description: Bucket to copy the zipped package to
    required: true
    value: my-lambda-function-store
    secret: false
  - name: AWS_ACCESS_KEY_ID
    description: AWS credentials to push the artefact container image to the ECR defined by AWS_ACCOUNTID_TARGET
    required: true
    value: AKIA1234567890123456
    secret: false
  - name: AWS_SECRET_ACCESS_KEY
    description: AWS credentials to push the artefact container image to the ECR defined by AWS_ACCOUNTID_TARGET
    required: true
    value: thisisnotarealawssecretaccesskeybutihope
    secret: true
```

### The repository to act upon

```
repo:
  slug: aws-lambda-sns-to-google-chat
  owner: ixorcvba
```

### The pipeline template to use

```
pipeline_template: nodejs-lambda-template.yml
```

* The available templates are in the directory `pipeline_templates`.
* If a `bitbucket-pipelines.yml` already exists in the repo, it will not be changed or overwritten

### The `ssh` comnfiguration

```
ssh:
  privatekey: |
    -----BEGIN RSA PRIVATE KEY-----
    rubbish
    -----END RSA PRIVATE KEY-----
  publickey: |
    ssh-rsa ...............
```

* Required if you want to checkout a private repository during the build
* The `privatekey` and the `publickey` belong together
* Can be ommitted if you do not need it

### The pipeline's environment variables

```
variables:
  - name: LAMBDA_RUNTIME
    value: node8.10
    description: Lambda Runtime, see https://docs.aws.amazon.com/lambda/latest/dg/API_CreateFunction.html#SSS-CreateFunction-request-Runtime for list
    required: true
    secret: false

```

#### `name`

The name of the variable. **REQUIRED**

#### `value`

The value for the variable. **REQUIRED**

#### `description`

An optional description.

#### `required`

Wether or not the variable is required, this is merely for documentation purposes.

#### `secret`

Wether or not the variable value should be shown in the BB UI. **It is very important to set this to `true` for all secrets!!!**



## Running the tool

### Set your environment for BB access

* `BB_USER`: The BitBucket user to use to run these actions. The user should have sufficient access to change the repository configuration.
* `BB_APP_PASSWD`: A BitBucket application application password for the `BB_USER` user. See [this procedure](https://confluence.atlassian.com/bitbucket/app-passwords-828781300.html) to create a _BB Application password_.

### Run the script

```
$ python bb-pipeline-setup.py -f <path_to_configfile>
```

This will produce some logging like this:

```
2018-07-09 12:07:32,761 - bb-pipeline-setup - INFO - Verifying variable LAMBDA_FUNCTION_NAME with value the-name-of-the-function
2018-07-09 12:07:32,761 - bb-pipeline-setup - INFO - Pipeline variable LAMBDA_FUNCTION_NAME does exists.
2018-07-09 12:07:33,668 - bb-pipeline-setup - INFO - Verifying variable S3_DEST_BUCKET with value the-name-of-the-bucket
2018-07-09 12:07:33,668 - bb-pipeline-setup - INFO - Pipeline variable S3_DEST_BUCKET does exists.
2018-07-09 12:07:34,441 - bb-pipeline-setup - INFO - Verifying variable AWS_ACCESS_KEY_ID with value AKIA123456789
2018-07-09 12:07:34,442 - bb-pipeline-setup - INFO - Pipeline variable AWS_ACCESS_KEY_ID does exists.
2018-07-09 12:07:35,245 - bb-pipeline-setup - INFO - Verifying variable AWS_SECRET_ACCESS_KEY with value xxxxxxxxxx
2018-07-09 12:07:35,245 - bb-pipeline-setup - INFO - Pipeline variable AWS_SECRET_ACCESS_KEY does exists.
2018-07-09 12:07:36,092 - bb-pipeline-setup - INFO - Verifying if ssh keypair needs to be added and add it
2018-07-09 12:07:36,092 - bb-pipeline-setup - INFO - Configuration does not contains private or public key, skip adding ssh keypair
```

## Troubleshooting

### `403` errors are probably caused by the scope of the BB app password not being enough.

When you encounter a `403` HTTPS error when running the tool, the scope of the BB App Password probably is too narrow.

THere is now way, however, to change the scopt for an existing BB Application Password. You should create another one, or delete and recreate the one that fails.

The scope should contain (at least):

* `Pipelines`: `Read`, `Write` and `Edit Variables` 
* `Repositories`: `Read`
