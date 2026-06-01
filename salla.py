from __future__ import annotations

from typing import Any, Dict, List
import httpx

from .config import SALLA_ACCESS_TOKEN, SALLA_BASE_URL


def _headers() -> Dict[str, str]:
    if not SALLA_ACCESS_TOKEN:
        raise RuntimeError("SALLA_ACCESS_TOKEN is missing. Put it in .env")
    return {
        "Authorization": f"Bearer {SALLA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def list_orders(page: int = 1, sort_by: str = "created_at") -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{SALLA_BASE_URL}/orders",
            headers=_headers(),
            params={"page": page, "sort_by": sort_by},
        )
        r.raise_for_status()
        payload = r.json()
        return payload.get("data", [])


async def add_order_history(order_id: int | str, note: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{SALLA_BASE_URL}/orders/{order_id}/histories",
            headers=_headers(),
            json={"note": note},
        )
        r.raise_for_status()
        return r.json()
