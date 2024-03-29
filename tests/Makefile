.PHONY := all tf_init tf_workspace tf_options tf_info aws_account_info
.DEFAULT_GOAL := help

SUPPORTED_ENVS = dev tst acc qas prd run sbx
REQUIRED_BINS = terraform jq aws
env           ?= $(shell terraform workspace show)

WHITE := '\033[0;37m'
BLUE  := '\033[0;34m'
GREEN := '\033[0;32m'
RED   := '\033[0;31m'

all: check_prerequisites

help:
	@echo "Usage: make <TARGET> (env=<ENVIRONMENT>) (args=<TERRAFORM ARGUMENTS>)\n"
	@echo "Where:"
	@echo "\t- ENVIRONMENT is one of ['dev','tst','acc','qas','prd','run','sbx']"
	@echo "\t- TARGET is one:"
	@awk -F ':|##' '/^[^\t].+?:.*?##/ {printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF }' $(MAKEFILE_LIST)
	@echo "\nNote:\n"
	@echo "- parameter 'env' is only required when selecting an environment"
	@echo "- parameter 'args' can be used to pass terraform understandable arguments. Example: \"make apply args='-input=false -no-color -auto-approve'\""

check_prerequisites:
K := $(foreach bin,$(REQUIRED_BINS), \
		$(if $(shell which $(bin)),,$(error Before you continue, please install '$(bin)')))

tf_validate:
ifeq ($(filter $(env),$(SUPPORTED_ENVS)),)
	$(error Environment '$(env)' is not supported! Valid options are '$(SUPPORTED_ENVS)')
endif

aws_account_info:
	$(eval AWS_ACCOUNT_ID=$(shell aws sts get-caller-identity --output text --query 'Account'))
	$(eval AWS_ACCOUNT_ALIAS=$(shell aws iam list-account-aliases --output text --query 'AccountAliases[*]'))

tf_init: aws_account_info
	@if [ -e .terraform/environment ]; then rm .terraform/environment; fi;
	@if [ -e .terraform/terraform.tfstate ]; then rm .terraform/terraform.tfstate; fi;
	@terraform init -backend-config 'workspace_key_prefix=$(AWS_ACCOUNT_ALIAS)'

tf_options:
	$(if $(wildcard vars/$(env).tfvars), $(eval TF_OPTIONS := $(TF_OPTIONS) -var-file "vars/$(env).tfvars"))

tf_workspace:
	@terraform workspace select $(env) 2> /dev/null || terraform workspace new $(env)

tf_info: aws_account_info
	@echo "\n\nUsing workspace '$(env)' on '$(AWS_ACCOUNT_ALIAS)' ...\n\n"

foobar: ## Just checking if this works
	@echo "FOOBAR"

update: ## Update terraform modules and providers
	@terraform get -update=true 

select: tf_validate tf_init tf_workspace ## Select and initialize terraform workspace (aka 'stage')
	@echo $(GREEN)"\n\n>>> Now using Terraform workspace '$(env)' on AWS account '$(AWS_ACCOUNT_ALIAS)' ..."$(WHITE)

show: aws_account_info ## Show current terraform workspace
	$(eval CURRENT_WORKSPACE=$(shell terraform workspace show))
	@echo $(GREEN)"\nCurrently using Terraform workspace '$(CURRENT_WORKSPACE)' on AWS account '$(AWS_ACCOUNT_ALIAS)' ..."$(WHITE)

plan: tf_validate tf_options tf_info ## Generate and show an execution plan
	@terraform $@ $(TF_OPTIONS) $(args)

apply: tf_validate tf_options tf_info ## Builds or changes infrastructure
	@terraform $@ $(TF_OPTIONS) $(args)
	@terraform output -no-color -json 2> /dev/null | jq 'with_entries(.value |= .value)' > tf.${env}.outputs.json

destroy: tf_validate tf_options tf_info ## Destroy Terraform-managed infrastructure
	@terraform $@ $(TF_OPTIONS) $(args)

refresh: tf_validate tf_options tf_info ## Refresh terraform state
	@terraform $@ $(TF_OPTIONS) $(args)
