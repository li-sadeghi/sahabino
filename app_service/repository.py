from typing import Any

from common.db import connection


def create_application(data: dict[str, Any]) -> dict[str, Any]:
    query = """
        INSERT INTO applications(name, package_name, category)
        VALUES (%(name)s, %(package_name)s, %(category)s)
        RETURNING *
    """
    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, data)
        return cur.fetchone()


def list_applications(active_only: bool = False) -> list[dict[str, Any]]:
    query = "SELECT * FROM applications"
    if active_only:
        query += " WHERE active = TRUE"
    query += " ORDER BY id"
    with connection() as conn, conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def get_application(application_id: int) -> dict[str, Any] | None:
    with connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM applications WHERE id = %s", (application_id,))
        return cur.fetchone()


def update_application(
    application_id: int, data: dict[str, Any]
) -> dict[str, Any] | None:
    fields = []
    params: dict[str, Any] = {"id": application_id}

    for name, value in data.items():
        fields.append(f"{name} = %({name})s")
        params[name] = value

    if not fields:
        return get_application(application_id)

    fields.append("updated_at = NOW()")
    query = (
        f"UPDATE applications SET {', '.join(fields)} "
        "WHERE id = %(id)s RETURNING *"
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def deactivate_application(application_id: int) -> dict[str, Any] | None:
    return update_application(application_id, {"active": False})


def database_is_ready() -> bool:
    with connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        return cur.fetchone() is not None
