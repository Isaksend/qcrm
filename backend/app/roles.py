"""Роли CRM: Admin, Manager, Sales Representative (+ legacy user, super_admin)."""

from __future__ import annotations

SALES_ROLES = frozenset({"user", "sales_representative"})
COMPANY_ADMIN_ROLES = frozenset({"admin", "manager"})


def is_sales_rep(role: str | None) -> bool:
    return (role or "") in SALES_ROLES


def is_company_admin(role: str | None) -> bool:
    return (role or "") in COMPANY_ADMIN_ROLES


def is_super_admin(role: str | None) -> bool:
    return (role or "") == "super_admin"


def is_manager(role: str | None) -> bool:
    return (role or "") == "manager"


def sees_own_deals_only(role: str | None) -> bool:
    """Менеджер и линейные продажи — только сделки, где они ответственные (userId)."""
    return is_sales_rep(role) or is_manager(role)


def can_manage_company_users(role: str | None) -> bool:
    """Создание/удаление пользователей компании — только admin и super_admin."""
    return role in ("admin", "super_admin")
