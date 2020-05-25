import os
import click
from jinja2 import Environment, PackageLoader
import yaml
import json

from tfmake import __version__

from tfmake.custom import DefaultCommandHandler, DefaultCommandGroup

env = Environment(
    loader=PackageLoader('tfmake', 'templates')
)

@click.group(cls=DefaultCommandGroup)
@click.version_option(version=__version__)
def main():
    pass

@main.command(name='azure')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
@click.option('--dry-run', is_flag=True, default=False)
def azure(target, args, dry_run):
    '''
    Use Azure provider
    '''
    DefaultCommandHandler('azure').call(target, args, dry_run)

@main.command(name='guess', default_command=True)
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
@click.option('--dry-run', is_flag=True, default=False)
def guess(target, args, dry_run):
    '''
    Default command that guesses what provider you're using.
    '''
    DefaultCommandHandler().call(target, args, dry_run)

@main.command(name='aws')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
@click.option('--dry-run', is_flag=True, default=False)
def aws(target, args, dry_run):
    '''
    Use AWS provider.
    '''
    DefaultCommandHandler('aws').call(target, args, dry_run)

@main.command()
@click.argument('provider', default='aws')
def init(provider):
    '''
    Create configuration for provider (migrate if needed).
    '''
    legacy = None
    cwd = os.path.join(os.getcwd(), '.tfmake')
    if os.path.isfile(cwd):
        if click.confirm('Legacy configuration found! Do you want me to migrate?', default=True):
            with open(cwd,'r') as f:
                legacy = f.read()

        os.rename(cwd, '{}.bkp'.format(cwd))

    if not os.path.isdir(cwd):
        os.mkdir(cwd)

    config = os.path.join(cwd, "config")
    if os.path.isfile(config):
        click.confirm('Existing configuration found! Do you want to continue?', abort=True)

    # Get provider-specific template (this is for future use ... not used yet)
    template = env.get_template('tfmake.{}.j2'.format(provider))

    contents = legacy if legacy else template.render(provider=provider)

    with open(config, 'w+') as f:
        f.write(contents)

    if legacy and os.path.isfile('{}.bkp'.format(cwd)):
        if click.confirm('\n\nSuccessfully migrated configuration. Delete backup?', default=True):
            os.remove('{}.bkp'.format(cwd))

    click.echo("\nConfiguration written to '{}'".format(config))

if __name__ == '__main__':
    main()

