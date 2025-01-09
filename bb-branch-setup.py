import logging

from bb_repo import Repo


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler('./' + name + '.log')
    ch = logging.StreamHandler()

    formatter_file = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter_stderr = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh.setFormatter(formatter_file)
    fh.setLevel(logging.DEBUG)

    ch.setFormatter(formatter_stderr)
    ch.setLevel(logging.DEBUG)

    return logger

logger = setup_logger("bb-branch-setup")
myRepo = Repo(logger=logger, repo_owner='ixorvcba', repo_slug='aws-cdk-ixorthink-toolbox', project_key='ITHINK')

if myRepo.repo_exists():
    myRepo.branch_exists('develop')
else:
    logger.info("Repo does not exist")
