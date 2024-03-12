#!/usr/bin/env python3
# WARNING: If importing this fails set PYTHONPATH.
import yaml
import logging
import ansible
import argparse
import subprocess
import functools
from enum import Enum
from os import path, environ
from packaging import version
from concurrent import futures

HELP_DESCRIPTION='''
This tool managed Ansible roles as Git repositories.

It is both faster and simpler than Ansible Galaxy.
'''
HELP_EXAMPLE='''Examples:
./roles.py --install
./roles.py --check
./roles.py --update
'''


SCRIPT_DIR = path.dirname(path.realpath(__file__))
# Where Ansible looks for installed roles.
ANSIBLE_ROLES_PATH = path.join(environ['HOME'], '.ansible/roles')
WORK_DIR = path.join(environ['HOME'], 'work')

# Setup logging.
log_format = '[%(levelname)s] %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
LOG = logging.getLogger(__name__)


class State(Enum):
    # Order is priority. Higher status trumps lower.
    UNKNOWN       = 0
    EXISTS        = 1
    WRONG_VERSION = 2
    DIRTY         = 3
    NO_VERSION    = 4
    CLONE_FAILURE = 5
    MISSING       = 6
    CLONED        = 7
    UPDATED       = 8
    VALID         = 9

    def __str__(self):
        return self.name

    # Allow calling max() to compare with previous state.
    def __gt__(self, other):
        if other is None:
            return True
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    # Decorator to manage Role state based on function return value.
    def update(success=None, failure=None):
        def decorator(func):
            @functools.wraps(func)
            def wrapper_decorator(self, *args, **kwargs):
                # Set state to failure one on exception.
                try:
                    rval = func(self, *args, **kwargs)
                except:
                    self.state = max(failure, self.state)
                    raise
                # Set state based on truthiness of result, higher one wins.
                if rval:
                    self.state = max(success, self.state)
                else:
                    self.state = max(failure, self.state)
                LOG.debug('[%s]: %s%s: state = %s',
                          self.name, func.__name__, args, self.state)
                return rval
            return wrapper_decorator
        return decorator

class Role:

    def __init__(self, name, src, required):
        self.name = name
        self.src = src
        self.required = required
        self.state = State.UNKNOWN

    @classmethod
    def from_requirement(cls, obj):
        return cls(obj['name'], obj.get('src'), obj.get('version'))

    def _git(self, *args, cwd=None):
        cmd = ['git'] + list(args)
        LOG.debug('[%s]: COMMAND: %s', self.name, ' '.join(cmd))
        rval = subprocess.run(
            cmd,
            capture_output=True,
            cwd=cwd or self.path
        )
        LOG.debug('[%s]: RETURN: %d', self.name, rval.returncode)
        if rval.stdout:
            LOG.debug('[%s]: STDOUT: %s', self.name, rval.stdout.decode().strip())
        if rval.stderr:
            LOG.debug('[%s]: STDERR: %s', self.name, rval.stderr.decode().strip())
        rval.check_returncode()
        return str(rval.stdout.strip(), 'utf-8')

    @property
    def repo_parent_dir(self):
        return self.path.removesuffix(self.name)

    @property
    def commit(self):
        return self._git('rev-parse', 'HEAD')

    @State.update(success=State.DIRTY)
    def is_dirty(self):
        try:
            self._git('diff-files', '--quiet')
        except:
            return True
        else:
            return False

    @property
    @State.update(failure=State.NO_VERSION)
    def version(self):
        return self.required

    @State.update(success=State.VALID, failure=State.WRONG_VERSION)
    def valid_version(self):
        return self.version == self.commit

    @State.update(success=State.UPDATED)
    def pull(self):
        return self._git('pull')

    @State.update(success=State.CLONED, failure=State.CLONE_FAILURE)
    def clone(self):
        LOG.debug('Clogning: %s', self.src)
        try:
            self._git(
                'clone',
                self.src, self.name,
                cwd=self.repo_parent_dir
            )
        except Exception as ex:
            LOG.error('Clone failed: %s', ex.stderr.decode())
            return False
        return True

    @property
    def path(self):
        return path.join(ANSIBLE_ROLES_PATH, self.name)

    @State.update(success=State.EXISTS, failure=State.MISSING)
    def exists(self):
        return path.isdir(self.path)


def parse_args():
    parser = argparse.ArgumentParser(
        description=HELP_DESCRIPTION, epilog=HELP_EXAMPLE
    )

    parser.add_argument('-f', '--filter', default='',
                        help='Filter role repo names.')
    parser.add_argument('-w', '--workers', default=20, type=int,
                        help='Max workers to run in parallel.')
    parser.add_argument('-l', '--log-level', default='INFO',
                        help='Logging level.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--install', action='store_true',
                       help='Clone and update required roles.')
    group.add_argument('-c', '--check', action='store_true',
                       help='Only check roles, no installing.')

    args = parser.parse_args()

    assert args.install or args.check, \
        parser.error('Pick one: --install or --check')

    return args


def handle_role(role, check=False):
    LOG.debug('[%s]: Processing role...', role.name)
    if not role.exists():
        if not check:
            role.clone()
        return role

    if role.valid_version():
        return role

    if role.is_dirty():
        return role

    if not check:
        role.pull()
    return role


def main():
    args = parse_args()

    LOG.setLevel(args.log_level.upper())

    # Verify Ansible version is 2.8 or newer.
    if version.parse(ansible.__version__) < version.parse("2.8"):
        LOG.error('Your Ansible version is lower than 2.8. Upgrade it.')
        exit(1)

    # Read Ansible requirements file.
    with open(path.join(SCRIPT_DIR, 'requirements.yml'), 'r') as f:
        requirements = yaml.load(f, Loader=yaml.FullLoader)

    roles = [
        Role.from_requirement(req)
        for req in requirements
        if args.filter in req['name']
    ]

    # Check if each Ansible role is installed and has correct version.
    with futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        these_futures = [
            executor.submit(handle_role, role, args.check)
            for role in roles
        ]

        for result in futures.as_completed(these_futures):
            role = result.result()
            LOG.info('%-32s - %s' % (role.name, role.state))

    fail_states = set([
        State.DIRTY,
        State.MISSING,
        State.WRONG_VERSION
    ])
    if fail_states.intersection([r.state for r in roles]):
        exit(1)

if __name__ == "__main__":
    main()
