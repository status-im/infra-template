# Description

### :warning: Replace with actual description!

>This repo defines a standard template for new Status infrastructure repositories.
>
>Key things to change:
>
>- Update `README.md`
>- Terraform
>    - Change `path` in `main.tf` to match new fleet
>    - Add necessary providers in `providers.tf`
>    - Add necessary secrets in `secrets.tf`
>    - Adjust or remove `workspaces.tf`
>    - Adjust `versions.tf`
>- Ansible
>    - Extend `ansible/group_vars/all.yml`
>    - Or add a dedicated `group_vars` file
>    - Create the `ansible/main.yml` playbook
>- Github
>    - Add to `infra-repos/variables.tf`

# Repo Usage

For how to use this repo read the [Infra Repo Usage](https://github.com/status-im/infra-docs/blob/master/docs/general/infra_repo_usage.md) doc.

# Test 

## Prerequisites

To run the test environement, you need to have installed 

* [vagrant](https://www.vagrantup.com/)
* [VirtualBox](https://www.virtualbox.org/)

> **Note**: It's opssible to use another virtualization hypervisor, in that case, you need to modify the Vagrantfile accordingly.

## Launch

The command ``make test`` will launch the following actions:

* `init-test-env` : Create the VM, add the user ssh public key into the `admin.pub` file of `infra-role-bootstrap-linux`, run the linux bootstraping of the VM (tags for `packages`, `role`, `docker`, `firewall`, `user`, `logging`)
* `test-run-upgrade`: Example of plabook to run
* `clean-text-env`: Delete the VM, and remove the `.vagrant` directory.

## Adapt to project

* Modify the `ansible/inventory/test` to add host group matching the playbook you want to run.
* Add function in the Makefile for each playbook you want to run.

> **Warning**: The test VM doesn't not install consul on the host, some part of the playbook might failed. Use tags to specify witch role to execute.
