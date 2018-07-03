# Stellar Network Infrastructure Orchestartion

This directory is responsible for launching a new Stellar network from scratch.
At Kin TLV we are using Terraform with a bit of Jinja2 templating to achieve this,
so being familiar with the above is a requirement.

## Executing Actions

Terraform is a complex tool, and its HCL language has some limitation,
most specfically looping over modules.
To solve this we are using pyinvoke and Jinja2 templates to generate Terraform `.tf` files
before calling the `terraform ...` command.

Thus, all executions involve calling `invoke plan/apply/destroy/etc` instead of `terraform plan/apply/destroy/etc`.

## File Structure

- [tasks.py](tasks.py) automates the flow of processing templates and calling various `terraform ...` commands.
It is written in Python using pyinvoke and is called using `invoke ...` command. See the file for various targets.
- [vars.yml](vars.yml) includes the parameters that define the network topology e.g. amount of cores and horizons to launch, network name, etc.
This file is used in processing the `.tf.j2` Jinja2 templates to product `.tf` files.
- Terraform state is cached in a special private bucket on S3. See [state.tf.j2](state.tf.j2) for more information.

## Launch

- Generate .pem keys for SSHing into the instances that will be launched and place them in the root directory.
- Generate the RDS password for the RDS instances. This password is given to Jinja2 for template processing via the environment variable `RDS_PASSWORD`.
Currently this environment variable must be set on every call to `invoke ...`
- Update [vars.yml](vars.yml) with the new network parameters.
- call `invoke new-workspace` to initialize the new network Terraform state on S3:
```
RDS_PASSWORD='xxx' invoke new-workspace
```
- call `invoke plan` to see a plan the resources that will be launched and
verify everything is in place:
```
RDS_PASSWORD='xxx' invoke plan
```
- call `invoke apply` to execute the plan you saw when calling `invoke plan`

## Input for Ansible

After launching the infrastructure, Terraform will output a list of addresses and other information.
This is required for Ansible to deploy Stellar Core and Horizon on the newly launched infrastructure.
See documentation in (../ansible/](../ansible) for additional information.
