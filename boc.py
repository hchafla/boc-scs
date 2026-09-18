name: Actualizar noticias BOC SCS

on:
  workflow_dispatch:
  schedule:
    - cron: "*/15 * * * *"

permissions:
  contents: write

jobs:
  actualizar:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Instalar dependencias
        run: |
          pip install feedparser beautifulsoup4

      - name: Procesar RSS
        run: |
          python - <<'PY'
          import feedparser
          import json
          import re
          from bs4 import BeautifulSoup
          from datetime import datetime

          RSS_URL = "https://www.gobiernodecanarias.org/boc/feeds/capitulo/autoridades_personal_oposiciones.rss"
          OUTPUT = "noticias.json"

          # --------------------------------------------------
          # Cargar noticias existentes
          # --------------------------------------------------

          try:
              with open(OUTPUT, "r", encoding="utf-8") as f:
                  noticias_existentes = json.load(f)
          except (FileNotFoundError, json.JSONDecodeError):
              noticias_existentes = []

          existentes = {
              noticia["id"]: noticia
              for noticia in noticias_existentes
              if noticia.get("id")
          }

          # --------------------------------------------------
          # Descargar RSS
          # --------------------------------------------------

          feed = feedparser.parse(RSS_URL)

          nuevas = 0
          noticias_scs = 0

          # --------------------------------------------------
          # Procesar entradas
          # --------------------------------------------------

          for entry in feed.entries:

              title_original = entry.get("title", "").strip()

              # Solo Servicio Canario de la Salud
              if not title_original.startswith(
                  "Servicio Canario de la Salud.-"
              ):
                  continue

              noticias_scs += 1

              entry_id = entry.get("id", "").strip()

              if not entry_id:
                  continue

              # ------------------------------------------------
              # Título limpio
              # ------------------------------------------------

              title = re.sub(
                  r"^Servicio Canario de la Salud\.-\s*",
                  "",
                  title_original
              )

              # ------------------------------------------------
              # Fecha de publicación
              # ------------------------------------------------

              published = entry.get("published", "")

              if published:
                  dt = datetime.strptime(
                      published,
                      "%a, %d %b %Y %H:%M:%S %z"
                  )

                  date = dt.strftime("%Y-%m-%d")
              else:
                  date = ""

              # ------------------------------------------------
              # Obtener CVE
              # ------------------------------------------------

              summary_html = entry.get("summary", "")

              soup = BeautifulSoup(
                  summary_html,
                  "html.parser"
              )

              text = soup.get_text(
                  " ",
                  strip=True
              )

              match = re.search(
                  r"CVE:\s*(BOC-[A-Z]-\d{4}-\d+-\d+)",
                  text
              )

              cve = match.group(1) if match else ""

              # ------------------------------------------------
              # Crear noticia
              # ------------------------------------------------

              noticia = {
                  "id": entry_id,
                  "title": title,
                  "url": entry.get("link", ""),
                  "date": date,
                  "source": "BOC",
                  "organismo": "Servicio Canario de la Salud",
                  "cve": cve
              }

              # ------------------------------------------------
              # Añadir o actualizar
              # ------------------------------------------------

              if entry_id not in existentes:
                  existentes[entry_id] = noticia
                  nuevas += 1
              else:
                  existentes[entry_id].update(noticia)

          # --------------------------------------------------
          # Ordenar de más reciente a más antigua
          # --------------------------------------------------

          noticias = list(existentes.values())

          noticias.sort(
              key=lambda x: (
                  x.get("date", ""),
                  x.get("id", "")
              ),
              reverse=True
          )

          # --------------------------------------------------
          # Guardar JSON
          # --------------------------------------------------

          with open(OUTPUT, "w", encoding="utf-8") as f:
              json.dump(
                  noticias,
                  f,
                  ensure_ascii=False,
                  indent=2
              )

          # --------------------------------------------------
          # Mostrar información en el log
          # --------------------------------------------------

          print(f"Entradas RSS: {len(feed.entries)}")
          print(f"Noticias SCS encontradas: {noticias_scs}")
          print(f"Nuevas noticias: {nuevas}")
          print(f"Total histórico: {len(noticias)}")
          print("=" * 80)

          for noticia in noticias[:10]:
              print(
                  f"{noticia['date']} | "
                  f"{noticia['cve']} | "
                  f"{noticia['title']}"
              )
          PY

      - name: Guardar cambios
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add noticias.json

          if git diff --cached --quiet; then
            echo "No hay cambios."
          else
            git commit -m "Actualizar noticias BOC SCS"
            git push
          fi
