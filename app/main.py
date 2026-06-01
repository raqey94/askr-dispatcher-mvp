from __future__ import annotations

from typing import Any, Dict
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from .config import WEBHOOK_SECRET, DRY_RUN, AUTO_ADD_ORDER_NOTE
from .dispatch import load_drivers, choose_driver, build_note, summarize_assignments
from .salla import list_orders, add_order_history


app = FastAPI(title="Askr Dispatch MVP", version="0.1.0")


@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "Askr Dispatch MVP",
        "dry_run": DRY_RUN,
        "auto_add_order_note": AUTO_ADD_ORDER_NOTE,
    }


@app.post("/webhooks/salla/order")
async def salla_order_webhook(
    request: Request,
    x_askr_secret: str | None = Header(default=None),
):
    # اجعل هذا الهيدر في إعدادات Webhook داخل سلة:
    # key: x-askr-secret
    # value: WEBHOOK_SECRET
    if x_askr_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload: Dict[str, Any] = await request.json()

    # تختلف بنية Webhook حسب نسخة سلة، لذلك نحاول التقاط الطلب بمرونة
    order = payload.get("data") or payload.get("order") or payload
    order_id = order.get("id") or order.get("order_id")

    drivers = load_drivers()
    driver, city, reason = choose_driver(order, drivers)
    note = build_note(order, driver, city, reason)

    result = {
        "assigned_driver": driver.name,
        "city": city,
        "reason": reason,
        "order_id": order_id,
        "note_preview": note,
        "written_to_salla": False,
        "dry_run": DRY_RUN,
    }

    if order_id and AUTO_ADD_ORDER_NOTE and not DRY_RUN:
        await add_order_history(order_id, note)
        result["written_to_salla"] = True

    return result


@app.get("/preview/latest")
async def preview_latest_orders(page: int = 1):
    orders = await list_orders(page=page)
    drivers = load_drivers()

    items = []
    for order in orders:
        driver, city, reason = choose_driver(order, drivers)
        note = build_note(order, driver, city, reason)
        items.append({
            "order_id": order.get("id"),
            "reference_id": order.get("reference_id"),
            "city": city,
            "assigned_driver": driver.name,
            "reason": reason,
            "payment_method": order.get("payment_method"),
            "total": order.get("total"),
            "note_preview": note,
        })

    return {
        "count": len(items),
        "items": items,
        "summary": summarize_assignments(orders),
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(page: int = 1):
    orders = await list_orders(page=page)
    summary = summarize_assignments(orders)

    rows = ""
    for driver, stats in summary.items():
        rows += f"""
        <tr>
          <td>{driver}</td>
          <td>{stats["orders_count"]}</td>
          <td>{stats["total_amount"]:.2f}</td>
          <td>{stats["cod_count"]}</td>
          <td>{stats["paid_count"]}</td>
          <td>{", ".join([f"{k}: {v}" for k, v in stats["cities"].items()])}</td>
          <td>{", ".join([f"{k}: {v}" for k, v in stats["products"].items()])}</td>
        </tr>
        """

    mode = "تجريبي DRY RUN" if DRY_RUN else "فعّال"
    note_mode = "مفعلة" if AUTO_ADD_ORDER_NOTE else "غير مفعلة"

    return f"""
    <html dir="rtl" lang="ar">
      <head>
        <meta charset="utf-8" />
        <title>لوحة توزيع مناديب عسكر الجنوب</title>
        <style>
          body {{ font-family: Arial, sans-serif; padding: 24px; background: #fafafa; }}
          table {{ border-collapse: collapse; width: 100%; background: white; }}
          th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
          th {{ background: #f0f0f0; }}
          .note {{ background: #fff7df; padding: 12px; margin-bottom: 16px; }}
        </style>
      </head>
      <body>
        <h1>لوحة توزيع مناديب عسكر الجنوب</h1>
        <div class="note">
          الوضع الحالي: {mode} /
          إضافة الملاحظة داخل سلة: {note_mode}
        </div>
        <table>
          <thead>
            <tr>
              <th>المندوب</th>
              <th>عدد الطلبات</th>
              <th>إجمالي المبالغ</th>
              <th>COD</th>
              <th>مدفوع</th>
              <th>المدن</th>
              <th>أنواع المنتجات</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </body>
    </html>
    """
