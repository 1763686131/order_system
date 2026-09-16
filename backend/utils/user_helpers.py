"""User identity helpers shared by business audit routes."""


def resolve_user_display_name(conn, identifier, default="系统用户"):
    """Resolve a login account from request headers to its display name."""
    account = str(identifier or "").strip()
    fallback = str(default or "").strip() or "系统用户"
    if not account:
        return fallback

    user = conn.execute(
        """
        SELECT username, name
        FROM users
        WHERE CAST(username AS TEXT) = ?
        LIMIT 1
        """,
        (account,),
    ).fetchone()
    if not user:
        return account

    return str(user["name"] or user["username"] or fallback).strip() or fallback
