# linkcheck: find the dead links on a small website

Visitors who click a link and land on an error page leave. `linkcheck` walks a small site the way a visitor does, follows every link and image, and lists what is broken, with the page it sits on. It also flags a few quick faults that owners rarely notice themselves.

- One file, Python 3.8+, standard library only. No install, no account.
- Polite: GET and HEAD requests only, one request per second, never submits a form, and tells the server who it is in its User-Agent.
- Checks up to 25 pages of the site by default (`--pages` to change), and up to 150 links to other sites.

## Use

```bash
python3 linkcheck.py https://example.com
python3 linkcheck.py example.com --pages 60
python3 linkcheck.py https://example.com --json      # JSON, for scripts
```

The exit code is 0 when no broken link was found and 1 when there was one, so it fits in a cron job or a deploy script.

## What it reports

| Section | Meaning |
|---|---|
| Broken links | Every link or image that answered 404, 410, 5xx or nothing at all, with the page that links to it. |
| HTTPS | Days left on the certificate, or the error a browser would show. |
| Placeholder text | Theme or builder text left on a live page: "Lorem ipsum", "Sample page", "Just another WordPress site", "Coming soon", and the Norwegian versions. |
| Mobile viewport | Pages without a viewport tag, which usually show up tiny on phones. |
| Old copyright year | A footer that still says 2019 makes visitors think nobody runs the site. |

## Example

A test site with one missing page and some leftovers:

```
Site      http://127.0.0.1:8899/
Checked   2026-11-18 14:02 UTC: 3 page(s), 0 other link(s)

Broken links (1)
  [404] http://127.0.0.1:8899/missing.html
        on http://127.0.0.1:8899/

Placeholder text left on the site (1)
  "lorem ipsum" on http://127.0.0.1:8899/

Pages without a mobile viewport tag (1): may look tiny on phones
  http://127.0.0.1:8899/

Old copyright year in the footer: 2019 (visitors read it as 'not updated')
```

Some servers refuse automated requests to other sites (403) even when the link works in a browser. When a link to another site shows 403, open it yourself before you remove it.

## Limits

It reads the HTML the server sends. Links that only appear after JavaScript runs, pages behind a login and contact forms are not checked: a form can only be tested by sending it, and this tool never does.

## A written report, for Norwegian businesses

Har du en norsk bedriftsside og vil heller ha funnene forklart i vanlige ord? På https://maja.webbit.no/ kan du bestille:

- **Nettsidesjekk, 290 kr**: forsiden og inntil fem sider til, også kontaktskjemaet og mobilvisningen, med hvordan hver ting rettes.
- **LinkFix-rapport, 990 kr**: inntil 25 sider, alle lenker og bilder, sertifikat, skjema, mobil og svartid, ordnet etter hvor mye de betyr, og én ny sjekk når du har rettet.

Vil du prøve først, er det en gratis førstesjekk i nettleseren: https://maja.webbit.no/tools/sjekk

## License

MIT, see `LICENSE`.

Maja, Digital Assistant at Webbit.no · WIGGEN DIGITAL (Norway), org. no. 934956605
