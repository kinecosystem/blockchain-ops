"""Call various Terraform actions."""
import os
import os.path

from invoke import task
import jinja2
import yaml


TERRAFORM_VERSION = '0.11.7'


@task
def install(c, ostype='linux', version=TERRAFORM_VERSION):
    """Download a local version of Terraform."""
    if ostype == 'mac':
        ostype = 'darwin'

    file = f'terraform_{version}_{ostype}_amd64.zip'

    if os.path.exists('terraform'):
        print('Terraform file found')
        return

    print(f'Downloading Terraform {version}')
    c.run(f'wget -q https://releases.hashicorp.com/terraform/{version}/{file}')
    c.run(f'unzip {file}')
    c.run(f'rm {file}')


MAIN_TF_FILE = 'stellar-network.tf'


@task
def template(c, vars_file='vars.yml'):
    """Process Terraform file taht require templating.

    Terraform and HCL has limitations that can be easily solved using template
    languages like Jinja.

    For example, avoiding redundancy when calling a module multiple times with
    just a single different variable value every time.
    """
    print('generating terraform files from templates')

    with open(vars_file) as f:
        variables = yaml.load(f)

    for root, _, files in os.walk("."):
        for file in files:
            stripped_file, ext = os.path.splitext(file)

            if ext != '.j2':
                continue

            out_file = f'{root}/{stripped_file}'
            print(f'processing file {root}/{file}')

            with open(f'{root}/{file}') as f:
                tmplate = jinja2.Template(f.read(), extensions=['jinja2.ext.do'])

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
def new_workspace(c, vars_file='vars.yml'):
    """Set terraform workspace."""
    print('setting workspace')

    with open(vars_file) as f:
        variables = yaml.load(f)

    workspace = variables['stellar']['network_name']
    c.run(f'./terraform workspace new {workspace}')


@task(init)
def workspace(c, vars_file='vars.yml'):
    """Set terraform workspace."""
    print('setting workspace')

    with open(vars_file) as f:
        variables = yaml.load(f)

    workspace = variables['stellar']['network_name']
    c.run(f'./terraform workspace select {workspace}')


@task(workspace)
def modules(c):
    """Call terraform get."""
    print('getting modules')
    c.run('./terraform get')


@task(modules)
def plan(c, destroy=False):
    """Call terraform plan."""
    print('planning')
    c.run('./terraform plan {}'.format('-destroy' if destroy else ''))


@task(modules)
def apply(c, yes=False):
    """Call terraform destroy."""
    print('applying')
    c.run('./terraform apply {}'.format('-auto-approve' if yes else ''))


@task(modules)
def destroy(c, yes=False):
    """Call terraform destroy."""
    print('destroying')
    c.run('./terraform destroy {}'.format('-auto-approve' if yes else ''))


@task(modules)
def output(c):
    """Call terraform output."""
    print('printing output')
    c.run('./terraform output')
