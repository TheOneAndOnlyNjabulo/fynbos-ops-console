"""
Generates synthetic supplier invoice images for testing the Extraction/
Validation agents - run via CLI:
    cd backend
    .venv/Scripts/python.exe scripts/generate_test_invoices.py

Not part of the live app; these are test fixtures only (backend/scripts/fixtures/,
gitignored). Four invoices, each targeting a different Validation Agent outcome:
  - clean_small.png: everything correct, small amount -> should auto-approve
  - clean_large.png: everything correct, large amount -> should need finance
    director approval
  - missing_po.png: no PO number -> should be flagged regardless of amount
  - bad_arithmetic.png: line items don't sum to the stated subtotal -> should
    be flagged regardless of amount
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default(size)


def draw_invoice(
    path: Path,
    vendor: str,
    invoice_number: str,
    invoice_date: str,
    po_number: str | None,
    line_items: list[tuple[str, float, float, float]],  # description, qty, unit_price, line_total
    subtotal: float,
    vat: float,
    grand_total: float,
) -> None:
    img = Image.new("RGB", (900, 700), "white")
    draw = ImageDraw.Draw(img)
    title_font = _font(28)
    body_font = _font(18)

    y = 30
    draw.text((40, y), vendor, fill="black", font=title_font)
    y += 45
    draw.text((40, y), f"Invoice #: {invoice_number}", fill="black", font=body_font)
    y += 25
    draw.text((40, y), f"Date: {invoice_date}", fill="black", font=body_font)
    y += 25
    if po_number:
        draw.text((40, y), f"PO Number: {po_number}", fill="black", font=body_font)
    y += 40

    draw.line([(40, y), (860, y)], fill="black", width=2)
    y += 15
    draw.text((40, y), "Description", fill="black", font=body_font)
    draw.text((450, y), "Qty", fill="black", font=body_font)
    draw.text((550, y), "Unit Price", fill="black", font=body_font)
    draw.text((700, y), "Line Total", fill="black", font=body_font)
    y += 30
    draw.line([(40, y), (860, y)], fill="black", width=1)
    y += 15

    for desc, qty, unit_price, line_total in line_items:
        draw.text((40, y), desc, fill="black", font=body_font)
        draw.text((450, y), f"{qty:g}", fill="black", font=body_font)
        draw.text((550, y), f"R{unit_price:,.2f}", fill="black", font=body_font)
        draw.text((700, y), f"R{line_total:,.2f}", fill="black", font=body_font)
        y += 30

    y += 20
    draw.line([(500, y), (860, y)], fill="black", width=1)
    y += 15
    draw.text((550, y), "Subtotal:", fill="black", font=body_font)
    draw.text((700, y), f"R{subtotal:,.2f}", fill="black", font=body_font)
    y += 30
    draw.text((550, y), "VAT (15%):", fill="black", font=body_font)
    draw.text((700, y), f"R{vat:,.2f}", fill="black", font=body_font)
    y += 30
    draw.text((550, y), "Grand Total:", fill="black", font=title_font)
    draw.text((700, y), f"R{grand_total:,.2f}", fill="black", font=title_font)

    FIXTURES_DIR.mkdir(exist_ok=True)
    img.save(path)
    print(f"Wrote {path}")


def main() -> None:
    # Clean, small amount - should auto-approve
    draw_invoice(
        FIXTURES_DIR / "clean_small.png",
        vendor="Karoo Packaging Supplies (Pty) Ltd",
        invoice_number="INV-2026-4471",
        invoice_date="2026-08-15",
        po_number="PO-88213",
        line_items=[
            ("Cardboard boxes, medium (500 units)", 500, 4.00, 2000.00),
            ("Bubble wrap rolls", 10, 34.00, 340.00),
        ],
        subtotal=2340.00,
        vat=351.00,
        grand_total=2691.00,
    )

    # Clean, large amount - should need finance director approval
    draw_invoice(
        FIXTURES_DIR / "clean_large.png",
        vendor="Highveld Electronics Distribution",
        invoice_number="INV-2026-9902",
        invoice_date="2026-08-20",
        po_number="PO-90144",
        line_items=[
            ("55-inch LED television, model HX55", 30, 2500.00, 75000.00),
        ],
        subtotal=75000.00,
        vat=11250.00,
        grand_total=86250.00,
    )

    # Missing PO number - should be flagged regardless of amount
    draw_invoice(
        FIXTURES_DIR / "missing_po.png",
        vendor="Cape Coastal Homeware Co.",
        invoice_number="INV-2026-3310",
        invoice_date="2026-08-18",
        po_number=None,
        line_items=[
            ("Ceramic dinner sets", 40, 45.00, 1800.00),
        ],
        subtotal=1800.00,
        vat=270.00,
        grand_total=2070.00,
    )

    # Arithmetic doesn't reconcile - should be flagged regardless of amount
    draw_invoice(
        FIXTURES_DIR / "bad_arithmetic.png",
        vendor="Durban Freight & Fulfilment",
        invoice_number="INV-2026-5521",
        invoice_date="2026-08-22",
        po_number="PO-91002",
        line_items=[
            ("Warehouse handling, August", 1, 3200.00, 3200.00),
        ],
        subtotal=3200.00,
        vat=480.00,
        grand_total=4200.00,  # wrong on purpose - should be 3680.00
    )


if __name__ == "__main__":
    main()
