"""Permission-scoped inventory aggregates for the admin home page."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, jsonify

from routes.stock_inbounds import read_stock_balances
from utils.access_scope import can_access_scope
from utils.auth import get_current_user, permission_granted, require_admin_permission
from utils.db_helper import read_products
from utils.permission_catalog import ADMIN_ROUTE_PERMISSIONS, ADMIN_ROUTE_BRANCH_PERMISSIONS


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/admin/dashboard")


@dashboard_bp.route("/inventory", methods=["GET"])
@require_admin_permission(ADMIN_ROUTE_PERMISSIONS["dashboard"])
def inventory_summary():
    user = get_current_user()
    inventory_permissions = ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]
    allowed_types = {
        product_type
        for product_type, permission in (
            ("finished-product", inventory_permissions["products"]),
            ("raw-material", inventory_permissions["materials"]),
        )
        if permission_granted(permission)
    }
    if not allowed_types:
        return jsonify({"success": False, "message": "当前账号没有库存读取权限"}), 403

    balances = [
        row for row in read_stock_balances()
        if row["productType"] in allowed_types
        and can_access_scope(user, "store", row["storeId"])
        and can_access_scope(user, "warehouse", row["warehouseId"])
    ]
    amount = sum(
        (Decimal(str(row["inventoryAmount"])) for row in balances),
        Decimal("0"),
    )
    products_summary = None
    if "finished-product" in allowed_types:
        data = read_products()
        quantities = defaultdict(float)
        for row in balances:
            if row["productType"] == "finished-product":
                quantities[row["productId"]] += row["quantity"]

        def visible(product):
            stores = product.get("storeIds") or []
            return (
                (
                    user.get("allStores") or user.get("isSuperAdmin")
                    or any(can_access_scope(user, "store", store_id) for store_id in stores)
                )
                and can_access_scope(user, "warehouse", product.get("warehouseId"))
            )

        products = [product for product in data["products"] if visible(product)]
        enabled = sum(bool(product.get("enabled", True)) for product in products)
        low_stock = 0
        for product in products:
            # Legacy stock has no store split; scoped accounts use posted balances.
            legacy = data.get("inventory", {}).get(str(product["id"]), {})
            stock = quantities.get(product["id"], 0)
            if user.get("isSuperAdmin") or (
                user.get("allStores") and user.get("allWarehouses")
            ):
                stock = legacy.get("stock", stock)
            minimum = legacy.get("minStock") or 0
            if product.get("enabled", True) and (stock <= 0 or stock < minimum):
                low_stock += 1
        products_summary = {
            "total": len(products),
            "enabled": enabled,
            "disabled": len(products) - enabled,
            "lowStock": low_stock,
        }

    return jsonify({
        "success": True,
        "inventoryAmount": float(amount.quantize(Decimal("0.01"))),
        "productTypes": sorted(allowed_types),
        "products": products_summary,
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
