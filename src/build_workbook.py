#!/usr/bin/env python3
"""Build the P13 deliverable workbook (run: python3 src/build_workbook.py).

Sheets:
- Audit Summary: KPIs + defects-by-type table + column scores, ALL live
  formulas over the Defect Register and Fixed Data sheets; native bar chart.
- Defect Register: all 300 defects (from outputs/defect_register.csv).
- Fixed Data: all 1,500 fixed rows (from data/processed/orders_FIXED.csv).

Output: outputs/data_quality_audit_SAMPLE.xlsx
Formulas use only functions LibreOffice and Excel both calculate
(COUNTIF / COUNTIFS / SUM / SUMPRODUCT); medians are avoided here.
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "outputs" / "data_quality_audit_SAMPLE.xlsx"

HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
SUB_FONT = Font(size=10, italic=True, color="595959")
KPI_FONT = Font(bold=True, size=12)
MONEY_FMT = '#,##0'
PCT_FMT = '0.0%'

TYPE_LABELS = [
    ("duplicate_order_id", "Duplicate order_id"),
    ("missing_email", "Missing email"),
    ("invalid_email", "Invalid email"),
    ("missing_city", "Missing city"),
    ("negative_quantity", "Negative quantity"),
    ("zero_unit_price", "Zero unit price"),
    ("total_mismatch", "Total mismatch"),
    ("future_date", "Future date"),
    ("malformed_date", "Malformed date"),
    ("orphan_product_code", "Orphan product code"),
    ("category_mismatch", "Category mismatch"),
    ("nonstandard_payment", "Non-standard payment"),
]
COLUMNS = ["order_id", "order_date", "customer_name", "customer_email",
           "product_code", "product_name", "category", "quantity",
           "unit_price", "total_amount", "payment_method", "city"]


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def main():
    register = list(csv.DictReader(open(ROOT / "outputs" / "defect_register.csv", encoding="utf-8")))
    fixed = list(csv.DictReader(open(ROOT / "data" / "processed" / "orders_FIXED.csv", encoding="utf-8")))
    n_reg = len(register)          # 300
    n_fix = len(fixed)             # 1,500
    reg_last = n_reg + 1           # last data row on Defect Register
    fix_last = n_fix + 1           # last data row on Fixed Data

    wb = Workbook()

    # ---- Defect Register (build first so formulas can reference it) ----
    ws_r = wb.active
    ws_r.title = "Defect Register"
    reg_headers = ["defect_id", "order_id", "column", "defect_type",
                   "severity", "detail", "fix_applied"]
    ws_r.append(reg_headers)
    for d in register:
        ws_r.append([d[h] for h in reg_headers])
    style_header(ws_r, 1, len(reg_headers))
    for w, col in zip([12, 13, 16, 22, 10, 52, 48], range(1, 8)):
        ws_r.column_dimensions[get_column_letter(col)].width = w
    ws_r.freeze_panes = "A2"
    ws_r.auto_filter.ref = f"A1:G{reg_last}"

    # ---- Fixed Data ----
    ws_f = wb.create_sheet("Fixed Data")
    fix_headers = ["order_id", "order_date", "customer_name", "customer_email",
                   "product_code", "product_name", "category", "quantity",
                   "unit_price", "total_amount", "payment_method", "city",
                   "audit_flag"]
    ws_f.append(fix_headers)
    for r in fixed:
        ws_f.append([r["order_id"], r["order_date"], r["customer_name"], r["customer_email"],
                     r["product_code"], r["product_name"], r["category"],
                     int(r["quantity"]), int(r["unit_price"]), int(r["total_amount"]),
                     r["payment_method"], r["city"], r["audit_flag"]])
    style_header(ws_f, 1, len(fix_headers))
    for w, col in zip([13, 12, 20, 26, 12, 22, 15, 9, 11, 13, 17, 12, 44], range(1, 14)):
        ws_f.column_dimensions[get_column_letter(col)].width = w
    for row in range(2, fix_last + 1):
        ws_f.cell(row=row, column=10).number_format = MONEY_FMT
        ws_f.cell(row=row, column=9).number_format = MONEY_FMT
    ws_f.freeze_panes = "A2"
    ws_f.auto_filter.ref = f"A1:M{fix_last}"

    # ---- Audit Summary ----
    ws = wb.create_sheet("Audit Summary", 0)
    ws["A1"] = "Data Quality Audit — Al-Noor Traders (SAMPLE)"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = ("Orders file, Jan–Jun 2026 · audited 9 Nov 2026 · every KPI below is a live "
                "formula over the Defect Register and Fixed Data sheets — change a row and the summary re-runs.")
    ws["A2"].font = SUB_FONT
    ws.merge_cells("A2:F2")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 30

    ws["A4"] = "KPI"
    ws["B4"] = "Value"
    ws["C4"] = "How it is calculated"
    style_header(ws, 4, 3)
    # Rows received = fixed rows + duplicate copies dropped
    kpis = [
        ("Rows received",
         f"=COUNTA('Fixed Data'!A2:A{fix_last})+COUNTIF('Defect Register'!D2:D{reg_last},\"duplicate_order_id\")",
         "Fixed rows + duplicate copies dropped"),
        ("Unique orders",
         f"=COUNTA('Fixed Data'!A2:A{fix_last})",
         "Order IDs in the fixed file"),
        ("Orders with ≥1 defect",
         f"=SUMPRODUCT(1/COUNTIF('Defect Register'!B2:B{reg_last},'Defect Register'!B2:B{reg_last}))",
         "Distinct order IDs in the register"),
        ("Clean orders",
         f"=COUNTIF('Fixed Data'!M2:M{fix_last},\"OK\")",
         "Fixed rows with no audit flag"),
        ("Total defects found",
         f"=COUNTA('Defect Register'!A2:A{reg_last})",
         "Rows in the Defect Register"),
        ("Critical defects",
         f"=COUNTIF('Defect Register'!E2:E{reg_last},\"Critical\")",
         "Register rows marked Critical"),
        ("High defects",
         f"=COUNTIF('Defect Register'!E2:E{reg_last},\"High\")",
         "Register rows marked High"),
        ("Medium defects",
         f"=COUNTIF('Defect Register'!E2:E{reg_last},\"Medium\")",
         "Register rows marked Medium"),
        ("Fixed total (PKR)",
         f"=SUM('Fixed Data'!J2:J{fix_last})",
         "Sum of total_amount in the fixed file"),
        ("Rows still flagged for the client",
         f"=COUNTA('Fixed Data'!A2:A{fix_last})-COUNTIF('Fixed Data'!M2:M{fix_last},\"OK\")",
         "Fixed rows whose audit_flag is not OK"),
    ]
    row = 5
    for label, formula, note in kpis:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        c = ws.cell(row=row, column=2, value=formula)
        c.font = KPI_FONT
        if "PKR" in label:
            c.number_format = MONEY_FMT
        ws.cell(row=row, column=3, value=note).font = Font(size=10, color="595959")
        row += 1

    type_start = row + 1
    ws.cell(row=type_start, column=1, value="Defects by type").font = Font(bold=True, size=12, color="1F3864")
    ws.cell(row=type_start + 1, column=1, value="Defect type").font = HDR_FONT
    ws.cell(row=type_start + 1, column=2, value="Rows").font = HDR_FONT
    ws.cell(row=type_start + 1, column=3, value="Share of defects").font = HDR_FONT
    style_header(ws, type_start + 1, 3)
    for i, (dtype, label) in enumerate(TYPE_LABELS):
        r = type_start + 2 + i
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=f"=COUNTIF('Defect Register'!D2:D{reg_last},\"{dtype}\")")
        ws.cell(row=r, column=3, value=f"=IF($B${type_start + 2 + len(TYPE_LABELS)}=0,0,B{r}/$B${type_start + 2 + len(TYPE_LABELS)})")
        ws.cell(row=r, column=3).number_format = PCT_FMT
    tot = type_start + 2 + len(TYPE_LABELS)
    ws.cell(row=tot, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=tot, column=2, value=f"=SUM(B{type_start + 2}:B{tot - 1})").font = Font(bold=True)
    ws.cell(row=tot, column=3, value=f"=SUM(C{type_start + 2}:C{tot - 1})").font = Font(bold=True)
    ws.cell(row=tot, column=3).number_format = PCT_FMT

    chart = BarChart()
    chart.type = "col"
    chart.title = "Defects by type"
    chart.y_axis.title = "Rows"
    chart.x_axis.title = "Defect type"
    chart.height = 7.5
    chart.width = 15
    chart.shape = 4
    data = Reference(ws, min_col=2, min_row=type_start + 1, max_row=tot - 1)
    cats = Reference(ws, min_col=1, min_row=type_start + 2, max_row=tot - 1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.dataLabels = None
    ws.add_chart(chart, f"A{tot + 2}")

    score_start = tot + 20
    ws.cell(row=score_start, column=1, value="Column quality scores").font = Font(bold=True, size=12, color="1F3864")
    ws.cell(row=score_start + 1, column=1, value="Column").font = HDR_FONT
    ws.cell(row=score_start + 1, column=2, value="Defects").font = HDR_FONT
    ws.cell(row=score_start + 1, column=3, value="Quality").font = HDR_FONT
    style_header(ws, score_start + 1, 3)
    for i, col in enumerate(COLUMNS):
        r = score_start + 2 + i
        ws.cell(row=r, column=1, value=col)
        ws.cell(row=r, column=2, value=f"=COUNTIF('Defect Register'!C2:C{reg_last},\"{col}\")")
        ws.cell(row=r, column=3, value=f"=1-B{r}/$B$5")
        ws.cell(row=r, column=3).number_format = PCT_FMT

    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 62
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = "1:4"

    wb.save(XLSX)
    print(f"wrote {XLSX} ({n_reg} register rows, {n_fix} fixed rows)")


if __name__ == "__main__":
    main()
