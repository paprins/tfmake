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
  aws
  azure
```

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

~ the end