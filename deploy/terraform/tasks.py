"""Call various Terraform actions."""
import os
import os.path

from invoke import task
import jinja2
import yaml


TERRAFORM_VERSION = '0.11.7'


@task
def install(c, version=TERRAFORM_VERSION):
    """Download a local version of Terraform."""
    file = f'terraform_{version}_linux_amd64.zip'

    if os.path.exists('terraform'):
        print('Terraform file found')
        return

    print(f'Downloading Terraform {version}')
    c.run(f'wget -q https://releases.hashicorp.com/terraform/{version}/{file}')
    c.run(f'unzip {file}')
    c.run(f'rm {file}')


MAIN_TF_FILE = 'stellar-network.tf'


@task
def template(c,
             template_file=f'{MAIN_TF_FILE}.j2',
             vars_file='vars.yml',
             out_file=MAIN_TF_FILE):
    """Process Terraform file taht require templating.

    Terraform and HCL has limitations that can be easily solved using template
    languages like Jinja.

    For example, avoiding redundancy when calling a module multiple times with
    just a single different variable value every time.
    """
    print('generating terraform file from template')

    with open(vars_file) as f:
        variables = yaml.load(f)

    with open(template_file) as f:
        tmplate = jinja2.Template(f.read())

    out = tmplate.render(variables, env_vars=os.environ)

    with open(out_file, 'w') as f:
        f.write(out)

    c.run(f'./terraform fmt {out_file}')


@task(template)
def init(c):
    """Call terraform init."""
    print('initializing')
    c.run('./terraform init')


@task(init)
def modules(c):
    """Call terraform get."""
    print('getting modules')
    c.run('./terraform get')


@task(modules, template)
def plan(c, destroy=False):
    """Call terraform plan."""
    print('planning')
    c.run('./terraform plan {}'.format('-destroy' if destroy else ''))


@task(modules, template)
def apply(c, yes=False):
    """Call terraform destroy."""
    print('applying')
    c.run('./terraform apply {}'.format('-auto-approve' if yes else ''))


@task(modules, template)
def destroy(c, yes=False):
    """Call terraform destroy."""
    print('destroying')
    c.run('./terraform destroy {}'.format('-auto-approve' if yes else ''))
