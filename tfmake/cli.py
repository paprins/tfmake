import os
import click

from tfmake import __version__

@click.command()
@click.version_option(version=__version__)
@click.option('-f', '--file', envvar='TF_MAKEFILE', default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Makefile'), help='Path to Makefile (defaults to bundled Makefile)')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def main(file, target, args):
    """
    Super fancy wrapper for our Terraform Makefile ;)
    """
    if not os.path.isfile(file):
        click.echo('Your {file} not found :('.format(file=file))
        os.sys.exit(1)

    _args = list(args)

    if len(_args) > 0:
        os.system("make -f {file} {target} {args}".format(file=file, target=target, args=' '.join(_args)))
    else:
        os.system("make -f {file} {target}".format(file=file, target=target))

if __name__ == '__main__':
    main()