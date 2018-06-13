import os.path

from invoke import task


TERRAFORM_VERSION = '0.11.7'
@task
def install(c, version=TERRAFORM_VERSION):
    file = f'terraform_{version}_linux_amd64.zip'

    with c.cd('deploy/terraform'):
        if os.path.exists('terraform'):
            print('Terraform file found')
            return

        print(f'Downloading Terraform {version}')
        c.run(f'wget -q https://releases.hashicorp.com/terraform/{version}/{file}')
        c.run(f'unzip {file}')
        c.run(f'rm {file}')


@task
def init(c):
    with c.cd('deploy/terraform'):
        c.run('./terraform init')


@task
def modules(c):
    print('Downloading Terraform modules')
    with c.cd('deploy/terraform'):
        c.run('./terraform get')


@task
def plan(c):
    with c.cd('deploy/terraform'):
        c.run('./terraform plan')

@task
def apply(c):
    with c.cd('deploy/terraform'):
        c.run('./terraform apply')

@task
def destroy(c):
    with c.cd('deploy/terraform'):
        c.run('./terraform destroy')
