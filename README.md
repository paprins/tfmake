# tfmake

This is a Python based wrapper around an opionated `Makefile` I use for `terraform` projects. 

You still need `make`, though. The main advantage is that you don't have to copy the `Makefile`. 

## DISCLAIMER
This module includes a highly opinionated `Makefile` implementation. It's working very well for us, but your requirements might be different.

Also, ... we use Amazon AWS as our go-to Cloud Provider. Because we work in a multi-account environment, the bundled `Makefile` uses the AWS account alias to ensure the path to the Terraform state file is unique.

As a result, this module expects the correct AWS credentials to be available. I use [`aws-vault`](https://github.com/99designs/aws-vault) to manage my AWS credentials.

## Install

```
$ pip install tfmake
```

## Usage
> Here's the help for the wrapper
```
$ tfmake --help

Usage: tfmake [OPTIONS] [TARGET] [ARGS]...

  Super fancy wrapper for our Terraform Makefile ;)

Options:
  -f, --file TEXT  Path to Makefile (defaults to bundled Makefile)
  --help           Show this message and exit.
```

**Note**: by default it uses the bundled `Makefile`. If, for whatever reason you would like to use a different version, use the `--file` option.

> Here's the help for the Makefile
```
$ tfmake

Usage: make <TARGET> (env=<ENVIRONMENT>) (args=<TERRAFORM ARGUMENTS>)

Where:
	- ENVIRONMENT is one of ['dev','tst','acc','prd']
	- TARGET is one:
update                          Update terraform modules and providers
select                          Select and initialize terraform workspace (aka 'stage')
show                            Show current terraform workspace
plan                            Generate and show an execution plan
apply                           Builds or changes infrastructure
destroy                         Destroy Terraform-managed infrastructure
refresh                         Refresh terraform state

Note:

- parameter 'env' is only required when selecting an environment
- parameter 'args' can be used to pass terraform understandable arguments. Example: "make apply args='-input=false -no-color -auto-approve'"
```

## Example

> Initialise 'dev' environment
```
$ aws-vault exec foobar -- tfmake select env=dev
```

> Plan changes
```
$ aws-vault exec foobar -- tfmake plan
```

> Apply changes
```
$ aws-vault exec foobar -- tfmake apply
```

> Apply changes ... automagically
```
$ aws-vault exec foobar -- tfmake apply args='-no-color -auto-approve'
```

**Note**: the `args` parameter can be used for arbitrary Terraform arguments.

~ the end