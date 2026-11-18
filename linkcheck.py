#!/usr/bin/env python3
"""linkcheck: a polite dead-link and quick-fault check for a small website.

GET/HEAD only, never submits forms, one request per second, honest User-Agent.
Python 3.8+, standard library only.

    python3 linkcheck.py https://example.com            # up to 25 pages
    python3 linkcheck.py https://example.com --pages 60
    python3 linkcheck.py https://example.com --json     # JSON for scripts

Exit code: 0 = no broken links found, 1 = broken links or the site did not answer.
"""
import sys, json, time, ssl, socket, re, argparse
import urllib.request, urllib.parse, urllib.error
from html.parser import HTMLParser
from datetime import datetime, timezone

UA = "linkcheck/1.0 (+https://github.com/ClaudVanDamCode/maja-linkcheck)"
PLACEHOLDERS = ["lorem ipsum", "hello world!", "sample page", "just another wordpress site",
                "under construction", "coming soon", "your text here", "hei, verden", "ny side",
                "eksempelside", "enda et wordpress", "din tekst her"]
SKIP_EXT = re.compile(r"\.(pdf|jpe?g|png|gif|webp|svg|ico|zip|docx?|xlsx?|mp4|mp3)$", re.I)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.imgs, self.text = [], [], []
        self.title, self.viewport = "", False
        self._in_title, self._skip = False, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"): self.links.append(a["href"].strip())
        if tag == "img" and a.get("src"): self.imgs.append(a["src"].strip())
        if tag == "title": self._in_title = True
        if tag in ("script", "style"): self._skip += 1
        if tag == "meta" and (a.get("name") or "").lower() == "viewport": self.viewport = True

    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False
        if tag in ("script", "style") and self._skip: self._skip -= 1

    def handle_data(self, d):
        if self._in_title: self.title += d
        elif not self._skip: self.text.append(d)


def fetch(url, method="GET"):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(2_000_000) if method == "GET" else b""
            return r.status, r.geturl(), body, None
    except urllib.error.HTTPError as e:
        return e.code, url, b"", None
    except Exception as e:
        return None, url, b"", str(e)[:160]


def cert_days(host):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                exp = datetime.strptime(ss.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z")
                return (exp.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days, None
    except Exception as e:
        return None, str(e)[:160]


def check(start, maxpages=25, maxlinks=150):
    if not start.startswith("http"): start = "https://" + start
    start = start.rstrip("/") + "/"
    host = urllib.parse.urlparse(start).hostname
    out = {"site": start, "checked": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "cert_days_left": None, "cert_error": None, "pages": [], "broken": [],
           "placeholders": [], "no_viewport": [], "copyright_years": {}}
    if start.startswith("https://"):
        out["cert_days_left"], out["cert_error"] = cert_days(host)
    queue, seen, links, came_from = [start], set(), {}, {}
    while queue and len(out["pages"]) < maxpages:
        url = queue.pop(0)
        if url in seen: continue
        seen.add(url)
        if out["pages"]: time.sleep(1)
        st, final, body, err = fetch(url)
        out["pages"].append({"url": url, "status": st, "error": err})
        if st is None or st >= 400:
            out["broken"].append({"on": came_from.get(url, "(start page)"), "link": url, "status": st, "error": err})
            continue
        if urllib.parse.urlparse(final).hostname != host or not body: continue
        html = body.decode("utf-8", "replace")
        p = Page(); p.feed(html)
        if not p.viewport: out["no_viewport"].append(url)
        low = " ".join(p.text).lower()
        for ph in PLACEHOLDERS:
            if ph in low: out["placeholders"].append({"page": url, "text": ph})
        yrs = re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", html, re.I)
        if yrs: out["copyright_years"][url] = yrs[-1]
        for href in p.links + p.imgs:
            if href.startswith(("mailto:", "tel:", "javascript:", "#", "data:")): continue
            u = urllib.parse.urljoin(final, href).split("#")[0]
            if not u.startswith("http"): continue
            same = urllib.parse.urlparse(u).hostname == host
            if same and href in p.links and not SKIP_EXT.search(u):
                if u not in seen and u not in queue:
                    queue.append(u); came_from[u] = url
            elif u not in links and len(links) < maxlinks:
                time.sleep(1)
                s2 = fetch(u, "HEAD")
                if s2[0] in (403, 405, None): s2 = fetch(u)   # some servers refuse HEAD
                links[u] = s2[0]
                if s2[0] is None or s2[0] >= 400:
                    out["broken"].append({"on": url, "link": u, "status": s2[0], "error": s2[3]})
    out["links_checked"] = len(links)
    return out


def report(o):
    print(f"Site      {o['site']}")
    print(f"Checked   {o['checked']}: {len(o['pages'])} page(s), {o['links_checked']} other link(s)")
    if o["cert_error"]: print(f"HTTPS     PROBLEM: {o['cert_error']}")
    elif o["cert_days_left"] is not None:
        warn = "  <- renew soon" if o["cert_days_left"] < 14 else ""
        print(f"HTTPS     certificate valid, {o['cert_days_left']} days left{warn}")
    print()
    if o["broken"]:
        print(f"Broken links ({len(o['broken'])})")
        for b in o["broken"]:
            why = b["status"] if b["status"] else (b["error"] or "no answer")
            print(f"  [{why}] {b['link']}\n        on {b['on']}")
    else:
        print("Broken links: none found")
    if o["placeholders"]:
        print(f"\nPlaceholder text left on the site ({len(o['placeholders'])})")
        for x in o["placeholders"]: print(f"  \"{x['text']}\" on {x['page']}")
    if o["no_viewport"]:
        print(f"\nPages without a mobile viewport tag ({len(o['no_viewport'])}): may look tiny on phones")
        for u in o["no_viewport"][:10]: print(f"  {u}")
    this_year = datetime.now(timezone.utc).year
    old = {u: y for u, y in o["copyright_years"].items() if int(y) < this_year - 1}
    if old:
        print(f"\nOld copyright year in the footer: {sorted(set(old.values()))[0]} (visitors read it as 'not updated')")


def main():
    ap = argparse.ArgumentParser(description="Polite dead-link and quick-fault check for a small website.")
    ap.add_argument("site")
    ap.add_argument("--pages", type=int, default=25, help="max pages to crawl on the site (default 25)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    a = ap.parse_args()
    o = check(a.site, a.pages)
    if a.json: json.dump(o, sys.stdout, ensure_ascii=False, indent=1); print()
    else: report(o)
    sys.exit(1 if o["broken"] else 0)


if __name__ == "__main__":
    main()
