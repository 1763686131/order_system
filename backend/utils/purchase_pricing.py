"""Keep entered tax-inclusive prices authoritative through procurement."""

from decimal import Decimal, ROUND_HALF_UP


def purchase_line_amounts(quantity, unit_price, tax_rate, tax_included_price=None):
    quantity = Decimal(str(quantity))
    tax_rate = Decimal(str(tax_rate))
    cent = Decimal("0.01")
    if tax_included_price is not None:
        tax_included_price = Decimal(str(tax_included_price))
        unit_price = tax_included_price * 100 / (100 + tax_rate)
        included_amount = quantity * tax_included_price
        total = included_amount.quantize(cent, rounding=ROUND_HALF_UP)
        amount = (included_amount * 100 / (100 + tax_rate)).quantize(cent, rounding=ROUND_HALF_UP)
        tax = total - amount
    else:
        unit_price = Decimal(str(unit_price)) if unit_price is not None else None
        base = quantity * (unit_price or Decimal("0"))
        amount = base.quantize(cent, rounding=ROUND_HALF_UP)
        tax = (base * tax_rate / 100).quantize(cent, rounding=ROUND_HALF_UP)
        total = amount + tax
    return {
        "unit_price": float(unit_price) if unit_price is not None else None,
        "tax_included_price": float(tax_included_price) if tax_included_price is not None else None,
        "amount": float(amount),
        "tax_amount": float(tax),
        "total_amount": float(total),
    }
