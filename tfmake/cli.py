import os
import click

from tfmake import __version__

from tfmake.custom import DefaultCommandGroup

def call(provider, target, args):
    '''
    Call provider specific Makefile using target and (optional) args.
    '''
    makefile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Makefile.{}'.format(provider))

    if not os.path.isfile(makefile):
        click.echo("Makefile '{}' not found :(".format(makefile))
        os.sys.exit(1)

    _args = list(args)

    if len(_args) > 0:
        os.system("make -f {file} {target} {args}".format(file=makefile, target=target, args=' '.join(_args)))
    else:
        os.system("make -f {file} {target}".format(file=makefile, target=target))

@click.group(cls=DefaultCommandGroup)
@click.version_option(version=__version__)
def main():
    pass

@main.command(name='azure')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def azure(target, args):
    call('azure', target, args)

@main.command(name='aws', default_command=True)
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def aws(target, args):
    call('aws', target, args)

if __name__ == '__main__':
    main()