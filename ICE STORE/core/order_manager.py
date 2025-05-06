import json
from pathlib import Path
from datetime import datetime

ORDERS_FILE = Path(__file__).parent.parent / 'data' / 'orders.json'
PRODUCTS_FILE = Path(__file__).parent.parent / 'data' / 'products.json'

def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save_orders(data):
    ORDERS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')

def create_order(user_email, items, shipping, payment_method, discount_code=None, discount_rate=0):
    data = load_json(ORDERS_FILE)
    products = load_json(PRODUCTS_FILE)["products"]
    total = sum(next(p for p in products if p["id"] == pid)["price"] * qty for pid, qty in items.items())
    discounted = int(total*(1-discount_rate))
    order = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "user": user_email,
        "items": [{"id": pid, "qty": qty} for pid, qty in items.items()],
        "shipping": shipping,
        "payment_method": payment_method,
        "discount_code": discount_code,
        "total": total,
        "discounted_total": discounted,
        "date": datetime.now().isoformat()
    }
    data["orders"].append(order)
    save_orders(data)
    return order

def get_orders_by_user(user_email):
    data = load_json(ORDERS_FILE)
    return [o for o in data["orders"] if o["user"] == user_email]
