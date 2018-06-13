import os
import os.path

from invoke import task
import jinja2
import yaml


TERRAFORM_VERSION = '0.11.7'


@task
def install(c, version=TERRAFORM_VERSION):
    file = f'terraform_{version}_linux_amd64.zip'

    if os.path.exists('terraform'):
        print('Terraform file found')
        return

    print(f'Downloading Terraform {version}')
    c.run(f'wget -q https://releases.hashicorp.com/terraform/{version}/{file}')
    c.run(f'unzip {file}')
    c.run(f'rm {file}')


@task
def template(c,
             template_file='stellar-network.tf.j2',
             vars_file='vars.yml',
             out_file='stellar-network.tf'):

    print('generating terraform file from template')

    with open(vars_file) as f:
        vars = yaml.load(f)

    with open(template_file) as f:
        t = jinja2.Template(f.read())

    out = t.render(vars, env_vars=os.environ)

    with open(out_file, 'w') as f:
        f.write(out)

    c.run(f'./terraform fmt {out_file}')


@task(template)
def init(c):
    print('initializing')
    c.run('./terraform init')


@task(init)
def modules(c):
    print('getting modules')
    c.run('./terraform get')


@task(modules, template)
def plan(c):
    print('planning')
    c.run('./terraform plan')


@task(modules, template)
def apply(c):
    print('applying')
    c.run('./terraform apply')


@task(modules, template)
def destroy(c):
    print('destroying')
    c.run('./terraform destroy')
