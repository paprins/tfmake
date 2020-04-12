import os
import re
import subprocess
import inspect
from functools import wraps
import yaml
import click

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

        _c = os.path.join(os.getcwd(), '.tfmake')

        if os.path.isfile(_c):
            with open(_c) as f:
                try:
                    self.config = yaml.safe_load(f)
                except yaml.parser.ParserError:
                    os.sys.exit('[ERROR] {} could not be parsed.'.format(_c))

        if not provider and self.config:
            self.provider = self.config.get('provider','aws').lower()
        else:
            self.provider = provider or 'aws'

        if self.config:
            _provider = self.config.get('provider','aws').lower()
            if not self.provider == _provider:
                raise click.ClickException("Hmmm ... you configured '{}' and you provided '{}' ... make up your mind!\n\n\n\n\n... please".format(_provider, self.provider))

    @before_and_after
    def call(self, target, args):
        '''
        Call provider specific Makefile using target and (optional) args.
        '''
        makefile = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../Makefile.{}'.format(self.provider))

        if not os.path.isfile(makefile):
            click.echo("Makefile '{}' not found :(".format(makefile))
            os.sys.exit(1)

        _args = list(args)

        if len(_args) > 0:
            os.system("make -f {file} {target} {args}".format(file=makefile, target=target, args=' '.join(_args)))
        else:
            os.system("make -f {file} {target}".format(file=makefile, target=target))

    def before(self):
        '''
        Uses configuration to 'prepare' call to Makefile by setting environment variables and 
        executing arbitrary commands.
        '''
        if not self.config: 
            return

        for e in self.config.get('environment', []):
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
                    raise click.ClickException('Exception when executing command: "{}":\n\n{}'.format(cmd, e.output))

            else:
                os.environ[k] = v

        # process pre actions
        for pre in self.config.get('before', []):
            os.system(pre)

    def after(self):
        '''
        Uses configuration to 'cleanup' after call to Makefile by executing arbitrary commands.
        '''
        if not self.config: 
            return

        for post in self.config.get('after', []):
            os.system(post)