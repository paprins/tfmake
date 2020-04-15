import os
import click
from jinja2 import Environment, PackageLoader
import yaml
import json

from tfmake import __version__
from outdated import check_outdated

from tfmake.custom import DefaultCommandHandler, DefaultCommandGroup

env = Environment(
    loader=PackageLoader('tfmake', 'templates')
)

@click.group(cls=DefaultCommandGroup)
@click.version_option(version=__version__)
def main():
    is_outdated, latest_version = check_outdated('tfmake', __version__)

    if is_outdated:
        _msg = '* Your version of tfmake is out of date! Your version is {}, the latest is {} *'.format(__version__, latest_version)
        
        click.echo('\n' + ('* ' * 43))
        click.echo(_msg)
        click.echo('* ' * 43)    

@main.command(name='azure')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def azure(target, args):
    '''
    Use Azure provider
    '''
    DefaultCommandHandler('azure').call(target, args)

@main.command(name='guess', default_command=True)
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def guess(target, args):
    '''
    Default command that guesses what provider you're using.
    '''
    DefaultCommandHandler().call(target, args)

@main.command(name='aws')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def aws(target, args):
    '''
    Use AWS provider.
    '''
    DefaultCommandHandler('aws').call(target, args)

@main.command()
@click.argument('provider', default='aws')
def init(provider):
    '''
    Create configuration for provider.
    '''
    cwd = os.path.join(os.getcwd(), '.tfmake')
    if os.path.isfile(cwd):
        click.confirm('Existing configuration found! Do you want to continue?', abort=True)

    # Get provider-specific template
    # NOTE: this is for future use ... not used yet
    template = env.get_template('tfmake.{}.j2'.format(provider))

    with open(cwd, 'w+') as f:
        f.write(template.render(provider=provider))

    click.echo("\nConfiguration written to '{}'".format(cwd))

if __name__ == '__main__':
    main()

