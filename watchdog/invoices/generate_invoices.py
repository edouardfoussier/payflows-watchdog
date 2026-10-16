"""Generate demo vendor invoices (PDF) consistent with the Payflows sandbox.

Buyer is the sandbox entity Halden SAS; vendors, countries and PO numbers come from the sandbox.
Foreign EU/UK vendors invoice with reverse charge (0 % VAT), like the sandbox's own invoices.

    python3 generate_invoices.py   # writes <number>.html and <number>.pdf next to this script
"""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE = "/private/tmp/claude-501/-Users-edouardfoussier-code-payflows-payflows-cld/698139e4-018d-433f-886c-c2fe246913b6/scratchpad/chrome-pdf"

LABELS = {
    "fr": dict(title="FACTURE", number="N°", date="Date", due="Échéance", bill_to="Facturé à", ref="Référence client",
               po="Bon de commande", po_missing="non communiqué", desc="Description", qty="Qté", unit="Prix unitaire HT",
               total="Total HT", subtotal="Total HT", vat="TVA", grand="Total TTC", buyer_dept="Service comptabilité fournisseurs",
               terms="Paiement par virement à 30 jours. Coordonnées bancaires selon la fiche fournisseur.",
               demo="DOCUMENT DE DÉMONSTRATION · Finance AI Lab Payflows × Anthropic · Team 11 · sans valeur comptable"),
    "en": dict(title="INVOICE", number="No.", date="Date", due="Due date", bill_to="Bill to", ref="Customer reference",
               po="Purchase order", po_missing="not provided", desc="Description", qty="Qty", unit="Unit price (excl. VAT)",
               total="Amount", subtotal="Total excl. VAT", vat="VAT", grand="Total due", buyer_dept="Accounts Payable",
               terms="Payment by bank transfer within 30 days. Bank details as per vendor record.",
               demo="DEMO DOCUMENT · Finance AI Lab Payflows × Anthropic · Team 11 · no accounting value"),
}

INVOICES = [
    dict(number="KES-2026-0312", lang="fr", vendor="Kestrel Events", legal="Kestrel Events SAS",
         address="14 rue des Petites Écuries, 75010 Paris, France", color="#b4462b", date="15/10/2026", due="14/11/2026",
         ref="Séminaire équipe Q4 – Lyon", po=None, vat_rate=0.20, vat_note=None,
         lines=[("Location salle de séminaire – 2 jours", 2, 1450), ("Traiteur – déjeuners et pauses (40 personnes)", 80, 37.5),
                ("Animation team building", 1, 1000)]),
    dict(number="JOR-2026-0148", lang="en", vendor="Jorvik Agency", legal="Jorvik Agency Ltd",
         address="22 Fitzwilliam Square, Dublin 2, Ireland", color="#2b6cb4", date="15/10/2026", due="14/11/2026",
         ref="Social ads campaign – October 2026", po=None, vat_rate=0.0,
         vat_note="Reverse charge – VAT to be accounted for by the recipient (Art. 196, Directive 2006/112/EC)",
         lines=[("Campaign creative production", 1, 1800), ("Social ads campaign management – October 2026", 1, 1400)]),
    dict(number="IVR-2026-1102", lang="fr", vendor="Ivrea Software", legal="Ivrea Software SAS",
         address="5 rue de la Bourse, 69002 Lyon, France", color="#3a7d44", date="15/10/2026", due="14/11/2026",
         ref="Licences Ivrea Analytics – extension équipe Data", po=None, vat_rate=0.20, vat_note=None,
         lines=[("Licence Ivrea Analytics – utilisateur supplémentaire (01/11/2026 – 31/10/2027)", 10, 480)]),
    dict(number="GAL-2026-0417", lang="en", vendor="Galdane Events", legal="Galdane Events Ltd",
         address="48 Clerkenwell Road, London EC1M 5PS, United Kingdom", color="#7a3fb4", date="15/10/2026", due="14/11/2026",
         ref="Client cocktail – Big Data & AI Paris, 5 Nov 2026", po=None, vat_rate=0.0,
         vat_note="Outside the scope of UK VAT – reverse charge, VAT to be accounted for by the recipient",
         lines=[("Venue hire – evening reception", 1, 2000), ("Catering – cocktail for 60 guests", 60, 32.5),
                ("Event hosts", 2, 150)]),
    dict(number="KAL-2026-0389", lang="en", vendor="Kaldera Consulting", legal="Kaldera Consulting GmbH",
         address="Friedrichstraße 68, 10117 Berlin, Germany", color="#b48a2b", date="15/10/2026", due="14/11/2026",
         ref="Procure-to-pay process audit", po=None, vat_rate=0.0,
         vat_note="Reverse charge – recipient liable for VAT (§13b UStG, Art. 196 Directive 2006/112/EC)",
         lines=[("Procure-to-pay process audit – senior consultant (days)", 3, 1350), ("Travel expenses (Berlin – Paris)", 1, 180)]),
    dict(number="HES-2026-0921", lang="en", vendor="Hestia Hosting", legal="Hestia Hosting GmbH",
         address="Hanauer Landstraße 182, 60314 Frankfurt am Main, Germany", color="#2b8ab4", date="15/10/2026", due="14/11/2026",
         ref="Dedicated servers – Halden production cluster", po="PAYF-1027455", vat_rate=0.0,
         vat_note="Reverse charge – recipient liable for VAT (§13b UStG, Art. 196 Directive 2006/112/EC)",
         lines=[("Dedicated servers hosting – October 2026", 1, 12612.5)]),
]


def money(x, lang):
    s = f"{x:,.2f}".replace(",", " ")
    return (s.replace(".", ",") + " €") if lang == "fr" else ("€" + s.replace(" ", ","))


def html(inv):
    L = LABELS[inv["lang"]]
    m = lambda x: money(x, inv["lang"])
    rows = "".join(
        f'<tr><td>{d}</td><td class="n">{q:g}</td><td class="n">{m(u)}</td><td class="n">{m(q * u)}</td></tr>'
        for d, q, u in inv["lines"])
    ht = sum(q * u for _, q, u in inv["lines"])
    vat = round(ht * inv["vat_rate"], 2)
    po = inv["po"] or f"<i>{L['po_missing']}</i>"
    note = f'<p class="muted" style="margin-top:4mm">{inv["vat_note"]}</p>' if inv["vat_note"] else ""
    return f"""<!doctype html><html lang="{inv['lang']}"><head><meta charset="utf-8"><title>{L['title']} {inv['number']}</title>
<style>
@page {{ size: A4; margin: 18mm; }}
body {{ font-family: Helvetica, Arial, sans-serif; color: #1a1a1a; font-size: 11pt; }}
.top {{ display: flex; justify-content: space-between; align-items: flex-start; }}
.brand {{ font-size: 20pt; font-weight: 700; color: {inv['color']}; }}
h1 {{ font-size: 22pt; margin: 0 0 4mm; letter-spacing: 1px; }}
.muted {{ color: #666; }}
.box {{ border: 1px solid #ddd; border-radius: 4px; padding: 4mm; width: 44%; }}
.parties {{ display: flex; justify-content: space-between; margin: 10mm 0 8mm; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 4mm; }}
th {{ text-align: left; background: #f3f3f3; padding: 3mm; font-size: 10pt; }}
td {{ padding: 3mm; border-bottom: 1px solid #eee; }}
td.n, th.n {{ text-align: right; }}
.totals {{ width: 48%; margin-left: auto; margin-top: 6mm; }}
.totals td {{ border: none; padding: 1.5mm 3mm; }}
.totals .grand td {{ font-weight: 700; border-top: 2px solid #1a1a1a; font-size: 12pt; }}
.demo {{ margin-top: 14mm; padding: 3mm; border: 1px dashed #b4462b; color: #b4462b; font-size: 9pt; text-align: center; }}
</style></head><body>
<div class="top">
  <div><div class="brand">{inv['vendor']}</div><div class="muted">{inv['legal']}<br>{inv['address']}</div></div>
  <div style="text-align:right"><h1>{L['title']}</h1><div><b>{L['number']} {inv['number']}</b></div>
  <div>{L['date']} : {inv['date']}</div><div>{L['due']} : {inv['due']}</div></div>
</div>
<div class="parties">
  <div class="box"><div class="muted">{L['bill_to']}</div><b>Halden SAS</b><br>{L['buyer_dept']}<br>Paris, France</div>
  <div class="box"><div class="muted">{L['ref']}</div>{inv['ref']}<br>{L['po']} : {po}</div>
</div>
<table><tr><th>{L['desc']}</th><th class="n">{L['qty']}</th><th class="n">{L['unit']}</th><th class="n">{L['total']}</th></tr>{rows}</table>
<table class="totals">
  <tr><td>{L['subtotal']}</td><td class="n">{m(ht)}</td></tr>
  <tr><td>{L['vat']} {inv['vat_rate'] * 100:g} %</td><td class="n">{m(vat)}</td></tr>
  <tr class="grand"><td>{L['grand']}</td><td class="n">{m(ht + vat)}</td></tr>
</table>
{note}
<p class="muted" style="margin-top:6mm">{L['terms']}</p>
<div class="demo">{L['demo']}</div>
</body></html>"""


def main():
    for inv in INVOICES:
        src = HERE / f"{inv['number']}.html"
        src.write_text(html(inv))
        pdf = HERE / f"{inv['number']}.pdf"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={PROFILE}",
                        f"--print-to-pdf={pdf}", f"file://{src}"], capture_output=True, timeout=60)
        ht = sum(q * u for _, q, u in inv["lines"])
        print(f"{pdf.name:22} {inv['vendor']:20} HT {ht:>10,.2f}  VAT {inv['vat_rate']:.0%}  PO {inv['po'] or '-'}")


if __name__ == "__main__":
    main()
