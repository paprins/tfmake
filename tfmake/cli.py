import os
import click

from tfmake import __version__

@click.command()
@click.version_option(version=__version__)
@click.option('-p', '--provider', default='aws', type=click.Choice(['aws', 'azure']), help='Using AWS or Azure (default: aws)?')
@click.argument('target', default='help')
@click.argument('args', nargs=-1)
def main(provider, target, args):
    """
    Super fancy wrapper for our Terraform Makefile ;)
    """
    click.echo('Using provider {}'.format(provider))
    makefile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Makefile.{}'.format(provider))
    if not os.path.isfile(makefile):
        click.echo("Makefile '{}' not found :(".format(makefile))
        os.sys.exit(1)

    _args = list(args)

    if len(_args) > 0:
        os.system("make -f {file} {target} {args}".format(file=makefile, target=target, args=' '.join(_args)))
    else:
        os.system("make -f {file} {target}".format(file=makefile, target=target))

if __name__ == '__main__':
    main()