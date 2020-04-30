import os
import re
import subprocess
from enum import Enum
import inspect
from functools import wraps
import yaml
import click

from tfmake import __version__
from outdated import check_outdated

class Provider(Enum):
    AWS   = 'aws'
    AZURE = 'azure'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_ 

    @classmethod
    def to_list(cls):
        return cls._value2member_map_.keys()

    @classmethod
    def to_string(cls):
        return ", ".join(cls._value2member_map_.keys())

class Workspace(Enum):
    DEV = 'dev'
    TST = 'tst'
    ACC = 'acc'
    PRD = 'prd'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def to_string(cls):
        return ", ".join(cls._value2member_map_.keys())

class DefaultCommandGroup(click.Group):
    '''
    Allow a default command for a group
    '''

    def command(self, *args, **kwargs):
        default_command = kwargs.pop('default_command', False)
        if default_command and not args:
            kwargs['name'] = kwargs.get('name', '<>')
        decorator = super(
            DefaultCommandGroup, self).command(*args, **kwargs)

        if default_command:
            def new_decorator(f):
                cmd = decorator(f)
                self.default_command = cmd.name
                return cmd

            return new_decorator

        return decorator

    def resolve_command(self, ctx, args):
        try:
            # test if the command parses
            return super(
                DefaultCommandGroup, self).resolve_command(ctx, args)
        except click.UsageError:
            # command did not parse, assume it is the default command
            args.insert(0, self.default_command)
            return super(
                DefaultCommandGroup, self).resolve_command(ctx, args)

def check_latest_version(f):
    @wraps(f)
    def wrapper(self, *args, **kw):
        is_outdated = False
        latest_version = __version__
        try:
            is_outdated, latest_version = check_outdated('tfmake', __version__)

        except ValueError as e:
            click.echo("\nYour version of tfmake is ahead of time! {}".format(str(e)))

        if is_outdated:
            _msg = '* Your version of tfmake is out of date! Your version is {}, the latest is {} *'.format(__version__, latest_version)
            
            click.echo('\n' + ('* ' * 43))
            click.echo(_msg)
            click.echo('* ' * 43)   

        return f(self, *args, **kw)

    return wrapper

def before_and_after(f):
    @wraps(f)
    def wrapper(self, *args, **kw):
        if hasattr(self, 'before') and inspect.ismethod(self.before):
            self.before()
        result = f(self, *args, **kw)
        if hasattr(self, 'after') and inspect.ismethod(self.after):
            self.after()
        return result
    return wrapper

class DefaultCommandHandler(object):
    def __init__(self, provider = None):
        self.config = None

        base    = os.path.join(os.getcwd(), '.tfmake')

        if os.path.isfile(base):
            raise click.ClickException("Legacy configuration found! Run 'tfmake init' first.")

        if not os.path.isdir(base):
            os.mkdir(base)

        _config = os.path.join(base, 'config')
        _cache  = os.path.join(base, 'cache')

        if os.path.isfile(_config):
            with open(_config, 'r') as f:
                try:
                    self.config = yaml.safe_load(f)
                except yaml.parser.ParserError:
                    os.sys.exit('[ERROR] {} could not be parsed.'.format(_config))

        if not provider and self.config:
            self.provider = self.config.get('provider','aws').lower()
        else:
            self.provider = provider or 'aws'

        if self.config:
            _provider = self.config.get('provider','aws').lower()
            if not self.provider == _provider:
                raise click.ClickException("hmmm ... you configured '{}' and provided '{}' ... make up your mind!\n\n\n... please".format(_provider, self.provider))

        # Check if provider is valid
        if not Provider.has_value(self.provider):
            raise click.ClickException("Invalid provider '{}' (expecting: {})".format(self.provider, Provider.to_string()))

        # Check cache
        if os.path.isfile(_cache):
            with open(_cache, 'r') as f:
                try:
                    self.cache = yaml.safe_load(f)
                except yaml.parser.ParserError:
                    os.sys.exit('[ERROR] {} could not be parsed.'.format(_cache))
        else:
            self.cache = dict()

    def __get_environment(self, target, args=[]):
        """
        Get environment via 'select' target or terraform cli.
        """
        if target == "select":
            _args = dict(item.split("=") for item in args) 
            if 'env' in _args:
                environment = _args.get('env')
            else:
                raise click.ClickException("target '{}' expects an argument 'env'.".format(target))
        else:
            try:
                cmd = "terraform workspace show"
                environment = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, universal_newlines=True).strip()

            except subprocess.CalledProcessError as e:
                raise click.ClickException("error executing '{}': {}".format(cmd, str(e)))

            except OSError as e:
                raise click.ClickException("did you install terraform?")

        if not Workspace.has_value(environment):
            raise click.ClickException("environment '{}' is not supported (expecting: {})".format(environment, Workspace.to_string()))

        return environment

    def __get_account_alias(self):
        """
        Get provider account alias.
        Using cli to avoid adding Python dependencies!
        """
        if Provider(self.provider) == Provider.AWS:
            cmd = "aws iam list-account-aliases --query AccountAliases[*] --output text"
        elif Provider(self.provider) == Provider.AZURE:
            cmd = "az account show --query name --output tsv"

        output = None

        try:
            output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, universal_newlines=True)

        except subprocess.CalledProcessError as e:
            raise click.ClickException("error fetching {} account alias. You sure you're using the correct credentials?".format(self.provider))

        except OSError as e:
            raise click.ClickException("error fetching account alias. Did you install the '{}' command-line interface?".format(self.provider))

        return output.strip()

    def __write_to_cache(self, k, v):
        """
        Writing cache to fs
        """
        self.cache[k] = v
        _cache = os.path.join(os.getcwd(), '.tfmake', 'cache')

        with open(_cache, 'w+') as f:
            yaml.dump(self.cache, f, default_flow_style=False, explicit_start=True)

    def __read_from_cache(self, k):
        """
        Get value from cache
        """
        return self.cache.get(k, None)

    @check_latest_version
    @before_and_after
    def call(self, target, args, **kwargs):
        '''
        Call provider specific Makefile using target and (optional) args.
        '''
        makefile = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../Makefile.{}'.format(self.provider))

        if not os.path.isfile(makefile):
            click.echo("Makefile '{}' not found :(".format(makefile))
            os.sys.exit(1)

        _args = list(args)

        env = self.__get_environment(target, args)
        alias = self.__get_account_alias()

        # read from cache
        cached_alias = self.__read_from_cache(env)

        if cached_alias and alias != cached_alias:
            click.confirm("\n[WARNING] You previously used '{}' for provider {}. Now you're using '{}'. Are you sure?".format(cached_alias, self.provider, alias), abort=True)

        if len(_args) > 0:
            os.system("make -f {file} {target} {args}".format(file=makefile, target=target, args=' '.join(_args)))
        else:
            os.system("make -f {file} {target}".format(file=makefile, target=target))

        # write to cache
        self.__write_to_cache(env, alias)
        

    def before(self):
        '''
        Uses configuration to 'prepare' call to Makefile by setting environment variables and 
        executing arbitrary commands.
        '''
        if not self.config: 
            return

        for e in self.config.get('environment', []) or []:
            k,v = map(str.strip, e.split('='))
            # Value 'v' could still contain hashtag to comment out rest of line
            v = v.split('#',1)[0]
            if v.startswith('$(') and v.endswith(')'):
                try:
                    pattern = "\$\((.*?)\)"
                    cmd = re.search(pattern, v).group(1) # get substring between $(...)

                    output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, universal_newlines=True)
                    os.environ[k] = output

                except subprocess.CalledProcessError as e:
                    raise click.ClickException('exception when executing command: "{}":\n\n{}'.format(cmd, e.output))

            else:
                os.environ[k] = v

        # process pre actions
        for pre in self.config.get('before', []) or []:
            os.system(pre)

    def after(self):
        '''
        Uses configuration to 'cleanup' after call to Makefile by executing arbitrary commands.
        '''
        if not self.config: 
            return

        for post in self.config.get('after', []) or []:
            os.system(post)