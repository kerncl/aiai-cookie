# Deployment checklist — aiai 饼家

Live status of getting this site onto Azure at **RM 0/month**.

**Target architecture:** Azure Container Apps (scale-to-zero) + GHCR (free public image)
**Region:** `southeastasia` (Singapore — nearest to Malaysia)
**Last updated:** 2026-11-18

---

## Status at a glance

| Phase | Status |
|---|---|
| 1. Build the app | ✅ Done |
| 2. Containerize | ✅ Done |
| 3. Azure account prep | ✅ Done |
| 4. Source control | 🔴 **Blocked — needs you** |
| 5. Push image to GHCR | ⬜ Not started |
| 6. Create Azure resources | ⬜ Not started |
| 7. Verify + automate | ⬜ Not started |
| 8. Optional extras | ⬜ Not started |

**Current spend: RM 0/month.** No billable Azure resources exist.

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
- [x] `.dockerignore` keeps `images_raw/` and `.venv/` out
- [x] Image built and **smoke-tested running in the container**

## Phase 3 — Azure account prep ✅

- [x] Azure CLI authenticated — `lkchindeveloper@gmail.com`
- [x] Subscription identified — Pay-As-You-Go, **spending limit OFF** ⚠️
- [x] Budget `aiai-cookie-budget` created — USD 12/mo cap, alerts at 1% / 50% / forecast 100%
- [x] `Microsoft.App` resource provider registered *(the usual first-deploy blocker)*
- [x] Deleted leftover `rg-aks-training` — **saved ~RM 20/month**
- [x] Architecture + cost model decided

## Phase 4 — Source control 🔴 BLOCKED

> **This is the only step that needs you.** It opens a browser, so it can't be automated.

- [ ] **Log in to personal github.com**
      ```bash
      gh auth login --hostname github.com --web --scopes "repo,workflow,write:packages"
      ```
      `write:packages` is required for GHCR. Your `github.amd.com` login is unaffected —
      `gh` holds both accounts.
- [ ] First commit (18 files; branch already renamed `master` → `main`)
- [ ] Create the GitHub repo — **must be public** so GHCR packages can be public
- [ ] Push

## Phase 5 — Push the image to GHCR ⬜

- [ ] Tag for GHCR — **lowercase only**, `ghcr.io` rejects capitals
      ```bash
      docker tag aiai-cookie:local ghcr.io/<username>/aiai-cookie:latest
      ```
- [ ] Authenticate Docker to GHCR
- [ ] Push the image
- [ ] **Flip the package to public** ⚠️
      Packages default to **private**. If you skip this, Azure fails to pull with an
      auth error that never mentions visibility. GitHub → your profile → Packages →
      `aiai-cookie` → Package settings → Change visibility → Public.
- [ ] Verify an anonymous pull works:
      ```bash
      docker logout ghcr.io && docker pull ghcr.io/<username>/aiai-cookie:latest
      ```

## Phase 6 — Create Azure resources ⬜

- [ ] Resource group *(free — just a folder)*
      ```bash
      az group create --name rg-aiai-cookie --location southeastasia
      ```
- [ ] Container Apps environment *(free on Consumption)*
      ```bash
      az containerapp env create \
        --name aiai-env --resource-group rg-aiai-cookie \
        --location southeastasia
      ```
      Do **not** pass `--enable-workload-profiles` — a Dedicated profile adds a
      $0.10/hour management fee (~RM 295/month).
- [ ] Container app, scale-to-zero
      ```bash
      az containerapp create \
        --name aiai-cookie --resource-group rg-aiai-cookie \
        --environment aiai-env \
        --image ghcr.io/<username>/aiai-cookie:latest \
        --target-port 8000 --ingress external \
        --min-replicas 0 --max-replicas 2 \
        --cpu 0.25 --memory 0.5Gi
      ```
      `--min-replicas 0` is what makes this RM 0. `--target-port 8000` must match
      the `EXPOSE` in the Dockerfile.

## Phase 7 — Verify and automate ⬜

- [ ] Get the live URL
      ```bash
      az containerapp show --name aiai-cookie --resource-group rg-aiai-cookie \
        --query properties.configuration.ingress.fqdn -o tsv
      ```
- [ ] Open it and confirm the catalogue renders (first hit = 15–30 s cold start)
- [ ] Run `scripts/smoke.py` against the live URL
- [ ] Confirm it scales to zero when idle
- [ ] Add `AZURE_CREDENTIALS` secret in GitHub so CI can deploy
- [ ] Confirm a push to `main` builds, tests and deploys automatically

## Phase 8 — Optional extras ⬜

- [ ] Custom domain (`aiaicookies.com`) — free on Container Apps, you pay the registrar ~RM 60/yr
- [ ] Managed TLS certificate — free, auto-renewing
- [ ] Replace placeholder cookies with real products
- [ ] Add real photos to `images_raw/`, run `scripts/optimize_images.py`
- [ ] Wire 纯素 (vegan) into the dietary filter
- [ ] Application Insights for deeper monitoring

---

## Cost tracker

| Resource | Status | Monthly |
|---|---|---|
| Resource group | not created | RM 0 |
| Container Apps environment | not created | RM 0 |
| Container app | not created | RM 0 *(within free grant)* |
| Log Analytics | not created | ~RM 0.01 |
| Bandwidth | — | RM 0 *(100 GB free)* |
| GHCR | not pushed | RM 0 *(public)* |
| Budget alert | ✅ active | RM 0 |
| ~~ACR from AKS training~~ | ✅ **deleted** | ~~RM 20~~ → RM 0 |
| | **Projected total** | **≈ RM 0** |

Free grant per month: **180,000 vCPU-sec · 360,000 GiB-sec · 2M requests**.
At 0.25 vCPU that's ~200 hours of runtime — the binding limit is uptime, not traffic.

---

## Emergency stop

Deletes everything and stops all charges:

```bash
az group delete --name rg-aiai-cookie --yes
```

Check current spend any time:

```bash
az consumption usage list --start-date 2026-11-01 --end-date 2026-11-30 \
  --query "[].{name:instanceName, cost:pretaxCost}" -o table
```

⚠️ Your subscription has **no spending limit**. Budget alerts notify, they do **not** cap.
The `az group delete` above is the real off switch.

---

## Gotchas already hit or avoided

| Gotcha | Status |
|---|---|
| `Microsoft.App` not registered → deploy fails | ✅ Fixed in advance |
| Leftover ACR billing RM 20/mo for a deleted cluster | ✅ Found and deleted |
| Budget forecast alarming on *historical* spend | ✅ Diagnosed — not a real overage |
| GHCR packages default to private → Azure can't pull | ⬜ Watch for this in Phase 5 |
| `ghcr.io` rejects uppercase image paths | ⬜ Handled in CI via `${GITHUB_REPOSITORY,,}` |
| Deleting the registry breaks scale-to-zero apps later | ℹ️ Why GHCR beats ACR here |
| Stopping an App Service doesn't stop its bill | ℹ️ Why we avoided App Service |
