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

class PROVIDER(Enum):
    """
    Supporder providers.
    """
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

class WORKSPACE(Enum):
    """
    Supported workspaces/environments.
    """
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
            click.secho("\nYour version of tfmake is ahead of time! {}".format(str(e)), bold=True)

        if is_outdated:
            _msg = '* Your version of tfmake is out of date! Your version is {}, the latest is {} *'.format(__version__, latest_version)
            
            click.secho('\n' + ('* ' * 43), bold=True)
            click.secho(_msg, bold=True)
            click.secho('* ' * 43, bold=True)

        return f(self, *args, **kw)

    return wrapper

def before_and_after(f):
    @wraps(f)
    def wrapper(self, *args, **kw):
        if hasattr(self, 'before') and inspect.ismethod(self.before):
            self.before(*args)
        result = f(self, *args)
        if hasattr(self, 'after') and inspect.ismethod(self.after):
            self.after(*args, **kw)
        return result
    return wrapper

class DefaultCommandHandler(object):
    def __init__(self, provider = None):
        self.config   = None
        self.switched = False

        # filter os.environ for TFMAKE variables
        self.tfmake_env = {key: value for key, value in os.environ.items() if key.startswith('TFMAKE_')}

        base = os.path.join(os.getcwd(), '.tfmake')

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
        if not PROVIDER.has_value(self.provider):
            raise click.ClickException("Invalid provider '{}' (expecting: {})".format(self.provider, PROVIDER.to_string()))

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

        if target not in ['help','foo'] and not WORKSPACE.has_value(environment):
            raise click.ClickException("environment '{}' is not supported (expecting: {})".format(environment, WORKSPACE.to_string()))

        return environment

    def __get_account_alias(self):
        """
        Get provider account alias.
        Using cli to avoid adding Python dependencies!
        """
        if PROVIDER(self.provider) == PROVIDER.AWS:
            cmd = "aws iam list-account-aliases --query AccountAliases[*] --output text"
        elif PROVIDER(self.provider) == PROVIDER.AZURE:
            cmd = "az account show --query name --output tsv"

        output = None

        try:
            output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, universal_newlines=True)

        except subprocess.CalledProcessError as e:
            raise click.ClickException('error fetching {} account alias.\n{}'.format(self.provider, e.output))
            

        except OSError as e:
            raise click.ClickException('error fetching {} account alias.\n{}'.format(self.provider, e.output))

        return output.strip()

    def __write_to_cache(self, k, v):
        """
        Writing cache to fs
        """
        self.cache[k] = v
        _cache = os.path.join(os.getcwd(), '.tfmake', 'cache')

        with open(_cache, 'w+') as f:
            # yaml.dump(self.cache, f, default_flow_style=False, explicit_start=True)
            yaml.safe_dump(self.cache, f, encoding='utf-8', allow_unicode=True)

    def __read_from_cache(self, k):
        """
        Get value from cache
        """
        return self.cache.get(k, None)

    @check_latest_version
    @before_and_after
    def call(self, target, args, dry_run, workspace_key_prefix, **kwargs):
        '''
        Call provider specific Makefile using target and (optional) args.
        '''
        makefile = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../Makefile.{}'.format(self.provider))

        if not os.path.isfile(makefile):
            click.secho("Makefile '{}' not found :(".format(makefile), fg='red', bold=True)
            os.sys.exit(1)

        _args = list(args)

        # adding prefix '-' for each argument
        # why? because 'click' does _not_ allow a dash in front of an argument value (~ it thinks its an option)
        # 
        # extra: _only_ when arguments are _not_ meant as terraform arguments (ugly ... i know)
        if target in ['select', 'import']:
            _args=' '.join(_args)
        else:
            if 'TFMAKE_APPROVE' in self.tfmake_env and target in ['apply','destroy'] and not 'auto-approve' in _args:
                _args.append('auto-approve')

            # TODO: handle 'terraform plan' files in a better way ... this is f*cking ugly
            ## @START::ugly
            for arg in _args:
                if arg.endswith('.plan'):
                    # move '.plan' to last in list
                    _args.append(_args.pop(_args.index(arg)))

            # prepare terraform arguments: making sure that 'plan' files are not prefixed with a dash (~ `-`)
            _args = "args='{args}'".format(args=' '.join(['-' + arg if not arg.endswith('.plan') or '=' in arg else arg for arg in _args]))
            ## @END::ugly

        env   = self.__get_environment(target, args)
        alias = self.__get_account_alias()

        # # read from cache
        # cached_alias = self.__read_from_cache(env)

        # # besides checking if alias has changed, also check if on Gitlab Runner (if so, don't ask to confirm)
        # if cached_alias and alias != cached_alias and 'CI_JOB_ID' not in os.environ:
        #     click.confirm("\n[WARNING] You previously used '{}' for provider {}. Now you're using '{}'. Are you sure?".format(cached_alias, self.provider, alias), abort=True)

        if workspace_key_prefix:
            os.environ['TFMAKE_KEY_PREFIX'] = workspace_key_prefix

        if len(_args) > 0:
            if not dry_run:
                os.system("make -f {file} {target} {args}".format(file=makefile, target=target, args=_args))
            else:
                click.echo("make -f {file} {target} {args}".format(file=makefile, target=target, args=_args))
        else:
            if not dry_run:
                os.system("make -f {file} {target}".format(file=makefile, target=target))
            else:
                click.echo("make -f {file} {target}".format(file=makefile, target=target))

        # write to cache
        self.__write_to_cache(env, alias)
        

    def before(self, target, args, dry_run, workspace_key_prefix):
        '''
        Uses configuration to 'prepare' call to Makefile by setting environment variables and 
        executing arbitrary commands.
        '''
        if not self.config: 
            return

        # when auto-switch enabled, switch to target Azure subscription using 'azctx'
        env          = self.__get_environment(target, args)
        alias        = self.__get_account_alias()
        cached_alias = self.__read_from_cache(env)

        if self.config.get('auto_switch', False) and PROVIDER(self.provider) == PROVIDER.AZURE:
            click.secho('AutoSwitch enabled for Azure subscriptions (using cached subscription for {} environment)'.format(env), bold=True)
            if cached_alias:
                try:
                    from shutil import which
                    # First, check if 'azctx' is installed
                    azctx = which('azctx')
                    if azctx is not None and self.__get_account_alias() != cached_alias:
                        p = subprocess.run("{} '{}'".format(azctx, cached_alias), 
                            shell              = True,
                            universal_newlines = True,
                            capture_output     = True,
                            text               = True
                        )
                        self.switched = (p.returncode == 0)
                        if self.switched:
                            click.echo(p.stdout)
                        else:
                            raise Exception(p.stderr)

                except Exception as e:
                    raise click.ClickException("switching to Azure subscription '{}': {}".format(cached_alias, str(e)))
        elif cached_alias and alias != cached_alias and 'CI_JOB_ID' not in os.environ:
            # besides checking if alias has changed, also check if on Gitlab Runner (if so, don't ask to confirm)
            click.confirm("\n[WARNING] You previously used '{}' for provider {}. Now you're using '{}'. Are you sure?".format(cached_alias, self.provider, alias), abort=True)

        # first, evaluate environment variables
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
                    raise click.ClickException("exception executing '{}':\n\n{}".format(cmd, e.output))

            else:
                os.environ[k] = v

        # next, run 'before' actions
        for pre in self.config.get('before', []) or []:
            os.system(pre)

    def after(self, target, args, dry_run, workspace_key_prefix):
        '''
        Uses configuration to 'cleanup' after call to Makefile by executing arbitrary commands.
        '''
        if not self.config: 
            return

        if self.switched and PROVIDER(self.provider) == PROVIDER.AZURE:
            # When auto-switch enabled (~ and we actually switched), switch back using 'azctx'
            try:
                from shutil import which
                azctx = which('azctx')
                if azctx is not None:
                    p = subprocess.run('{} -'.format(azctx), 
                        shell              = True,
                        universal_newlines = True,
                        capture_output     = True,
                        text               = True
                    )
                    if p.returncode == 0:
                        click.echo(p.stdout)
                    else:
                        raise Exception(p.stderr)

            except Exception as e:
                raise click.ClickException('switching to previous Azure subscription: {}'.format(str(e)))

        # run 'after' actions
        for post in self.config.get('after', []) or []:
            os.system(post)