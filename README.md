# tfmake

This is a Python based wrapper around an opionated `Makefile` I use for multi-cloud/cross-account `terraform` projects. 

You still need `make`, though. The main advantage is that you don't have to copy the `Makefile`. 

## DISCLAIMER
This module includes a highly opinionated `Makefile` implementation. It's working very well for us, but your requirements might be different.

Also, I've done my best to make this thing work on both MacOS and Linux. If you get an error message (~ and my colleagues haven't beat you to it) ... please get in touch and/or create a PR.

## Install

```
$ pip install tfmake
```

## Usage
> Here's the help for the wrapper
```
$ tfmake --help
Usage: tfmake [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  aws    Use AWS provider.
  azure  Use Azure provider
  guess  Default command that guesses what provider you're using.
  init   Create configuration for provider.
```

A warning will be shown when your `tfmake` is out-of-date. If you see one, please update: `pip install --upgrade tfmake` 

## Providers
Currently, `tfmake` supports two providers: `aws` and `azure`. The default provider is `aws`. Depending on the selected provider, a different, provider specific, `Makefile` is used to wrap `terraform`. Here, the provider is selected by using the right command.

See 'examples' for some ... examples.

Each provider leads to a specific `Makefile`. For example: `provider==azure` leads to using `Makefile.azure`.

## Provider Authentication
The used `Makefile` will _not_ handle authentication. It just assumes you're using an authenticated context.

For, `aws`, I use [`aws-vault`](https://github.com/99designs/aws-vault). For `azure`, I use the [`azure-cli`](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

> Here's the help for the (bundled) Makefile
```
$ tfmake help
The AWS Edition

Usage: make <TARGET> (env=<ENVIRONMENT>) (args=<TERRAFORM ARGUMENTS>)

Where:
 ENVIRONMENT is one of ['dev','tst','acc','prd']
 TARGET is one:
    update                          Update terraform modules and providers
    select                          Select and initialize terraform workspace (aka 'stage')
    show                            Show current terraform workspace
    plan                            Generate and show an execution plan
    apply                           Builds or changes infrastructure
    destroy                         Destroy Terraform-managed infrastructure
    refresh                         Refresh terraform state

Note:

 parameter 'env' is only required when selecting an environment
 parameter 'args' can be used to pass terraform understandable arguments. Example: "make apply args='-input=false -no-color -auto-approve'"
```

> Use `tfmake azure help` to see the `azure` edition ...

## Final Notes

By default, before any a `terraform` command is executed, you will be asked to confirm the usage of the current environment.

```
$ tfmake azure apply

Using workspace 'prd' on 'My_fancy_Azure_Production_subscription'.

Press [ENTER] to continue or [CTRL-C] to stop.
```

Please notice that the prompt shows the selected `terraform` workspace and the alias/name of the provider account.

> Use `TFMAKE_AGREE=1` to auto confirm that prompt ...

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

> Apply changes using the `azure` provider
```
$ az login
# (optionaly set subscription)
$ az account set --subscription=YOUR_SUBSCRIPTION_ID_HERE
$ tfmake azure apply
```

> Apply changes ... automagically
```
$ aws-vault exec foobar -- tfmake apply args='-no-color -auto-approve'
```

**Note**: the `args` parameter can be used for arbitrary Terraform arguments.

## Advanced Usage

You can use a _per_ project configuration file in which you can specify, for example, environment variables and/or arbitrary commands that need to be execute before or after the `make` target.

```
$ tfmake init aws

Configuration written to '/your/current/directory/.tfmake'
```

```
---
#
# Welcome to the wonderful world of TFMAKE!
#
# This file is the main config file for your tfmake project.
# It's very minimal at this point and uses default values.
# You can always add more config options for more control.
#
# Happy Coding!
#
provider: aws

# You can define service wide environment variables here
# Notes:
# - when using commands, dont use single quotes (sorry)
# - commands should be between $( and )
#
# environment:
#    - variable1 = value
#    - variable2 = $(command)

# You can define commands here that are executed _before_ the Make target
# Note: dont use single quotes (sorry)
#
# before:
#    - echo "[INFO] before"

# You can define commands here that are executed _after_ the Make target
# Note: dont use single quotes (sorry)
#
# after:
#    - echo "[INFO] after"%
```

#### Section `provider`
The `provider` section specifies what (default) provider to use for this project. As a result, you don't have to specify it anymore on the command-line.

So, no more `tfmake azure plan`. Instead, just configure the `provider` property and type `tfmake plan`.

#### Section `environment`
The `environment` section can contain a list of environment variables that need to be set before calling the `make` target. 

For example, when using the `azure` provider, you might want to dynamically fetch the value for the `ARM_SAS_TOKEN` or `ARM_ACCESS_KEY` from an Azure Key Vault.

#### Section `before`

The `before` section can contain a list of commands that need to be executed preparing the call to the `make` target.

#### Section `after`

The `after` section can contain a list of commands that you can use to cleanup after calling the `make` target.

~ the end
