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

# Repo Usage

For how to use this repo read the [Infra Repo Usage](https://github.com/status-im/infra-docs/blob/master/docs/general/infra_repo_usage.md) doc.
