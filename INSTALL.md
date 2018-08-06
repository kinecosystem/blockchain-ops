# Launch a Network

The following are instructions on setting up a group of Core validators in order to setup a new or join an existing network.

Kin Foundation are currently using AWS for managing its infrastructure, though other cloud providers are good as well.

## Network Topology

Before launching a group of nodes, it is important to decide on the following:

1. How many nodes to run, keeping in mind high-availabiltiy considerations:
    1. We recommend the network size include at least a total 7 nodes, to allow for more than one node to fail.
    1. Nodes should be deployed on different cloud regions e.g. AWS us-east-1 and us-west-1. Prefer a separate region for each node.
1. Decide on your [quorum set and safety threshold percentage](https://www.stellar.org/developers/stellar-core/software/admin.html#crafting-a-quorum-set).

## Core

1. [Configure Core](https://www.stellar.org/developers/stellar-core/software/admin.html).
    - See Stellar's [configuration example](https://github.com/stellar/stellar-core/blob/master/docs/stellar-core_example.cfg).
    - See [our example](deploy/ansible/playbooks/roles/stellar-core/templates/stellar-core.cfg.j2).
1. See how to [install and run Core](https://github.com/stellar/stellar-core/blob/master/INSTALL.md).
    - Kin Foundation runs Core using Docker.
    - See [our Dockerfile](images/dockerfiles/Dockerfile.stellar-core) as an example on how to build on Ubuntu 16.04.
1. Read on [hardware requirements](https://www.stellar.org/developers/guides/hardware.html) and launch the required infrastructure:
    1. Launch a cloud instance such as AWS EC2, used for running the Core application.
    1. Launch a PostgreSQL database instance such as AWS RDS, used for storing ledger state and other operational information by the Core application.
    1. Create an AWS S3 bucket, used for storing the history archive.
1. Repeat the above process for other Core nodes in your system.
1. Finally, see Core's [Administration Guide](https://www.stellar.org/developers/stellar-core/software/admin.html).

## Horizon

1. Launch an EC2 and RDS instance, similar to the above.
1. [Configure Horizon](https://www.stellar.org/developers/horizon/reference/admin.html#configuring)
    - Similar to Core, we run Horizon using Docker.
    - See [image/Dockerfile.Horizon](image/Dockerfile.horizon) and [image/docker-compose.yml](image/docker-compose.yml)
as an example on how to build and configure Horizon on Ubuntu 16.04.
1. Finally, see Horizon's [Administration Guide](https://www.stellar.org/developers/horizon/reference/admin.html).

## Automation

At Kin we use Ansible for orchestration and Terraform for infrastructure automation.

### Ansible

Ansible playbooks and roles can serve as specific step-by-step guide to deploying Core and Horizon on production.
Specific points of interest include:

1. [Core deploy role](deploy/ansible/playbooks/roles/stellar-core).
1. Horizon [init](deploy/ansible/playbooks/roles/stellar-core),
[setup](deploy/ansible/playbooks/roles/horizon-setup),
and [start](deploy/ansible/playbooks/roles/horizon-start) roles.
1. [Kernel network parameter optimization role](deploy/ansible/playbooks/roles/optimize-network).

See [deploy/ansible/](deploy/ansible) directory for further resources.

### Terraform

Similar to Ansible, our Terraform code can serve as a step-by-step guide to properly configure the infrastructure.

See [deploy/terraform/](deploy/terraform) directory for more information.
Please keep the [security concerns guide](SECURITY.md) in mind when launching infrastructure.

## Additional Resources

Official Stellar docs are located at [stellar.org/developers](https://www.stellar.org/developers/)

### Core

1. [Administration](https://www.stellar.org/developers/stellar-core/software/admin.html)
1. [Hardware Requirements](https://www.stellar.org/developers/guides/hardware.html)
1. [Security](https://www.stellar.org/developers/guides/security.html)
1. [github.com/stellar/stellar-core](https://github.com/stellar/stellar-core)
1. [github.com/stellar/stellar-protocol](https://github.com/stellar/stellar-protocol)

### Horizon and Other Apps

1. [Administration](https://www.stellar.org/developers/horizon/reference/admin.html)
1. [github.com/stellar/horizon](https://github.com/stellar/horizon)
    1. Deprecated repo
    1. Has latest stable release v0.11.1
1. [github.com/stellar/go](https://github.com/stellar/go)
    1. New mono-repo
    1. Has v0.12.0 RC
    1. Includes various other peripheral apps and tools: Bifrost, HD wallet, and more.
1. [github.com/stellar/laboratory](https://github.com/stellar/laboratory)

### Other

1. [Stellar Node Performance Tips](https://galactictalk.org/d/279-effectively-run-your-stellar-validator-node-performance-tips)
