# Orchestration

This directory is responsible for orchestrating installation of Core and Horizon apps when deploying a new network.

At Kin we are using Ansible for orchestration.

## Deploy

See [playbooks/example.yml](playbooks/example.yml) for an example playbook of deploying
Core and Horizon on a newly launched infrastructure done by our infrastructure automation at [../terraform/](../terraform).

Currently the playbooks rely on manually written inventory file (see [inventory/example.yml](inventory/example.yml)
and group_vars files (see [playbooks/group_vars](playbooks/group_vars/example) directory) that depend on information
outputted by terraform.

Once these are written, you can deploy.

NOTE you have to setup AWS credentials using environment variables or by assuming IAM roles.

```
ansible-playbook playbooks/example.yml
```
