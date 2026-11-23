# Terraform — aiai 饼家 infrastructure

The same three `az` commands you ran by hand, expressed as code.

| az CLI | Terraform resource |
|---|---|
| `az group create` | `azurerm_resource_group.rg` |
| *(auto-created by the CLI)* | `azurerm_log_analytics_workspace.law` |
| `az containerapp env create` | `azurerm_container_app_environment.env` |
| `az containerapp create` | `azurerm_container_app.app` |

Note the second row: the CLI silently created a Log Analytics workspace with a
random name. Terraform forces you to declare it. That's the whole value of IaC —
nothing exists that isn't written down.

## Install Terraform

```bash
winget install HashiCorp.Terraform
```

Restart your shell, then `terraform version`.

## Choose: adopt or rebuild

You already have these resources running. Two ways forward.

### Option A — Adopt (keeps your live URL) ✅ recommended

`imports.tf` maps your existing resources into Terraform state. Your site stays
up and the address doesn't change.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Then **uncomment this line** in `terraform.tfvars`:

```hcl
log_analytics_name = "workspace-rgaiaicookieC0FX"
```

Without it Terraform sees a renamed workspace, plans to replace it, and that
cascades into replacing the environment — **which changes your public URL.**

```bash
terraform init
terraform plan      # READ THIS CAREFULLY
terraform apply
```

In the plan you want to see **4 to import, 0 to add, 0 to destroy**.
If you see `must be replaced` anywhere, stop and re-check the variable above.

### Option B — Rebuild from scratch

Learn the full create cycle, at the cost of a new URL.

```bash
az group delete --name rg-aiai-cookie --yes   # ~15 min
rm imports.tf
terraform init && terraform apply
```

Your address changes, because the random subdomain
(`purplewater-3872fd76`) belongs to the environment.

## Everyday use

```bash
terraform plan     # what would change — always run first
terraform apply    # make it so
terraform output   # your URL
terraform destroy  # remove everything
```

Deploy a new image build:

```bash
terraform apply -var="image=ghcr.io/kerncl/aiai-cookie:<commit-sha>"
```

Kill cold starts (costs ~RM 23/month):

```bash
terraform apply -var="min_replicas=1"
```

## Cost

Identical to the hand-built version: **RM 0**. Terraform creates no extra Azure
resources — state is a local file.

The guardrails are in `variables.tf` as validation rules: `max_replicas` is
capped at 5 so a stray edit can't quietly authorise a large bill.

## State

State lives in `terraform.tfstate` locally. Good enough for one person, and free.

It is **gitignored** — state can contain secrets, and a shared repo is the wrong
place for it. If you ever work from two machines or add collaborators, move it to
Azure Storage with a `backend "azurerm"` block. That adds a storage account
(a few sen per month).

`.terraform.lock.hcl` **is** committed on purpose — it pins provider versions so
everyone gets identical builds.

## Not covered here

Your budget `watch_my_money` sits at **billing-account scope**, which the
`azurerm` provider doesn't manage. It stays as you created it in the portal.
Terraform can manage subscription- and resource-group-scoped budgets
(`azurerm_consumption_budget_subscription`) if you ever want that in code.
