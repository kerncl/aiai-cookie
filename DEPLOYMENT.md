# Deployment checklist — aiai 饼家

Live status of getting this site onto Azure at **RM 0/month**.

**Target architecture:** Azure Container Apps (scale-to-zero) + GHCR (free public image)
**Region:** `southeastasia` (Singapore — nearest to Malaysia)
**Repo:** https://github.com/kerncl/aiai-cookie (public)
**Image:** `ghcr.io/kerncl/aiai-cookie:latest` (public)
**Last updated:** 2026-11-19

> **You are driving from here.** Azure was provisioned once, then deliberately torn
> down so you can build it yourself by hand. Phases 1–5 are done; Phase 3 and 6
> onward are yours.

---

## Status at a glance

| Phase | Status |
|---|---|
| 1. Build the app | ✅ Done |
| 2. Containerize | ✅ Done |
| 3. Azure account prep | ♻️ **Reverted — redo this** |
| 4. Source control | ✅ Done |
| 5. Push image to GHCR | ✅ Done (CI did it automatically) |
| 6. Create Azure resources | 🔵 **You are here** |
| 7. Verify + automate | ⬜ Not started |
| 8. Optional extras | ⬜ Not started |

**Current Azure spend: RM 0.** Subscription contains no resources of this project.

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

## Phase 3 — Azure account prep ♻️ REVERTED

Done once, then undone on request. **Redo the unchecked items before Phase 6.**

- [x] Azure CLI authenticated — `lkchindeveloper@gmail.com`
- [x] Subscription identified — Pay-As-You-Go, **spending limit OFF** ⚠️
- [x] Deleted leftover `rg-aks-training` — **saved ~RM 20/month** *(permanent)*
- [x] Architecture + cost model decided
- [ ] **Re-register `Microsoft.App`** — currently `Unregistered`
      ```bash
      az provider register --namespace Microsoft.App
      az provider show -n Microsoft.App --query registrationState -o tsv   # poll until Registered
      ```
      Takes 2–5 min. Without it, `az containerapp create` fails with an
      "unknown resource type" error that looks like a typo in your command.
- [ ] **Recreate a budget** — deleted during the revert
      Portal → Cost Management → Budgets → + Add. USD 5 is plenty.
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

## Phase 6 — Create Azure resources 🔵 YOU ARE HERE

> Previously created and then deleted. Timings below are measured, not estimated.

- [ ] Resource group *(free — just a folder, instant)*
      ```bash
      az group create --name rg-aiai-cookie --location southeastasia
      ```
- [ ] Container Apps environment *(free on Consumption, **~5 min to create**)*
      ```bash
      az containerapp env create \
        --name aiai-env --resource-group rg-aiai-cookie \
        --location southeastasia
      ```
      - Do **not** pass `--enable-workload-profiles` — a Dedicated profile adds a
        $0.10/hour management fee (~RM 295/month).
      - It auto-creates a Log Analytics workspace and warns about it. That's expected.
      - ⚠️ Deleting this later takes **~15 minutes**, so read the flags before you run it.
- [ ] Container app, scale-to-zero
      ```bash
      az containerapp create \
        --name aiai-cookie --resource-group rg-aiai-cookie \
        --environment aiai-env \
        --image ghcr.io/kerncl/aiai-cookie:latest \
        --target-port 8000 --ingress external \
        --min-replicas 0 --max-replicas 2 \
        --cpu 0.25 --memory 0.5Gi
      ```
      | Flag | Why it matters |
      |---|---|
      | `--min-replicas 0` | **This is what makes it RM 0.** Set to 1 and you pay ~RM 23/mo |
      | `--target-port 8000` | Must match `EXPOSE` in the Dockerfile |
      | `--ingress external` | Without it the app has no public URL |
      | `--cpu 0.25 --memory 0.5Gi` | Smallest size; larger burns the free grant faster |

## Phase 7 — Verify and automate ⬜

- [ ] Get the live URL
      ```bash
      az containerapp show --name aiai-cookie --resource-group rg-aiai-cookie \
        --query properties.configuration.ingress.fqdn -o tsv
      ```
- [ ] Open it — first hit after idle is a **15–30 s cold start**, that's expected
- [ ] Run the smoke suite against the live site
- [ ] Confirm it scales to zero when idle
- [ ] **Fix the CI deploy job** ⚠️ — see below
- [ ] Confirm a push to `main` deploys automatically

### ⚠️ Known: the CI deploy job currently fails

`.github/workflows/azure-deploy.yml` has two jobs. `build-test-push` **succeeds** —
that's how the image reached GHCR. The `deploy` job **fails**, because it targets
**App Service**, which was the earlier plan, and needs an
`AZURE_WEBAPP_PUBLISH_PROFILE` secret that doesn't exist.

So a red ✗ on your Actions tab is expected right now, and harmless — the image still
published. To fix, swap the deploy step for the Container Apps one already commented
out at the bottom of that file, and add an `AZURE_CREDENTIALS` secret.

## Phase 8 — Optional extras ⬜

- [ ] Custom domain (`aiaicookies.com`) — free on Container Apps, ~RM 60/yr to your registrar
- [ ] Managed TLS certificate — free, auto-renewing
- [ ] Replace the placeholder cookies with real products
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
| GHCR package | ✅ pushed, public | RM 0 |
| Budget alert | ❌ **deleted — recreate** | RM 0 |
| ~~ACR from AKS training~~ | ✅ deleted | ~~RM 20~~ → RM 0 |
| | **Projected total** | **≈ RM 0** |

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
| `Microsoft.App` not registered → deploy fails | ♻️ Was fixed, then unregistered — **redo it** |
| Leftover ACR billing RM 20/mo for a deleted cluster | ✅ Found and deleted |
| Budget "forecast exceeded" alarm on *historical* spend | ✅ Diagnosed — naive linear forecast, not a real overage |
| GHCR packages default to private | ✅ Didn't apply — public repo made the package public |
| `ghcr.io` rejects uppercase image paths | ✅ Handled in CI via `${GITHUB_REPOSITORY,,}` |
| CI deploy job targets App Service, not Container Apps | ⚠️ **Still broken — Phase 7** |
| Container Apps env takes ~5 min to create, ~15 to delete | ℹ️ Measured |
| Deleting a registry breaks scale-to-zero apps later | ℹ️ Why GHCR beats ACR here |
| Stopping an App Service doesn't stop its bill | ℹ️ Why we avoided App Service |
