import json
import os
import random
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from error import problem
from models import Order
from store import OrderStore

store = OrderStore()
PAYMENTS_SERVICE_URL = os.getenv("PAYMENTS_SERVICE_URL", "http://localhost:5001/payments")
PAYMENT_TIMEOUT_SECONDS = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "2.0"))
PAYMENT_MAX_RETRIES = int(os.getenv("PAYMENT_MAX_RETRIES", "3"))


def validate(payload: Any) -> Tuple[bool, str]:
    """Validate the request body before accessing any of its fields."""
    if not isinstance(payload, dict):
        return False, "Request body must be a JSON object."

    required = {"customer_name", "customer_email", "items", "total_amount", "currency"}
    missing = sorted(required - payload.keys())
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}."

    if not isinstance(payload["customer_name"], str) or not payload["customer_name"].strip():
        return False, "customer_name must be a non-empty string."
    if not isinstance(payload["customer_email"], str) or "@" not in payload["customer_email"]:
        return False, "customer_email must be a valid email-like string."
    if not isinstance(payload["items"], list) or not payload["items"]:
        return False, "items must be a non-empty array."
    if not isinstance(payload["total_amount"], (int, float)) or isinstance(payload["total_amount"], bool):
        return False, "total_amount must be a number."
    if payload["total_amount"] <= 0:
        return False, "total_amount must be greater than zero."
    if not isinstance(payload["currency"], str) or len(payload["currency"]) != 3:
        return False, "currency must be a three-letter code."

    for item in payload["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("quantity"), int):
            return False, "Each item must contain a string name and integer quantity."
        if item["quantity"] <= 0:
            return False, "Item quantity must be greater than zero."

    return True, ""


def call_payments(order: Order, idempotency_key: str) -> Dict[str, Any]:
    """Call Payments with timeout, exponential backoff and jitter."""
    payload = json.dumps({
        "order_id": order.order_id,
        "amount": order.total_amount,
        "currency": order.currency,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json", "Idempotency-Key": idempotency_key}
    last_error = None

    for attempt in range(PAYMENT_MAX_RETRIES + 1):
        req = Request(PAYMENTS_SERVICE_URL, data=payload, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=PAYMENT_TIMEOUT_SECONDS) as response:
                if 200 <= response.status < 300:
                    return json.loads(response.read().decode("utf-8"))
                if 400 <= response.status < 500:
                    raise HTTPError(PAYMENTS_SERVICE_URL, response.status, "Payments 4xx", response.headers, None)
                last_error = RuntimeError(f"Payments returned {response.status}")
        except HTTPError as exc:
            if 400 <= exc.code < 500:
                raise
            last_error = exc
        except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc

        if attempt < PAYMENT_MAX_RETRIES:
            base = 0.1 * (2 ** attempt)
            time.sleep(base + random.uniform(0, base))

    raise RuntimeError("Payments service is unavailable") from last_error


def json_response(handler, status: int, body: Dict[str, Any], headers: Dict[str, str] | None = None):
    raw = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    for key, value in (headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(raw)


class OrdersHandler(BaseHTTPRequestHandler):
    server_version = "CampusEatsOrders/1.0"

    def log_message(self, fmt, *args):
        return

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def do_POST(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        if parts == ["orders"]:
            self.create_order()
            return
        if len(parts) == 3 and parts[0] == "orders" and parts[2] == "cancellation":
            self.cancel_order(parts[1])
            return
        self.not_found()

    def do_GET(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        if parts == ["orders"]:
            self.list_orders(parse_qs(parsed.query))
            return
        if len(parts) == 2 and parts[0] == "orders":
            self.get_order(parts[1])
            return
        self.not_found()

    def create_order(self):
        key = self.headers.get("Idempotency-Key")
        if not key:
            json_response(self, 400, problem(400, "Malformed request", "Idempotency-Key header is required for order creation."))
            return

        existing = store.get_idempotent_order(key)
        if existing:
            json_response(self, 201, existing.as_json(), {"Location": f"/orders/{existing.order_id}"})
            return

        payload = self.read_json()
        valid, detail = validate(payload)
        if not valid:
            json_response(self, 400, problem(400, "Malformed request", detail))
            return

        if payload["total_amount"] > 50000:
            json_response(self, 422, problem(422, "Order refused", "Orders above INR 50,000 require manual approval.", "https://campuseats.example/errors/order-limit"))
            return

        order = Order(
            internal_id=store.next_id(),
            order_id=f"CE-ORD-{uuid.uuid4().hex[:8].upper()}",
            customer_name=payload["customer_name"].strip(),
            customer_email=payload["customer_email"].strip(),
            items=payload["items"],
            total_amount=float(payload["total_amount"]),
            currency=payload["currency"].upper(),
        )

        try:
            payment = call_payments(order, key)
        except HTTPError:
            json_response(self, 422, problem(422, "Payment refused", "The Payments service refused the payment request.", "https://campuseats.example/errors/payment-refused"))
            return
        except RuntimeError:
            json_response(self, 503, problem(503, "Payment service unavailable", "The order was not created because payment confirmation could not be obtained.", "https://campuseats.example/errors/payment-unavailable"))
            return

        order.status = "CONFIRMED"
        order.payment_reference = payment.get("transaction_id")
        store.save(order)
        store.remember_idempotency(key, order.order_id)
        json_response(self, 201, order.as_json(), {"Location": f"/orders/{order.order_id}"})

    def get_order(self, order_id):
        order = store.get(order_id)
        if not order:
            json_response(self, 404, problem(404, "Order not found", f"No order exists with id '{order_id}'.", "https://campuseats.example/errors/not-found"))
            return
        json_response(self, 200, order.as_json())

    def list_orders(self, query):
        status = query.get("status", [None])[0]
        allowed = {"PENDING", "CONFIRMED", "CANCELLED"}
        if status and status.upper() not in allowed:
            json_response(self, 400, problem(400, "Malformed query", "status must be one of PENDING, CONFIRMED, or CANCELLED."))
            return
        orders = store.list(status.upper() if status else None)
        json_response(self, 200, {"orders": [o.as_json() for o in orders]})

    def cancel_order(self, order_id):
        order = store.get(order_id)
        if not order:
            json_response(self, 404, problem(404, "Order not found", f"No order exists with id '{order_id}'.", "https://campuseats.example/errors/not-found"))
            return
        if order.status == "CANCELLED":
            json_response(self, 409, problem(409, "State conflict", "The order has already been cancelled.", "https://campuseats.example/errors/state-conflict"))
            return
        if order.status not in {"PENDING", "CONFIRMED"}:
            json_response(self, 409, problem(409, "State conflict", f"Order in state {order.status} cannot be cancelled.", "https://campuseats.example/errors/state-conflict"))
            return
        order.status = "CANCELLED"
        json_response(self, 200, order.as_json())

    def not_found(self):
        json_response(self, 404, problem(404, "Resource not found", "The requested URL does not exist.", "https://campuseats.example/errors/not-found"))


def create_server(host="127.0.0.1", port=5000):
    return ThreadingHTTPServer((host, port), OrdersHandler)


if __name__ == "__main__":
    server = create_server(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
    print(f"CampusEats Orders service listening on http://0.0.0.0:{server.server_port}")
    server.serve_forever()
