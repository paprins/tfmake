# tfmake

## Hello ! 👋

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

Usage: make <TARGET> (env=<ENVIRONMENT>) (<TERRAFORM ARGUMENTS>)

Where:
 ENVIRONMENT is one of ['dev','tst','acc','qas','prd','run']
 TARGET is one:
    update                          Update terraform modules and providers
    select                          Select and initialize terraform workspace (aka 'stage')
    show                            Show current terraform workspace
    plan                            Generate and show an execution plan
    apply                           Builds or changes infrastructure
    destroy                         Destroy Terraform-managed infrastructure
    refresh                         Refresh terraform state
    import                          Import existing infrastructure into your Terraform state

Note:

 - parameter 'env' is only required when selecting an environment
 - <TERRAFORM ARGUMENTS> can be used to pass arbitrary terraform parameters (without a prefix dash). Example: "make apply input=false no-color auto-approve"
```

> Use `tfmake azure help` to see the `azure` edition ...

## Workspace Prefix

When selecting an environment, by default, the following naming convention is used to store the `terraform` state:

```
<ACCOUNT_ALIAS>/<TERRAFORM_S3_KEY>
```

Where:
* `ACCOUNT_ALIAS` is the alias of the account you're using (either: AWS or Azure)
* `TERRAFORM_S3_KEY` is the value of the `key` in `terraform.tf`

If you want something in-between the alias and the key, you can use the 'workspace prefix' like this:
> Only needed when using the `select` command!

```
$ aws-vault exec my-aws-account -- tfmake select env=dev --workspace-key-prefix foo/bar
```

After you `select`ed the environment, the path to your `terraform` state is:

```
<ACCOUNT_ALIAS>/<WORKSPACE_PREFIX>/<TERRAFORM_S3_KEY>
```

Assuming the `key` value is `whatever/terraform.tfstate`, this leads to: `my-aws-account/foo/bar/whatever/terraform.tfstate`


## Safeguarding Credentials
> This works for both `AWS` and `Azure`

Although, you have to provide the correct credentials yourself, `tfmake` _will_ check if the credentials you provide are expected.

```
$ cd /path/to/my/tf/project
$ aws-vault exec ACCOUNT_ONE -- tfmake select env=dev
Initializing modules...
...
>>> Now using Terraform workspace 'dev' on AWS account 'aws-account-one' ...
```

If you use different credentials the next time you use `tfmake` in this project, you'll see a warning. Press `<ENTER>` to abort (or `y` to continue).

```
$ cd /path/to/my/tf/project
$ aws-vault exec ACCOUNT_TWO -- tfmake plan
[WARNING] You previously used 'aws-account-one' for provider aws. Now you're using 'aws-account-two'. Are you sure? [y/N]:
Aborted!
```

> The 'magic' behind all this is a cache stored in `$(PWD)/.tfmake/cache`. So, if you delete this file, this safeguard won't work anymore :(

## Auto-switching Credentials on Azure

When you're using `Azure` _and_ installed [`azctx`](https://github.com/StiviiK/azctx), `tfmake` will use the cached credentials to automatically switch to the correct subscription.

In your `.tfmake/config`, make sure you enabled `auto_switching`:
```
---
provider: azure
auto_switch: True

environment:
  - ARM_ACCESS_KEY = $(az keyvault secret show --name YOUR_SECRET --vault-name YOUR_VAULT --query value -o tsv)
```

> Support for `AWS` will follow in a future version of `tfmake`

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

> Plan changes with plan file
```
$ aws-vault exec foobar -- tfmake plan out=foobar.plan
```

> Apply changes
```
$ aws-vault exec foobar -- tfmake apply
```

> Apply changes using plan file
```
$ aws-vault exec foobar -- tfmake apply input=false auto-approve foobar.plan
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
$ aws-vault exec foobar -- tfmake apply input=false no-color auto-approve'
```

**Note**: you can use arbitrary Terraform arguments after the command you're executing (~ in this example: `apply`). So, in this example, `input=false no-color auto-approve` will be used to create the following `terraform` arguments: `-input=false -no-color -auto-approve`.

Notice that you have to skip the dash in front of each argument.

**Another Note**: :arrow_up ... this only applies when using `tfmake` ... if, for whatever reason, you choose to use the `Makefile` directly: run `make help`

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

### Example

> Azure

The following example configuration creates an environment variable using a specified secret from a given key vault. Then, it will execute all `before` statements. Next it will just execute the `Makefile` target. And finally, it will execute all `after` statements.

Please note that the `environment` variables will _not_ be exposed system-wide. They will only be 'visible' within the context of the session. As a result, `terraform` can use it, but when the process is done, the variable will no longer be available.

```
---
provider: azure

environment:
    - ARM_ACCESS_KEY = $(az keyvault secret show --name YOUR_SECRET --vault-name YOUR_VAULT --query value -o tsv)

before:
    - echo $ARM_ACCESS_KEY

after:
    - echo "DONE!!"
```

~ the end
