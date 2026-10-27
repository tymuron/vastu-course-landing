#!/usr/bin/env python3
"""Build the masterclass copy of the landing: mk/index.html from index.html.

Same page, one difference: «Основной» costs 55 000 ₽ (75 000 crossed out) and
its button opens the СПЕЦЦЕНА tariff. «Наставничество» keeps 175 000 ₽ — Anna
gives no discount there. The page is hidden (noindex, linked from nowhere);
only masterclass participants get the link. The lava products are hidden
too, so there is no deadline: the price works for whoever has the link.

Never edit mk/index.html by hand. Change index.html, then run:
    python3 tools/make_mk_page.py
Every substitution must hit exactly once — if index.html changes shape the
script stops instead of quietly shipping a page with the wrong price.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = " "

# /buy/<offerId> on the platform (see vastu-portal/fulfilment.js for why it is
# never app.lava.top/products/...).
BASE_OFFER = "4d14d633-0578-4ce8-8ad6-2d85bc3e0c49"      # Основной 75 000 ₽
SPECIAL_OFFER = "ded0ec37-2888-4336-8e2d-38c49bab7df6"   # Основной СПЕЦЦЕНА 55 000 ₽
# «Рассрочка в рублях» = Мила's GetCourse pages (their paid orders reach the
# platform through /api/getcourse/order — see vastu-portal/server.js).
GK_BASE = "https://annaromeoschool.getcourse.ru/vastu-course_75"      # Основной 75 000 ₽
GK_SPECIAL = "https://annaromeoschool.getcourse.ru/vastu-course_55"   # Тариф МК 55 000 ₽

FULL = f"75{NB}000{NB}₽"
SPECIAL = f"55{NB}000{NB}₽"
NOTE = "Цена для участников мастер-класса"

CSS = """<style>
/* masterclass copy only (tools/make_mk_page.py) */
.hero__fact dd s{color:rgba(240,235,226,.54);font-size:.66em;margin-left:9px;text-decoration-thickness:1px}
.sticky__p1 s{color:rgba(240,235,226,.54);font-size:.62em;margin-left:7px;text-decoration-thickness:1px}
.tariff__now s{font-size:.44em;color:rgba(240,235,226,.56);text-decoration-thickness:1px}
.tariff__mk{margin:6px 0 18px;font-size:13px;letter-spacing:.04em;color:var(--gold)}
.price-was{display:block;margin-top:6px;font-size:13px;opacity:.62;text-decoration-thickness:1px}
@media(max-width:640px){.hero__fact dd s{display:inline;font-size:.6em;margin-left:6px}}
</style>
"""


def sub1(doc, pattern, repl, what):
    new, n = re.subn(pattern, repl, doc)
    if n != 1:
        sys.exit(f"make_mk_page: expected exactly 1 match for {what}, found {n} — index.html changed; update this script")
    return new


def main():
    doc = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

    # head: hidden from search, its own og:url, extra CSS
    doc = sub1(doc, r'(<meta name="viewport"[^>]*>)', r'\1\n<meta name="robots" content="noindex, nofollow">', "viewport meta")
    doc = sub1(doc, r'(<meta property="og:url" content=")[^"]*(")', r'\g<1>https://annaromeo-vastu-course.onrender.com/mk/\2', "og:url")
    doc = sub1(doc, r"</head>", CSS + "</head>", "</head>")
    doc = sub1(doc, r"(<meta name=\"description\" content=\"[^\"]*?)стоимость от 75 000 ₽", r"\1стоимость от 55 000 ₽ для участников мастер-класса", "meta description price")
    # no language switch: the Ukrainian page (ua/) has the full price, and
    # Ukrainians pay here through the «Покупка Частинами» badge
    doc = sub1(doc, r'<link rel="alternate" hreflang="ru" href="[^"]*">\n', "", "hreflang ru")
    doc = sub1(doc, r'<link rel="alternate" hreflang="uk" href="[^"]*">\n', "", "hreflang uk")
    doc = sub1(doc, r'\s*<li class="nav__lang">.*?</li>', "", "language switch")

    # prices («(?<!1)» keeps 175 000 untouched)
    doc = sub1(doc, rf'<div class="sticky__p1">{FULL}</div>', f'<div class="sticky__p1">{SPECIAL}<s>{FULL}</s></div>', "sticky price")
    doc = sub1(doc, rf"<dd>от([ {NB}]){FULL}</dd>", rf"<dd>от\g<1>{SPECIAL}<s>{FULL}</s></dd>", "hero price")
    doc = sub1(doc, rf'<span class="hero__note">Оплата на[ {NB}]сайте lava\.top · есть рассрочка в[ {NB}]рублях</span>', f'<span class="hero__note">{NOTE} · есть рассрочка в{NB}рублях</span>', "hero note")
    doc = sub1(doc, rf'<div class="tariff__now">{FULL}</div>', f'<div class="tariff__now">{SPECIAL} <s>{FULL}</s></div>\n          <p class="tariff__mk">{NOTE}</p>', "Основной card price")
    doc = sub1(doc, rf'(<td data-col="Основной"><b class="gold price-inline">){FULL}(</b>)', rf'\g<1>{SPECIAL}\2<s class="price-was">{FULL}</s>', "table price")
    doc = sub1(doc, rf"стоимость от([ {NB}]){FULL}", rf"стоимость от\g<1>{SPECIAL} для участников мастер-класса", "final screen price")
    doc = sub1(doc, rf"/buy/{BASE_OFFER}\?", f"/buy/{SPECIAL_OFFER}?", "Основной buy link")
    doc = sub1(doc, rf'href="{re.escape(GK_BASE)}"', f'href="{GK_SPECIAL}"', "Основной installment link")
    # monobank «Покупка Частинами»: the masterclass price in hryvnias (vastu-portal MONO_PRICES_UAH)
    doc = sub1(doc, r'/buy/mono/design-base"', '/buy/mono/design-base-mk"', "Основной monobank link")
    visible = re.sub(r"<s[^>]*>.*?</s>", "", doc.split("КОНФИГУРАЦИЯ")[0])
    if re.search(rf"(?<![1\d]){FULL}|от 75 000", visible):
        sys.exit("make_mk_page: a 75 000 ₽ price survived outside the strike-throughs")

    # one folder down: assets/ -> ../assets/ (attributes, CSS url(), JS strings)
    doc = doc.replace('="assets/', '="../assets/')
    doc = re.sub(r"url\(\s*(['\"]?)assets/", r"url(\1../assets/", doc)
    doc = doc.replace("'assets/", "'../assets/")
    if re.search(r"""(?<![./])['"(]assets/""", doc):
        sys.exit("make_mk_page: a relative asset path was not rewritten")

    banner = "<!-- GENERATED by tools/make_mk_page.py from index.html — do not edit; masterclass price copy -->\n"
    os.makedirs(os.path.join(ROOT, "mk"), exist_ok=True)
    open(os.path.join(ROOT, "mk", "index.html"), "w", encoding="utf-8").write(banner + doc)
    print("mk/index.html written: Основной 55 000 ₽ (СПЕЦЦЕНА, рассрочка vastu-course_55), Наставничество 175 000 ₽")


if __name__ == "__main__":
    main()
