# aiai 饼家 — aiai cookie

A bilingual catalogue of the Chinese biscuits aiai sells, and exactly what goes
into each one. Flask app, deployed to Azure App Service.

Chinese (Simplified) is the primary language with English alongside. Customers
can search by ingredient in **either language** and filter out allergens — so
someone with a peanut allergy sees only what's safe for them.

Searching 绿豆 correctly surfaces 杏仁饼 as well as 绿豆糕, because the almond
cookie is made with 绿豆粉 — the search reads the ingredient list, not just names.

## Run it locally

### With Docker (matches production)

```bash
docker compose up -d
```

Open <http://localhost:5000>. Stop with `docker compose down`.

`data/` and `static/images/cookies/` are mounted read-only, so editing a cookie
or dropping in a photo shows up on refresh — **no rebuild needed**. Only changes
to `app.py`, templates or CSS need `docker compose up -d --build`.

### Without Docker

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>. This runs Flask's dev server with hot reload for
templates too, which is handier while changing the layout.

### About the image

| | |
|---|---|
| Base | `python:3.12-slim`, two-stage build |
| Size | ~153 MB |
| User | `appuser` (uid 10001), non-root |
| Port | 8000 inside the container |
| Health | `HEALTHCHECK` hits the app's own `/healthz` |

Gunicorn runs as PID 1 via the exec-form `CMD`, so `docker stop` shuts it down
immediately instead of waiting out the 10-second grace period.

## Adding a cookie

### 1. The photo

Drop the original (full-size, straight off your phone is fine) into `images_raw/`,
then run:

```bash
python scripts/optimize_images.py
```

This squares it, scales it to 900px and compresses it into
`static/images/cookies/` — typically a 10x size reduction. `images_raw/` is
gitignored, so only the web-sized copies get deployed.

Name the file after the cookie: `salted-caramel.jpg`.

### 2. The entry

Add an object to the `cookies` array in `data/cookies.json`:

```json
{
  "slug": "pineapple-cake",
  "name_zh": "凤梨酥",
  "name_en": "Pineapple Cake",
  "tagline_zh": "酸甜适中，奶香酥皮",
  "tagline_en": "Tart-sweet filling in a buttery shell.",
  "price": 24.9,
  "unit_zh": "每盒 10 块",
  "unit_en": "box of 10",
  "image": "pineapple-cake.jpg",
  "available": true,
  "tags": ["bestseller"],
  "dietary": ["pork-free"],
  "ingredients": [
    { "zh": "小麦粉", "en": "Wheat flour" },
    { "zh": "凤梨馅", "en": "Pineapple filling", "note_zh": "自制", "note_en": "house-made" }
  ],
  "allergens": ["gluten", "dairy", "egg"],
  "nutrition": {
    "serving_size_g": 30, "calories": 140,
    "fat_g": 6.0, "carbs_g": 19.0, "sugar_g": 10.0, "protein_g": 1.8
  }
}
```

| Field | Notes |
|---|---|
| `slug` | URL-safe id, ASCII; becomes `/cookie/pineapple-cake`. Must be unique. |
| `name_zh` / `name_en` | Chinese shows large, English underneath in grey. |
| `unit_zh` / `unit_en` | How it's sold — 每盒 10 块 / box of 10. |
| `available` | `false` greys the card out and shows 售罄. |
| `tags` | `bestseller` 热销, `seasonal` 季节限定, `vegan` 纯素 — drives the corner badge. |
| `allergens` | Keys from `allergen_labels` at the top of the file. Drives the filter. |
| `dietary` | Keys from `dietary_labels`, e.g. `pork-free` 无猪油. Shows a blue tag. |
| `nutrition` | Optional. Omit the whole object and the section is hidden. |

### The two filters work in opposite directions

This is deliberate, and worth knowing before you add more:

- **`allergens` is exclusive** — ticking 花生 *hides* everything containing peanut.
  The question is "keep me safe."
- **`dietary` is inclusive** — ticking 只看无猪油 *keeps only* items carrying the
  marker. The question is "show me what I can eat."

So a product with no `dietary` entries disappears the moment any dietary filter
is ticked. Give every pork-free product the `pork-free` marker, or it will look
as though it contains lard.

Both `zh` and `en` are searchable. A cookie with no photo yet still renders —
it falls back to a 🍪 placeholder.

### Interface wording

Button labels, headings and the allergen disclaimer live in `data/ui.json`,
separate from the catalogue so you can reword the UI without touching product
data. Each entry has a `zh` and an `en`.

## Checking it still works

With the app running:

```bash
python scripts/smoke.py
```

Hits the live site over HTTP and verifies the filters, bilingual search,
ingredient rendering and API encoding. Exits non-zero on failure.

## Deploying to Azure

Now that it's containerized, the **same image** runs on either target. Pick on
cold start vs cost:

| | App Service for Containers (B1) | Container Apps (Consumption) |
|---|---|---|
| Cost | ~$13/month, fixed | Likely **$0** — free grant covers 180k vCPU-sec + 2M requests/month |
| Cold start | None, always warm | 1–3 s after idle |
| Custom domain + SSL | Yes | Yes |

For a shop catalogue the question is whether a customer clicking your link from
Instagram or WhatsApp should ever wait 1–3 seconds for a blank page. If that
matters, pay the $13. If you're starting out and want $0, Container Apps with
`minReplicas: 0` is genuinely free at this traffic level — and because it's the
same container, switching later is a redeploy, not a rewrite.

Do **not** set `minReplicas: 1` on Container Apps "to avoid cold starts" — that
removes scale-to-zero and ends up costing more than B1 for less.

### Where the image lives

Use **GitHub Container Registry** (`ghcr.io`) — free, and you already build on
GitHub Actions. Azure Container Registry works too but adds a monthly fee per
registry with no free tier.

### Option A — App Service for Containers (B1)

```bash
az group create --name aiai-cookie-rg --location southeastasia

az appservice plan create \
  --name aiai-cookie-plan --resource-group aiai-cookie-rg \
  --sku B1 --is-linux

az webapp create \
  --name aiai-cookie --resource-group aiai-cookie-rg \
  --plan aiai-cookie-plan \
  --deployment-container-image-name ghcr.io/<you>/aiai-cookie:latest

# The container listens on 8000, not 80 — App Service must be told.
az webapp config appsettings set \
  --name aiai-cookie --resource-group aiai-cookie-rg \
  --settings WEBSITES_PORT=8000
```

### Option B — Container Apps (scale to zero)

```bash
az containerapp env create \
  --name aiai-env --resource-group aiai-cookie-rg --location southeastasia

az containerapp create \
  --name aiai-cookie --resource-group aiai-cookie-rg \
  --environment aiai-env \
  --image ghcr.io/<you>/aiai-cookie:latest \
  --target-port 8000 --ingress external \
  --min-replicas 0 --max-replicas 2 \
  --cpu 0.25 --memory 0.5Gi
```

`southeastasia` (Singapore) is the closest region to Malaysia — lower latency
for your customers than a US region.

### Why not the Free tier

App Service Free (F1) cannot attach a custom domain at all, so `aiaicookies.com`
needs B1 or higher. Container Apps has no such restriction.

App Service names must be globally unique across Azure; if `aiai-cookie` is
taken, pick another and update `AZURE_WEBAPP_NAME` in
`.github/workflows/azure-deploy.yml`.

### Continuous deployment

The workflow in `.github/workflows/azure-deploy.yml` builds the image, pushes it
to `ghcr.io`, and tells Azure to pull the new tag.

For **App Service**: download the publish profile from the portal
(**Deployment Center → Manage publish profile**) and save it as a GitHub secret
named `AZURE_WEBAPP_PUBLISH_PROFILE`.

For **Container Apps**: create a service principal and save it as `AZURE_CREDENTIALS`.

Every push to `main` then deploys automatically.

### Custom domain and HTTPS

```bash
az webapp config hostname add \
  --webapp-name aiai-cookie --resource-group aiai-cookie-rg \
  --hostname www.aiaicookies.com

az webapp config ssl create \
  --name aiai-cookie --resource-group aiai-cookie-rg \
  --hostname www.aiaicookies.com
```

The managed certificate is free on B1+ and renews itself. Point a CNAME at
`aiai-cookie.azurewebsites.net` with your registrar first.

## Project layout

```
app.py                      Flask routes
data/cookies.json           the catalogue — the only file you edit routinely
data/ui.json                bilingual interface wording
templates/                  Jinja2 pages
static/css/style.css        all styling (light + dark, CJK font stack)
static/images/cookies/      web-sized photos, served to visitors
images_raw/                 your originals (gitignored)
scripts/optimize_images.py  raw photo -> web-sized photo
scripts/smoke.py            HTTP smoke test of the running site
```

## Room to grow

`GET /api/cookies` already returns the catalogue as JSON, and `/healthz` is wired
up for App Service health checks. When ordering comes, the data layer is the one
function `load_catalogue()` in `app.py` — swap it for a database call and nothing
else has to change.
