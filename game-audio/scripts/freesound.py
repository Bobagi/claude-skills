# Freesound without an API key: search (CC0 only by default) and check sounds before downloading.
#   python freesound.py search "<query>" [--n 8] [--any-license]
#       candidates as: id | user | title | duration | license, best rated first
#   python freesound.py check <url or user/id> [...]
#       per sound: license read from the sound's own page (not from a search engine or another AI), duration,
#       format, sample rate and the /download/ URL to open in the logged-in browser
# Downloading the ORIGINAL needs a logged-in Freesound session: open each /download/ URL in the user's Chrome
# (navigation, one per URL; see SKILL.md, "Baixar"). The HQ preview (mp3) is public but lossy: last resort.
import argparse
import html
import re
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (game-audio skill)"}
CC0 = "publicdomain/zero"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "replace")


def search(query, n, any_license):
    params = {"q": query, "s": "Rating highest first"}
    if not any_license:
        params["f"] = 'license:"Creative Commons 0"'
    page = get("https://freesound.org/search/?" + urllib.parse.urlencode(params))
    seen, out = set(), []
    for user, sid, title in re.findall(r'href="/people/([^/]+)/sounds/(\d+)/"[^>]*>([^<]{3,})<', page):
        if sid in seen:
            continue
        seen.add(sid)
        out.append((sid, user, html.unescape(title.strip())))
        if len(out) >= n:
            break
    for sid, user, title in out:
        info = check(f"{user}/{sid}")
        print(f"{sid} | {user} | {title} | {info['duration']} | {info['license']}")


def check(ref):
    m = re.search(r"(?:people/)?([^/\s]+)/sounds/(\d+)", ref) or re.match(r"([^/\s]+)/(\d+)$", ref)
    if not m:
        raise SystemExit(f"nao entendi: {ref} (use a URL do som ou usuario/id)")
    user, sid = m.group(1), m.group(2)
    url = f"https://freesound.org/people/{user}/sounds/{sid}/"
    page = get(url)
    lic = re.search(r"creativecommons\.org/(publicdomain/zero|licenses/[a-z-]+)/([0-9.]+)", page)
    lic = f"{lic.group(1)}/{lic.group(2)}" if lic else "?"
    lic_name = "CC0" if CC0 in lic else ("CC-BY (exige credito)" if "/by/" in lic else lic)
    if "sampling+" in lic or "-nc" in lic:
        lic_name += " NAO COMERCIAL/RESTRITA: nao usar"
    dl = re.search(rf"(/people/[^\"]+/sounds/{sid}/download/[^\"]+)", page)

    def field(label):
        # The info row under the player: <p ...>Label</p> followed by <p ...>value</p>.
        f = re.search(r">\s*" + label + r"\s*</p>\s*<p[^>]*>\s*([^<]+)", page)
        return f.group(1).strip() if f else "?"

    return {"id": sid, "user": user, "url": url, "license": lic_name, "duration": field("Duration"),
            "type": field("Type"), "rate": field("Sample rate"),
            "download": "https://freesound.org" + html.unescape(dl.group(1)) if dl else "?"}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--n", type=int, default=8)
    s.add_argument("--any-license", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("refs", nargs="+")
    a = ap.parse_args()
    if a.cmd == "search":
        search(a.query, a.n, a.any_license)
    else:
        for r in a.refs:
            i = check(r)
            print(f"{i['id']} | {i['user']} | {i['license']} | {i['duration']} | {i['type']} {i['rate']}\n    {i['download']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
