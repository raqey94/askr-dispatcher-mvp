from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import json
import re
from pathlib import Path


@dataclass
class Driver:
    id: str
    name: str
    cities: List[str]
    type: str
    max_open_orders: int
    active: bool = True


def load_drivers(path: str = "drivers.json") -> List[Driver]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Driver(**item) for item in data["drivers"]]


def normalize_ar(text: str | None) -> str:
    text = (text or "").strip()
    text = text.replace("إ", "ا").replace("أ", "ا").replace("آ", "ا")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def extract_city(order: Dict[str, Any]) -> Tuple[str, str]:
    customer = order.get("customer") or {}
    city = customer.get("city") or ""
    location = customer.get("location") or ""
    combined = f"{city} {location}"

    n = normalize_ar(combined)
    if "خميس" in n:
        return "خميس مشيط", "city_or_address_contains_khamis"
    if "ابها" in n:
        return "أبها", "city_or_address_contains_abha"

    if city:
        return city, "customer_city"

    return "غير معروف", "unknown_city"


def classify_products(order: Dict[str, Any]) -> str:
    names = " ".join([item.get("name", "") for item in order.get("items", [])])
    n = normalize_ar(names)

    tags = []
    if "شوك" in n or "شوكلاته" in n or "شوكولات" in n:
        tags.append("شوكولاتة")
    if "مفرزن" in n or "مجمد" in n:
        tags.append("مفرزنات")
    if "رقائق" in n or "سمبوس" in n or "رول" in n:
        tags.append("رقائق/سمبوسة")
    if "معمول" in n:
        tags.append("معمول")
    if "بقلاوة" in n:
        tags.append("بقلاوة")
    if "صاج" in n or "خبز" in n:
        tags.append("خبز")

    return " / ".join(tags) if tags else "منتجات متنوعة"


def choose_driver(order: Dict[str, Any], drivers: List[Driver]) -> Tuple[Driver, str, str]:
    city, reason = extract_city(order)
    ncity = normalize_ar(city)

    for driver in drivers:
        if not driver.active:
            continue
        for c in driver.cities:
            nc = normalize_ar(c)
            if nc and nc not in ("external", "unknown") and nc in ncity:
                return driver, city, reason

    fallback = next((d for d in drivers if d.id == "abu_rayan" and d.active), None)
    if not fallback:
        fallback = next(d for d in drivers if d.active)
    return fallback, city, "external_or_unknown_city"


def build_note(order: Dict[str, Any], driver: Driver, city: str, reason: str) -> str:
    payment_method = order.get("payment_method", "غير معروف")
    total = order.get("total", {}).get("amount", "")
    currency = order.get("total", {}).get("currency", "SAR")
    product_type = classify_products(order)
    reference_id = order.get("reference_id", order.get("id", ""))

    cod_text = "نعم" if payment_method == "cod" else "لا"

    return (
        "توزيع تلقائي - عسكر الجنوب\n"
        f"رقم الطلب: {reference_id}\n"
        f"المندوب: {driver.name}\n"
        f"المنطقة المقروءة: {city}\n"
        f"سبب الإسناد: {reason}\n"
        f"نوع الطلب: {product_type}\n"
        f"طريقة الدفع: {payment_method}\n"
        f"دفع عند الاستلام: {cod_text}\n"
        f"مبلغ الطلب: {total} {currency}\n"
        "ملاحظة: تم إنشاء هذه الملاحظة بواسطة نظام توزيع المناديب."
    )


def summarize_assignments(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    drivers = load_drivers()
    summary: Dict[str, Any] = {}

    for order in orders:
        driver, city, reason = choose_driver(order, drivers)
        key = driver.name
        if key not in summary:
            summary[key] = {
                "orders_count": 0,
                "total_amount": 0.0,
                "cod_count": 0,
                "paid_count": 0,
                "cities": {},
                "products": {},
            }

        total = float(order.get("total", {}).get("amount") or 0)
        payment_method = order.get("payment_method", "")
        product_type = classify_products(order)

        summary[key]["orders_count"] += 1
        summary[key]["total_amount"] += total
        summary[key]["cod_count"] += 1 if payment_method == "cod" else 0
        summary[key]["paid_count"] += 0 if payment_method == "cod" else 1
        summary[key]["cities"][city] = summary[key]["cities"].get(city, 0) + 1
        summary[key]["products"][product_type] = summary[key]["products"].get(product_type, 0) + 1

    return summary
