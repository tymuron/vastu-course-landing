#!/usr/bin/env python3
"""Build the Ukrainian version of the landing: ua/index.html from index.html.

Same page, in Ukrainian, for buyers in Ukraine — monobank asked for it before
switching on «Покупка Частинами». What differs from the Russian page:

  * every visible string is translated from tools/ua_strings.json;
  * prices are in hryvnias (the «Покупка Частинами» prices on the platform,
    MONO_PRICES_UAH) — monobank requires the price in parts to equal the
    price shown, so these numbers must match the platform's;
  * the tariff cards pay by card (lava, in €/$ — the /buy page in Ukrainian)
    or by «Покупка Частинами monobank» (official badge + the two legal lines
    monobank requires next to any mention of it); no rubles, no GetCourse;
  * the payment FAQ answers for Ukraine, and a new FAQ says the course itself
    is taught in Russian;
  * the footer carries monobank's product legal block;
  * the language switch points back to the Russian page.

Never edit ua/index.html by hand. Change index.html, then run:
    python3 tools/make_ua_page.py
If the Russian page gains or changes text, the script stops and lists every
string that has no translation yet — add them to tools/ua_strings.json.
Text that is already Ukrainian (і ї є ґ and no ы э ъ ё) is left as is.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = " "
SITE = "https://annaromeo-vastu-course.onrender.com"
PORTAL = "https://vastu-portal-app.onrender.com"

# Hryvnia prices = the platform's MONO_PRICES_UAH (design-base / design-pro).
UAH = {"base": f"42{NB}066,73{NB}₴", "pro": f"98{NB}155,70{NB}₴"}
# Card prices in lava (GET /api/lava/offer/<offer> on the platform).
CARD = {"base": f"832,5{NB}€ · 930{NB}$", "pro": f"1{NB}942,5{NB}€ · 2{NB}170{NB}$"}
LAVA_OFFER = {"base": "4d14d633-0578-4ce8-8ad6-2d85bc3e0c49", "pro": "d6a1aacb-974b-411c-8cee-3d353a44c852"}
MONO_PLAN = {"base": "design-base", "pro": "design-pro"}

# The seller behind «Покупка Частинами monobank»: the Ukrainian ФОП that owns
# the monobank store (store id 2882500098_823). Shown in the footer next to
# the card seller. None = not known yet, nothing is printed.
FOP_UA = None  # e.g. "ФОП Прізвище Ім’я По батькові · РНОКПП 0000000000"

# monobank's two lines for any promotion of «Покупка Частинами»
# (knowledge-base/chast/marketing) and its product block for the site
# (knowledge-base/chast/marketing/product) — verbatim.
MONO_AD_LEGAL = (f"Реальна річна процентна ставка — 0,000001%, макс. строк кредитування до 400{NB}000 грн — 24 місяці. "
                 "Перший внесок — аванс у розмірі щомісячного платежу. "
                 "АТ «УНІВЕРСАЛ БАНК», Ліцензія НБУ №92 від 20.01.1994, у держреєстрі банків №226, деталі на monobank.ua")
MONO_PRODUCT_LEGAL = ("Покупка частинами monobank | Universal Bank. Надавач послуг: АТ «УНІВЕРСАЛ БАНК» ліцензія НБУ №92 від 20.01.1994, "
                      f"номер у держреєстрі банків № 226. Мінімальна сума розстрочки: 2 грн. Максимальна сума розстрочки: 400{NB}000 грн. "
                      "Реальна річна процентна ставка: 0,000001%. Доступний строк, платежів: 3 — 25. Порядок погашення: щомісячні платежі "
                      "рівними частинами. Перший платіж у момент оформлення покупки. Інформація про істотні характеристики продукту та "
                      'попередження розміщені на сайті продукту <a href="https://chast.monobank.ua" target="_blank" rel="noopener">chast.monobank.ua</a>')

CSS = """<style>
/* Ukrainian copy only (tools/make_ua_page.py) */
.tariff__card{margin:10px 0 0;font-size:13px;color:var(--on-dark-soft)}
.tariff__card b{color:var(--cream);font-weight:600}
.tariff--pro .tariff__card{color:rgba(66,35,38,.75)}
.tariff--pro .tariff__card b{color:var(--burgundy)}
/* «Покупка Частинами monobank»: monobank's own badge, unchanged (their rules
   forbid altering it), with the two legal lines they require next to it. */
.tariff__mono{display:flex;flex-direction:column;align-items:center;gap:9px;margin-top:18px;text-decoration:none}
.tariff__mono img{display:block;width:min(236px,100%);height:auto;transition:transform .3s var(--ease)}
.tariff__mono-cap{font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--on-dark-soft);text-align:center}
.tariff--pro .tariff__mono-cap{color:rgba(66,35,38,.78)}
.tariff__mono-legal{font-size:10px;line-height:1.5;color:var(--on-dark-soft);margin:10px 0 0;text-align:center}
.tariff--pro .tariff__mono-legal{color:rgba(66,35,38,.72)}
@media (hover:hover) and (pointer:fine){.tariff__mono:hover img{transform:translateY(-2px)}}
.foot__mono{margin:20px 0 0;font-size:11px;line-height:1.6;max-width:980px;opacity:.82}
</style>
"""

RU_ONLY = re.compile("[ыэъёЫЭЪЁ]")
UK_ONLY = re.compile("[іїєґІЇЄҐ]")
CYR = re.compile("[А-Яа-яЁёІіЇїЄєҐґ]")


def sub1(doc, pattern, repl, what, flags=0):
    new, n = re.subn(pattern, repl, doc, flags=flags)
    if n != 1:
        sys.exit(f"make_ua_page: expected exactly 1 match for {what}, found {n} — index.html changed; update this script")
    return new


def norm(text):
    return re.sub(r"\s+", " ", html.unescape(text).replace(NB, " ")).strip()


def bind(text):
    """Ukrainian typography: no line break after a 1–2 letter word or a short preposition."""
    return re.sub(r"(?<![\w’-])(\w{1,2}|від|без|про|при|під|над|між|для|або|щоб)\s(?=\S)", rf"\1{NB}", text)


def tariff_block(key):
    gold = key == "pro"
    btn = "btn--dark" if gold else "btn--ghost-d"
    return f"""<div class="tariff__price">
          <div class="tariff__now">{UAH[key]}</div>
          <p class="tariff__card">або карткою: <b>{CARD[key]}</b></p>
        </div>
        <a class="btn {btn} btn--wide" data-tariff="{key}" href="{PORTAL}/buy/{LAVA_OFFER[key]}?currency=EUR&amp;lang=uk" target="_blank" rel="noopener">Зайняти місце</a>
        <a class="tariff__mono" data-tariff="{key}-mono" href="{PORTAL}/buy/mono/{MONO_PLAN[key]}" target="_blank" rel="noopener">
          <span class="tariff__mono-cap">Для клієнтів monobank · у{NB}гривнях</span>
          <img src="assets/mono/chast-6-white.png" width="800" height="264" alt="Покупка Частинами monobank: це можна купити частинами, до 6 платежів" loading="lazy" decoding="async">
        </a>
        <p class="tariff__mono-legal">{MONO_AD_LEGAL}</p>
          <p class="tiny muted" style="margin-top:12px">Карткою в{NB}євро чи доларах — на{NB}захищеній сторінці lava.top, Покупка Частинами — у{NB}застосунку monobank. Відкриється в{NB}новій вкладці.</p>
      </article>"""


FAQ_UA = (
    f'<div class="faq__i"><button class="faq__q">Якою мовою проходить курс?</button><div class="faq__a"><div>'
    f"Російською: уроки, прямі ефіри, чат і матеріали курсу — російською мовою. Ця сторінка українською, щоб вам було зручно "
    f"ознайомитися з програмою та умовами.</div></div></div>\n"
    f'      <div class="faq__i"><button class="faq__q">Як оплатити з України?</button><div class="faq__a"><div>'
    f"Двома способами. Покупкою Частинами monobank — до 6 платежів у гривнях за тією самою ціною: посилання з лапкою під тарифом, "
    f"оформлення в застосунку monobank. Або карткою в євро чи доларах — за основною кнопкою тарифу, на захищеній сторінці lava.top. "
    f"Одразу після оплати на пошту, вказану під час оплати, прийде лист із доступом до платформи та чатів курсу."
    f'<div class="btn-row" style="margin-top:18px"><a class="btn btn--dark btn--sm js-book" href="#tarify">До тарифів</a>'
    f'<a class="btn btn--ghost-l btn--sm" href="https://t.me/annaromeo_vastu_bot" target="_blank" rel="noopener">Поставити запитання</a></div>'
    f"</div></div></div>"
)


def translate(doc, strings):
    text_map, script_map = strings["text"], strings["script"]
    missing = []

    def tr(raw, where):
        key = norm(raw)
        if not key or not CYR.search(key):
            return raw
        if UK_ONLY.search(key) and not RU_ONLY.search(key):
            return raw  # already Ukrainian (e.g. monobank's legal text)
        uk = text_map.get(key)
        if uk is None:
            missing.append((where, key))
            return raw
        lead = re.match(r"^\s*", raw).group(0)
        trail = re.search(r"\s*$", raw).group(0)
        return lead + bind(html.escape(uk, quote=(where == "attr"))) + trail

    # scripts/styles/comments are not text; translate the listed script literals only
    protected = []

    def protect(m):
        block = m.group(0)
        if block.lower().startswith("<script"):
            for ru, uk in script_map.items():
                block = block.replace(f"'{ru}'", f"'{uk}'").replace(f"`{ru}`", f"`{uk}`").replace(f'"{ru}"', f'"{uk}"')
        protected.append(block)
        return f"\x00{len(protected) - 1}\x00"

    doc = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", protect, doc, flags=re.S | re.I)

    out = []
    for tok in re.split(r"(<[^>]+>)", doc):
        if tok.startswith("<"):
            tok = re.sub(r'(\s(?:alt|title|aria-label|content|placeholder|data-col)=")([^"]*)(")',
                         lambda m: m.group(1) + tr(m.group(2), "attr") + m.group(3), tok)
            out.append(tok)
        else:
            parts = re.split(r"(\x00\d+\x00)", tok)
            out.append("".join(p if p.startswith("\x00") else tr(p, "text") for p in parts))
    doc = "".join(out)
    doc = re.sub(r"\x00(\d+)\x00", lambda m: protected[int(m.group(1))], doc)

    left_scripts = [ru for ru in script_map if f"'{ru}'" in doc or f"`{ru}`" in doc]
    if missing or left_scripts:
        lines = [f"  [{w}] {k}" for w, k in dict.fromkeys(missing)] + [f"  [script] {s}" for s in left_scripts]
        sys.exit("make_ua_page: no Ukrainian for these strings — add them to tools/ua_strings.json:\n" + "\n".join(lines))
    return doc


def main():
    doc = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    strings = json.load(open(os.path.join(ROOT, "tools", "ua_strings.json"), encoding="utf-8"))

    # head
    doc = sub1(doc, r'<html lang="ru">', '<html lang="uk">', "html lang")
    doc = sub1(doc, r'(<meta property="og:url" content=")[^"]*(")', rf"\g<1>{SITE}/ua/\2", "og:url")
    doc = sub1(doc, r'(<meta property="og:type"[^>]*>)', r'\1\n<meta property="og:locale" content="uk_UA">', "og:type")
    doc = sub1(doc, r"</head>", CSS + "</head>", "</head>")

    # language switch -> back to Russian
    doc = sub1(doc, r'<li class="nav__lang"><a href="[^"]*" lang="uk" hreflang="uk" title="[^"]*">UA</a></li>',
               f'<li class="nav__lang"><a href="{SITE}/" lang="ru" hreflang="ru" title="Російська версія">RU</a></li>', "language switch")

    # tariff cards: everything from the price to the end of the card (ruble
    # buttons, GetCourse, any monobank block the Russian page may carry)
    doc = sub1(doc, r'<div class="tariff__price">(?:(?!</article>).)*?data-tariff="base".*?</article>', "\x01TARIFF_base\x01", "Основной card", re.S)
    doc = sub1(doc, r'<div class="tariff__price">(?:(?!</article>).)*?data-tariff="pro".*?</article>', "\x01TARIFF_pro\x01", "Наставничество card", re.S)

    # payment FAQ -> course language + paying from Ukraine
    doc = sub1(doc, r'<div class="faq__i"><button class="faq__q">Есть ли рассрочка[^\n]*', "\x01FAQ\x01", "payment FAQ")

    # prices in hryvnias (Наставничество first: "175 000" contains "75 000")
    doc = re.sub(rf"175[ {NB}]000[ {NB}]₽", UAH["pro"], doc)
    doc = re.sub(rf"(?<!\d)75[ {NB}]000[ {NB}]₽", UAH["base"], doc)
    if "₽" in re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", "", doc, flags=re.S):
        sys.exit("make_ua_page: a ruble price survived — update the price substitutions")

    doc = translate(doc, strings)

    doc = doc.replace("\x01TARIFF_base\x01", tariff_block("base")).replace("\x01TARIFF_pro\x01", tariff_block("pro"))
    doc = doc.replace("\x01FAQ\x01", FAQ_UA)
    if FOP_UA:
        doc = sub1(doc, r'(<div class="foot__legal">)', rf'\1\n      <span>Продавець за Покупкою Частинами monobank: {html.escape(FOP_UA)}</span>', "footer seller")
    if "foot__mono" not in doc.split("</head>", 1)[1]:
        doc = sub1(doc, r'(<div class="foot__legal">.*?</div>)', rf'\1\n    <p class="foot__mono">{MONO_PRODUCT_LEGAL}</p>', "footer legal", re.S)

    # nothing Russian may remain in what a visitor reads
    visible = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->|<[^>]+>", " ", doc, flags=re.S)
    visible = visible.replace("ИП Чистякова Елена Яковлевна · ИНН 614334916160 · ОГРНИП 322930100040113", "")
    ru_left = sorted(set(w for w in re.findall(r"\w*[ыэъё]\w*", html.unescape(visible), re.I)))
    if ru_left:
        sys.exit(f"make_ua_page: Russian words left on the page: {', '.join(ru_left[:30])}")

    # one folder down: assets/ -> ../assets/ (attributes, CSS url(), JS strings)
    doc = doc.replace('="assets/', '="../assets/')
    doc = re.sub(r"url\(\s*(['\"]?)assets/", r"url(\1../assets/", doc)
    doc = doc.replace("'assets/", "'../assets/")
    if re.search(r"""(?<![./])['"(]assets/""", doc):
        sys.exit("make_ua_page: a relative asset path was not rewritten")

    banner = "<!-- GENERATED by tools/make_ua_page.py from index.html + tools/ua_strings.json — do not edit -->\n"
    os.makedirs(os.path.join(ROOT, "ua"), exist_ok=True)
    open(os.path.join(ROOT, "ua", "index.html"), "w", encoding="utf-8").write(banner + doc)
    print(f"ua/index.html written: {UAH['base']} / {UAH['pro']}, card {CARD['base']} / {CARD['pro']}, monobank «Покупка Частинами»")


if __name__ == "__main__":
    main()
