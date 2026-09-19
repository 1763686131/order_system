"""Shared role-based data scope helpers."""


SCOPE_FIELDS = {
    "store": ("allStores", "storeIds"),
    "warehouse": ("allWarehouses", "warehouseIds"),
}


def attach_role_scopes(conn, roles):
    """Attach storeIds and warehouseIds to serialized active roles."""
    role_ids = [role["id"] for role in roles]
    stores_by_role = {role_id: [] for role_id in role_ids}
    warehouses_by_role = {role_id: [] for role_id in role_ids}

    if role_ids:
        placeholders = ",".join("?" for _ in role_ids)
        store_rows = conn.execute(
            f"""
            SELECT role_id, store_id
            FROM role_stores
            WHERE role_id IN ({placeholders})
            ORDER BY role_id, store_id
            """,
            role_ids,
        ).fetchall()
        warehouse_rows = conn.execute(
            f"""
            SELECT role_id, warehouse_id
            FROM role_warehouses
            WHERE role_id IN ({placeholders})
            ORDER BY role_id, warehouse_id
            """,
            role_ids,
        ).fetchall()

        for scope in store_rows:
            stores_by_role[scope["role_id"]].append(scope["store_id"])
        for scope in warehouse_rows:
            warehouses_by_role[scope["role_id"]].append(scope["warehouse_id"])

    for role in roles:
        role["storeIds"] = stores_by_role.get(role["id"], [])
        role["warehouseIds"] = warehouses_by_role.get(role["id"], [])
    return roles


def merge_role_scopes(roles, full_access=False):
    """Merge multiple role scopes using union semantics."""
    return {
        "allStores": bool(full_access),
        "allWarehouses": bool(full_access),
        "storeIds": sorted({
            store_id
            for role in roles
            for store_id in role.get("storeIds", [])
        }),
        "warehouseIds": sorted({
            warehouse_id
            for role in roles
            for warehouse_id in role.get("warehouseIds", [])
        }),
    }


def accessible_scope_ids(user, scope_type):
    """Return None for unrestricted access, otherwise permitted scope IDs."""
    if scope_type not in SCOPE_FIELDS:
        raise ValueError(f"Unsupported scope type: {scope_type}")
    if not user:
        return set()

    all_key, ids_key = SCOPE_FIELDS[scope_type]
    if user.get(all_key) or user.get("isSuperAdmin"):
        return None

    result = set()
    for scope_id in user.get(ids_key, []):
        try:
            result.add(int(scope_id))
        except (TypeError, ValueError):
            continue
    return result


def can_access_scope(user, scope_type, scope_id):
    allowed_ids = accessible_scope_ids(user, scope_type)
    if allowed_ids is None:
        return True
    try:
        return int(scope_id) in allowed_ids
    except (TypeError, ValueError):
        return False


def filter_records_by_scope(records, user, scope_type, scope_id_getter):
    allowed_ids = accessible_scope_ids(user, scope_type)
    if allowed_ids is None:
        return records

    scoped_records = []
    for record in records:
        try:
            scope_id = int(scope_id_getter(record))
        except (TypeError, ValueError):
            continue
        if scope_id in allowed_ids:
            scoped_records.append(record)
    return scoped_records
