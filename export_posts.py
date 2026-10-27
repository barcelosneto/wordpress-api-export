"""Consulta publicações públicas do WordPress e salva um catálogo JSON. Somente GET."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def title_text(value):
    parser = PlainText()
    parser.feed(value)
    return "".join(parser.parts).strip()


def fetch_json(url, timeout=10):
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "PedroPortfolio-WPExport/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ValueError("Resposta maior que o limite de 2 MB")
        return json.loads(payload.decode("utf-8")), dict(response.headers.items())


def export_posts(site, max_pages=5, per_page=20, fetch=fetch_json):
    parts = urlsplit(site)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Informe a URL HTTPS do site, sem credenciais, query ou fragmento")
    if not 1 <= max_pages <= 20 or not 1 <= per_page <= 100:
        raise ValueError("Limites: 1–20 páginas e 1–100 publicações por página")
    base = site.rstrip("/") + "/wp-json/wp/v2/posts"
    catalog, identifiers = [], set()
    total_pages = None
    truncated = False
    pages = 0
    for page in range(1, max_pages + 1):
        query = urlencode({"page": page, "per_page": per_page, "status": "publish",
                           "orderby": "id", "order": "asc", "_fields": "id,date_gmt,link,title"})
        items, headers = fetch(base + "?" + query)
        pages += 1
        if not isinstance(items, list):
            raise ValueError("A API não retornou uma lista de publicações")
        headers = {key.lower(): value for key, value in headers.items()}
        raw_total = headers.get("x-wp-totalpages")
        if raw_total is not None:
            total_pages = int(raw_total)
            if total_pages < 0:
                raise ValueError("Total de páginas inválido")
        for item in items:
            if not isinstance(item, dict) or type(item.get("id")) is not int:
                raise ValueError("Publicação sem ID inteiro")
            if item["id"] in identifiers:
                raise ValueError("ID repetido entre páginas; repita a consulta")
            title = item.get("title")
            if not isinstance(title, dict) or not isinstance(title.get("rendered"), str):
                raise ValueError("Título fora do contrato")
            if not isinstance(item.get("link"), str) or not isinstance(item.get("date_gmt"), str):
                raise ValueError("Link ou data fora do contrato")
            identifiers.add(item["id"])
            catalog.append({"id": item["id"], "title": title_text(title["rendered"]),
                            "date_gmt": item["date_gmt"], "link": item["link"]})
        if not items or (total_pages is not None and page >= total_pages) or len(items) < per_page:
            break
        if page == max_pages:
            truncated = total_pages is None or total_pages > page
    return {"source": site, "pages_read": pages, "truncated": truncated,
            "total_posts_read": len(catalog), "posts": catalog}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site")
    parser.add_argument("saida", type=Path)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--per-page", type=int, default=20)
    args = parser.parse_args()
    report = export_posts(args.site, args.max_pages, args.per_page)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['total_posts_read']} publicações; truncado={report['truncated']}")


if __name__ == "__main__":
    main()
