import feedparser

RSS_URL = "https://www.gobiernodecanarias.org/boc/feeds/capitulo/autoridades_personal_oposiciones.rss"

feed = feedparser.parse(RSS_URL)

print(f"Entradas encontradas: {len(feed.entries)}")
print("=" * 80)

for i, entry in enumerate(feed.entries, 1):
    print(f"\nENTRADA {i}")
    print("-" * 80)

    for key, value in entry.items():
        print(f"{key}: {value}")
