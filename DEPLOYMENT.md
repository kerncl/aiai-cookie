# Deployment checklist — aiai 饼家

Live status of getting this site onto Azure at **RM 0/month**.

**Target architecture:** Azure Container Apps (scale-to-zero) + GHCR (free public image)
**Region:** `southeastasia` (Singapore — nearest to Malaysia)
**Repo:** https://github.com/kerncl/aiai-cookie (public)
**Image:** `ghcr.io/kerncl/aiai-cookie:latest` (public)
**Last updated:** 2026-11-19

## 🍪 LIVE

**https://aiai-cookie.purplewater-3872fd76.southeastasia.azurecontainerapps.io**

Deployed by hand on 2026-11-19. Free HTTPS, Singapore region, **RM 0/month**.

---

## Status at a glance

| Phase | Status |
|---|---|
| 1. Build the app | ✅ Done |
| 2. Containerize | ✅ Done |
| 3. Azure account prep | ✅ Done |
| 4. Source control | ✅ Done |
| 5. Push image to GHCR | ✅ Done (CI did it automatically) |
| 6. Create Azure resources | ✅ **Done — deployed by hand** |
| 7. Verify + automate | 🔵 **You are here** — site verified, CI deploy still broken |
| 8. Optional extras | ⬜ Not started |
| 9. Infrastructure as Code (Terraform) | 📘 **Config ready — you run it manually** |

**Current Azure spend: RM 0** — inside the free monthly grant.

---

## Phase 1 — Build the app ✅

- [x] Flask app with bilingual (简体中文 + English) catalogue
- [x] 7 Chinese biscuits with ingredients, allergens, nutrition
- [x] Allergen filter (exclusive) + dietary filter (inclusive)
- [x] Search across both languages, matching ingredients not just names
- [x] Prices in Malaysian Ringgit, sold by the box
- [x] 无猪油 pork-free marker + filter
- [x] `scripts/smoke.py` — 23 HTTP checks, all passing

## Phase 2 — Containerize ✅

- [x] `Dockerfile` — two-stage, `python:3.12-slim`, 153 MB
- [x] Runs as non-root (`appuser`, uid 10001)
- [x] `HEALTHCHECK` wired to the app's `/healthz`
- [x] gunicorn as PID 1 for clean shutdown
- [x] `docker-compose.yml` with live-edit volume mounts
- [x] Image built and smoke-tested **running in the container**

## Phase 3 — Azure account prep ✅

- [x] Azure CLI authenticated — `lkchindeveloper@gmail.com`
- [x] Subscription identified — Pay-As-You-Go, **spending limit OFF** ⚠️
- [x] Deleted leftover `rg-aks-training` — **saved ~RM 20/month**
- [x] Architecture + cost model decided
- [x] `Microsoft.App` registered — `containerApps` + `managedEnvironments` available
- [x] Budget `watch_my_money` — USD 5/month at **billing-account scope**
      (broader than subscription scope: covers any future subscription too)
      Alerts: 1% actual + 100% forecast → `lkchindeveloper@gmail.com`
      ⚠️ Alerts notify, they never cap. `az group delete` is the real off switch.

## Phase 4 — Source control ✅

- [x] Personal github.com access via SSH host alias `github-personal.com`
      *(cleaner than `gh auth login` — avoids clashing with the github.amd.com account)*
- [x] Commit `f4e5970` "init" — 19 files
- [x] Repo created at `kerncl/aiai-cookie` and set **public**
- [x] Pushed; local `main` matches `origin/main`
- [x] Verified public: anonymous fetch of the repo page returns 200

## Phase 5 — Push the image to GHCR ✅

Done automatically — pushing to `main` triggered `.github/workflows/azure-deploy.yml`.

- [x] CI validated `cookies.json` / `ui.json` (unique slugs, known allergen + dietary keys)
- [x] CI built the image
- [x] CI ran `scripts/smoke.py` against the **running container**
- [x] CI pushed two tags: `latest` and `f4e5970b3bc3...` (the commit SHA)
- [x] Package is **public** — GitHub inherited visibility from the public repo,
      so the usual "packages default to private" trap did not apply
- [x] Verified anonymously: `linux/amd64`, pullable with no credentials

Confirm any time without Docker:
```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:kerncl/aiai-cookie:pull&service=ghcr.io" \
  | python -c "import json,sys; print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $TOKEN" https://ghcr.io/v2/kerncl/aiai-cookie/tags/list
```

## Phase 6 — Create Azure resources ✅

Deployed by hand on 2026-11-19. Three commands.

- [x] Resource group *(free, instant)*
      ```bash
      az group create --name rg-aiai-cookie --location southeastasia
      ```
- [x] Container Apps environment *(free on Consumption, took ~5 min)*
      ```bash
      az containerapp env create --name aiai-env --resource-group rg-aiai-cookie --location southeastasia
      ```
      - Did **not** pass `--enable-workload-profiles` — a Dedicated profile would add
        $0.10/hour (~RM 295/month) before the app uses anything.
      - Auto-created Log Analytics workspace `workspace-rgaiaicookieC0FX`.
      - ⚠️ Deleting this takes **~15 minutes**.
- [x] Container app, scale-to-zero
      ```bash
      az containerapp create --name aiai-cookie --resource-group rg-aiai-cookie \
        --environment aiai-env --image ghcr.io/kerncl/aiai-cookie:latest \
        --target-port 8000 --ingress external \
        --min-replicas 0 --max-replicas 2 --cpu 0.25 --memory 0.5Gi
      ```
      | Flag | Why it matters |
      |---|---|
      | `--min-replicas 0` | **This is what makes it RM 0.** Set to 1 and you pay ~RM 23/mo |
      | `--target-port 8000` | Must match `EXPOSE` in the Dockerfile |
      | `--ingress external` | Without it the app has no public URL |
      | `--cpu 0.25 --memory 0.5Gi` | Smallest size; must be a valid CPU/memory pair |

### ⚠️ `ConnectionResetError` during env create — and why you ignore it

`az containerapp env create` died with a long traceback ending in
`WinError 10054 — An existing connection was forcibly closed by the remote host`,
failing inside `poll_status`.

**The environment was created successfully anyway.** These commands are
*asynchronous*: the CLI sends one request, Azure accepts it, then the CLI polls for
completion. A corporate proxy or VPN dropping the long-lived SSL connection kills
the polling, not the operation.

**Always check state before re-running** — a blind retry risks duplicates or an
"already exists" error that sends you debugging the wrong problem:

```bash
az containerapp env list --resource-group rg-aiai-cookie -o table
az containerapp show --name aiai-cookie --resource-group rg-aiai-cookie --query properties.provisioningState -o tsv
```

## Phase 7 — Verify and automate 🔵 YOU ARE HERE

- [x] Got the live URL
      ```bash
      az containerapp show --name aiai-cookie --resource-group rg-aiai-cookie \
        --query properties.configuration.ingress.fqdn -o tsv
      ```
- [x] Site serves over HTTPS — `200`, 0.76 s warm / 0.22 s on repeat
- [x] `/healthz` returns `{"cookies":7,"status":"ok"}`
- [x] All 7 cookies render bilingually with RM prices and 每盒 units
- [x] 无猪油 tags on all 7, 售罄 badge present, `lang="zh-CN"` correct
- [x] Allergen filter verified live — hiding 花生 + 麸质 leaves 杏仁饼 and 绿豆糕
- [x] **Scale-to-zero CONFIRMED** ✅ — after a long idle period, a request took
      **40.7 seconds**. That is a genuine cold start: the app had scaled to zero
      replicas and Azure had to pull the image and boot gunicorn from nothing.
      Cold start is the *proof* you're paying nothing — no replicas, no billing.
      (The 0.76 s measured right after deploy was a still-warm container.)
      Check replica count any time:
      ```bash
      az containerapp replica list --name aiai-cookie --resource-group rg-aiai-cookie -o table
      ```
      Empty list = zero replicas = RM 0.
- [ ] **Fix the CI deploy job** ⚠️ — see below
- [ ] Confirm a push to `main` deploys automatically

### Wiring CI to deploy — OIDC, no stored secret

The workflow has been rewritten for Container Apps. Four bugs were fixed:

| Was wrong | Now |
|---|---|
| `azure/webapps-deploy` — targets **App Service** | `az containerapp update` |
| Needed `AZURE_WEBAPP_PUBLISH_PROFILE` (App Service concept) | OIDC federated identity |
| Stale `AZURE_WEBAPP_NAME` variable | `AZURE_CONTAINER_APP` |
| `resourceGroup: aiai-cookie-rg` — **words reversed** | `rg-aiai-cookie` |

It also now skips rebuilds for `**.md` and `terraform/**` changes.

**How OIDC works:** GitHub presents a short-lived token asserting *"I am
`kerncl/aiai-cookie`, branch `main`."* Azure checks that claim against a federated
credential you register, then issues an access token valid for minutes.
**No password is ever created or stored.** Nothing to leak or rotate.

#### Step 1 — Create the identity (run these)

```bash
SUB=60f1fa6b-f10c-486b-a720-3ee4d299959f
TENANT=30ab3971-2c14-43f2-9fff-fa8914b54591
REPO=kerncl/aiai-cookie
RG=rg-aiai-cookie

# a) App registration — the identity CI will use
APP_ID=$(az ad app create --display-name "github-aiai-cookie" --query appId -o tsv)
echo "APP_ID=$APP_ID"        # save this

# b) Service principal for that app
az ad sp create --id "$APP_ID"

# c) Federated credential — trusts ONLY this repo, ONLY the main branch
az ad app federated-credential create --id "$APP_ID" --parameters "{
  \"name\": \"github-main\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${REPO}:ref:refs/heads/main\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}"

# d) Permission — Contributor on the RESOURCE GROUP only, not the subscription
az role assignment create \
  --assignee "$APP_ID" \
  --role Contributor \
  --scope "/subscriptions/${SUB}/resourceGroups/${RG}"
```

The `subject` in (c) is the security boundary. A PR branch, a fork, or another
repo produces a different subject and is refused. Least privilege in (d) means a
compromised pipeline can only touch `rg-aiai-cookie`.

#### Step 2 — Add three GitHub secrets

⚠️ Your `gh` CLI is authenticated to **github.amd.com**, not github.com, so
`gh secret set` would target the wrong host. Use the web UI:

**github.com/kerncl/aiai-cookie → Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `AZURE_CLIENT_ID` | the `APP_ID` from step (a) |
| `AZURE_TENANT_ID` | `30ab3971-2c14-43f2-9fff-fa8914b54591` |
| `AZURE_SUBSCRIPTION_ID` | `60f1fa6b-f10c-486b-a720-3ee4d299959f` |

None of these are secret in the password sense — they're identifiers. The
security comes from the federated credential, not from hiding them.

#### Step 3 — Test it

```bash
git add .github/workflows/azure-deploy.yml
git commit -m "CI: deploy to Container Apps via OIDC"
git push
```

Watch the Actions tab. Both jobs should go green, and the deploy job prints your
live URL.

Then try the real loop: change a price in `data/cookies.json`, push, and watch it
reach the live site in ~3 minutes with no manual steps.

#### If it fails

| Error | Cause |
|---|---|
| `Unable to get ACTIONS_ID_TOKEN_REQUEST_URL` | Missing `permissions: id-token: write` — the #1 OIDC mistake |
| `AADSTS70021: No matching federated identity record` | `subject` doesn't match. Pushing from a branch other than `main`? |
| `AuthorizationFailed` | Role assignment missing or wrong scope; can take a minute to propagate |
| `ResourceGroupNotFound` | Check `rg-aiai-cookie`, not `aiai-cookie-rg` |

## Phase 8 — Optional extras ⬜

- [ ] Custom domain (`aiaicookies.com`) — free on Container Apps, ~RM 60/yr to your registrar
- [ ] Managed TLS certificate — free, auto-renewing
- [ ] Replace the placeholder cookies with real products
- [ ] Add real photos to `images_raw/`, run `scripts/optimize_images.py`
- [ ] Wire 纯素 (vegan) into the dietary filter
- [ ] Application Insights for deeper monitoring

---

## Phase 9 — Infrastructure as Code with Terraform 📘

**Config is written and validated. You run every command yourself.**

The `terraform/` folder expresses the exact same infrastructure you built by hand:

| az CLI you ran | Terraform resource |
|---|---|
| `az group create` | `azurerm_resource_group.rg` |
| *(auto-created silently by the CLI)* | `azurerm_log_analytics_workspace.law` |
| `az containerapp env create` | `azurerm_container_app_environment.env` |
| `az containerapp create` | `azurerm_container_app.app` |

Already done for you:
- [x] Terraform **1.17.1** installed via `winget install HashiCorp.Terraform`
- [x] `main.tf`, `variables.tf`, `outputs.tf`, `imports.tf` written
- [x] `terraform validate` → **Success! The configuration is valid**
- [x] azurerm provider v4.81.0 confirmed to resolve

### Your steps

- [ ] **1. Restart your shell** so `terraform` is on PATH
      ```bash
      terraform version      # expect v1.17.1
      ```

- [ ] **2. Create your tfvars**
      ```bash
      cd terraform
      cp terraform.tfvars.example terraform.tfvars
      ```
      Set these two lines:
      ```hcl
      subscription_id    = "60f1fa6b-f10c-486b-a720-3ee4d299959f"
      log_analytics_name = "workspace-rgaiaicookieC0FX"
      ```
      ⚠️ That second line is **critical**. The CLI auto-generated that workspace
      name. If Terraform sees a different name it plans to replace the workspace,
      which cascades into replacing the environment — **and your public URL
      changes**, because `purplewater-3872fd76` belongs to the environment.

- [ ] **3. Initialise** — downloads the azurerm provider (~1 min)
      ```bash
      terraform init
      ```

- [ ] **4. Validate**
      ```bash
      terraform validate      # expect: Success! The configuration is valid.
      ```

- [ ] **5. Plan — read this output carefully**
      ```bash
      terraform plan
      ```
      `plan` is **read-only**; it changes nothing in Azure.

      ⏱️ It can take **several minutes** — it queries every resource and imports
      are slow. Be patient; don't kill it. (My attempt was killed at 10 min,
      which left a stale `.terraform.tfstate.lock.info`. If you ever see
      *"Error acquiring the state lock"*, delete that file.)

      **What you want to see:**
      ```
      Plan: 0 to add, 0 to change, 0 to destroy.
      4 to import.
      ```
      **Stop immediately if you see** `must be replaced` on
      `azurerm_container_app_environment` — your URL would change. Re-check step 2.

- [ ] **6. Apply**
      ```bash
      terraform apply
      ```
      Type `yes` at the prompt. This adopts the four existing resources into
      Terraform state. Your site stays up throughout — nothing is recreated.

- [ ] **7. Confirm**
      ```bash
      terraform output        # should print your live URL
      terraform plan          # should now say "No changes"
      ```
      That second command is the real win: re-running is always safe and tells
      you reality still matches the config.

### Try these once it works

```bash
terraform plan -var="min_replicas=1"                         # preview killing cold starts (~RM 23/mo)
terraform plan -var="image=ghcr.io/kerncl/aiai-cookie:<sha>" # preview deploying a specific build
```

Run `plan` without `apply` to see the diff and change nothing — the habit the
az CLI can't give you.

---

## Learning track — Terraform concepts, in the order you'll meet them

Each exercise teaches **one idea** using your own cookie site. Do them in order;
each builds on the last. Nothing here costs money.

### 1. Providers and the lock file
```bash
terraform init
```
- [ ] Look at `.terraform/` — the azurerm **provider** was downloaded here. A provider
      is the plugin that knows how to talk to one API (Azure, AWS, GitHub…).
- [ ] Open `.terraform.lock.hcl`. It pins v4.81.0 so your colleague gets the same
      version. **Commit this file.**
- [ ] Find `required_providers` in `main.tf`. `~> 4.0` means "any 4.x, not 5.0" —
      version 5 could contain breaking changes.

**Concept:** Terraform itself knows nothing about Azure. Providers do.

### 2. HCL syntax and validation
```bash
terraform validate
terraform fmt -check      # is formatting canonical?
terraform fmt             # fix it
```
- [ ] Break something on purpose — change `cpu = 0.25` to `cpu = "lots"`, run
      `validate`, read the error, change it back.

**Concept:** `validate` checks syntax and types **offline** — it never contacts Azure.

### 3. Variables and validation rules
- [ ] Read `variables.tf`. Every value is a variable, so nothing is hardcoded.
- [ ] Try `terraform plan -var="max_replicas=50"` and watch the custom validation
      rule reject it before Azure is ever contacted.

**Concept:** guardrails live in code. The az CLI would have happily accepted 50.

### 4. Plan — the diff
```bash
terraform plan
```
- [ ] Read the symbols: `+` create, `~` change in place, `-` destroy,
      `-/+` **destroy and recreate**.
- [ ] `-/+` is the dangerous one. For `azurerm_container_app_environment` it means
      your URL changes.

**Concept:** you see the consequence *before* it happens. This has no az equivalent.

### 5. State — Terraform's memory
```bash
terraform apply
terraform state list          # what Terraform believes it manages
terraform show                # full detail
```
- [ ] Open `terraform.tfstate` in an editor. It's JSON recording every resource.
- [ ] **This is why re-running is safe.** The az CLI has no memory, which is why
      re-running `az containerapp create` says "already exists".

**Concept:** state maps your config to real Azure resource IDs.

### 6. Idempotency
```bash
terraform apply       # again, immediately
```
- [ ] Expect **"No changes. Your infrastructure matches the configuration."**
- [ ] Recall your `ConnectionResetError`: with Terraform you'd just re-run. It would
      reconcile to the correct state instead of erroring.

**Concept:** describing a destination, not steps, means repeating is harmless.

### 7. Drift detection
- [ ] In the **portal**, change the container app's max replicas from 2 to 3.
- [ ] Run `terraform plan`. It spots the drift and offers to put it back.

**Concept:** config is the source of truth. Manual changes get reverted.

### 8. Making a real change
- [ ] Edit `min_replicas` to `1` in `terraform.tfvars`
- [ ] `terraform plan` — confirm it says `1 to change, 0 to destroy`
- [ ] `terraform apply`, then load the site: no cold start
- [ ] Set it back to `0` and apply. ⚠️ Leaving it at 1 costs ~RM 23/month.

**Concept:** the normal workflow is edit → plan → apply.

### 9. Outputs
```bash
terraform output
terraform output -raw fqdn
```
- [ ] Read `outputs.tf`. `-raw` is what you'd pipe into a script.

**Concept:** outputs expose computed values — the FQDN doesn't exist until Azure assigns it.

### 10. Dependencies
- [ ] In `main.tf`, note `azurerm_container_app_environment.env.id` inside the app.
- [ ] That reference **is** the dependency — Terraform builds the graph itself and
      creates things in the right order. You never write "do this first".

**Concept:** implicit dependency graph from references.

### 11. Destroy and rebuild
> ⚠️ This changes your public URL. Do it when you're ready, or on a throwaway RG.
```bash
terraform destroy      # type yes
terraform apply        # rebuild from nothing
```
- [ ] Time it. Rebuilding the whole stack from one command is the real payoff.

**Concept:** infrastructure becomes disposable and reproducible.

### 12. What to learn next
- [ ] **Remote state** — `backend "azurerm"`, so two machines can share state
- [ ] **Modules** — package these four resources for reuse
- [ ] **Workspaces** — one config, separate dev/prod state
- [ ] **`for_each`** — deploy several cookie sites from one block
- [ ] **CI/CD** — run `plan` on every PR, `apply` on merge

### Glossary

| Term | Meaning |
|---|---|
| **provider** | Plugin for one API (azurerm) |
| **resource** | One real thing (`azurerm_container_app`) |
| **state** | Terraform's record of what it created |
| **plan** | Preview diff, read-only |
| **apply** | Execute the plan |
| **drift** | Reality diverging from config |
| **import** | Adopt an existing resource into state |
| **HCL** | HashiCorp Configuration Language |
| **idempotent** | Running twice equals running once |

### Notes

- **State** lives in local `terraform.tfstate`, gitignored. Free, fine for one
  person. For multiple machines, move it to Azure Storage with a `backend "azurerm"` block.
- **`.terraform.lock.hcl` should be committed** — it pins provider versions.
  It's deliberately *not* in `.gitignore`.
- **Cost: still RM 0.** Terraform creates no Azure resources of its own.
- Your budget `watch_my_money` is at billing-account scope, which the azurerm
  provider can't manage. It stays as you made it in the portal.

See `terraform/README.md` for the rebuild-from-scratch alternative.

---

## Cost tracker

| Resource | Status | Monthly |
|---|---|---|
| `rg-aiai-cookie` | ✅ created | RM 0 |
| `aiai-env` (Container Apps env) | ✅ created | RM 0 |
| `aiai-cookie` (container app) | ✅ **running, min-replicas 0** | RM 0 *(within free grant)* |
| `workspace-rgaiaicookieC0FX` | ✅ created | ~RM 0.01 |
| Bandwidth | in use | RM 0 *(100 GB free)* |
| GHCR package | ✅ public | RM 0 |
| Budget `watch_my_money` | ✅ active | RM 0 |
| ~~ACR from AKS training~~ | ✅ deleted | ~~RM 20~~ → RM 0 |
| | **Actual total** | **≈ RM 0** |

Free grant per month: **180,000 vCPU-sec · 360,000 GiB-sec · 2M requests**.
At 0.25 vCPU that's ~200 hours of runtime — the binding limit is uptime, not traffic.

---

## Emergency stop

Deletes everything and stops all charges:

```bash
az group delete --name rg-aiai-cookie --yes
```

Check current spend:

```bash
az rest --method post \
  --url "https://management.azure.com/subscriptions/<SUB_ID>/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{"type":"ActualCost","timeframe":"MonthToDate","dataset":{"granularity":"None","aggregation":{"totalCost":{"name":"Cost","function":"Sum"}}}}'
```
*(This API rate-limits aggressively — wait a minute between calls.)*

⚠️ Your subscription has **no spending limit**. Budget alerts notify, they do **not** cap.

---

## Gotchas — hit, avoided, or still ahead

| Gotcha | Status |
|---|---|
| `Microsoft.App` not registered → deploy fails | ✅ Registered |
| `ConnectionResetError` mid-command — operation succeeded anyway | ✅ Hit it; **check state, don't blind-retry** |
| Leftover ACR billing RM 20/mo for a deleted cluster | ✅ Found and deleted |
| Budget "forecast exceeded" alarm on *historical* spend | ✅ Diagnosed — naive linear forecast, not a real overage |
| GHCR packages default to private | ✅ Didn't apply — public repo made the package public |
| `ghcr.io` rejects uppercase image paths | ✅ Handled in CI via `${GITHUB_REPOSITORY,,}` |
| CI deploy job targets App Service, not Container Apps | ⚠️ **Still broken — Phase 7** |
| Container Apps env takes ~5 min to create, ~15 to delete | ℹ️ Measured |
| Deleting a registry breaks scale-to-zero apps later | ℹ️ Why GHCR beats ACR here |
| Stopping an App Service doesn't stop its bill | ℹ️ Why we avoided App Service |
| Updating a cookie needs a rebuild — data is baked into the image | ℹ️ Fix the CI job and `git push` handles it |
