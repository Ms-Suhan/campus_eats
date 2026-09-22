import json
import os
import random
import threading
import time
import uuid
import hashlib
import gzip
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

PAYMENTS_SERVICE_URL = os.getenv(
    "PAYMENTS_SERVICE_URL",
    "http://localhost:5001/payments"
)
PAYMENT_TIMEOUT_SECONDS = float(
    os.getenv("PAYMENT_TIMEOUT_SECONDS", "2.0")
)
PAYMENT_MAX_RETRIES = int(
    os.getenv("PAYMENT_MAX_RETRIES", "3")
)

# Assignment 5 configuration
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", "60"))
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "campuseats-demo-token")

# Per-client rate-limit state
rate_lock = threading.Lock()
rate_state = {}

# Idempotency result cache
idempotency_lock = threading.Lock()
idempotency_results = {}


def validate(payload: Any) -> Tuple[bool, str]:
    """Validate the request body before accessing any fields."""

    if not isinstance(payload, dict):
        return False, "Request body must be a JSON object."

    required = {
        "customer_name",
        "customer_email",
        "items",
        "total_amount",
        "currency",
    }

    missing = sorted(required - payload.keys())

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}."

    if (
        not isinstance(payload["customer_name"], str)
        or not payload["customer_name"].strip()
    ):
        return False, "customer_name must be a non-empty string."

    if (
        not isinstance(payload["customer_email"], str)
        or "@" not in payload["customer_email"]
    ):
        return False, "customer_email must be a valid email-like string."

    if (
        not isinstance(payload["items"], list)
        or not payload["items"]
    ):
        return False, "items must be a non-empty array."

    if (
        not isinstance(payload["total_amount"], (int, float))
        or isinstance(payload["total_amount"], bool)
    ):
        return False, "total_amount must be a number."

    if payload["total_amount"] <= 0:
        return False, "total_amount must be greater than zero."

    if (
        not isinstance(payload["currency"], str)
        or len(payload["currency"]) != 3
    ):
        return False, "currency must be a three-letter code."

    for item in payload["items"]:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("name"), str)
            or not isinstance(item.get("quantity"), int)
        ):
            return False, (
                "Each item must contain a string name "
                "and integer quantity."
            )

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

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Idempotency-Key": idempotency_key,
    }

    last_error = None

    for attempt in range(PAYMENT_MAX_RETRIES + 1):

        req = Request(
            PAYMENTS_SERVICE_URL,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(
                req,
                timeout=PAYMENT_TIMEOUT_SECONDS
            ) as response:

                if 200 <= response.status < 300:
                    return json.loads(
                        response.read().decode("utf-8")
                    )

                if 400 <= response.status < 500:
                    raise HTTPError(
                        PAYMENTS_SERVICE_URL,
                        response.status,
                        "Payments 4xx",
                        response.headers,
                        None,
                    )

                last_error = RuntimeError(
                    f"Payments returned {response.status}"
                )

        except HTTPError as exc:

            if 400 <= exc.code < 500:
                raise

            last_error = exc

        except (
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:

            last_error = exc

        if attempt < PAYMENT_MAX_RETRIES:
            base = 0.1 * (2 ** attempt)
            time.sleep(
                base + random.uniform(0, base)
            )

    raise RuntimeError(
        "Payments service is unavailable"
    ) from last_error


def make_etag(order: Order) -> str:
    """
    Generate an ETag from the current representation.
    The ETag changes whenever the serialized representation changes.
    """

    raw = json.dumps(
        order.as_json(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    digest = hashlib.sha256(raw).hexdigest()

    return f'"{digest}"'


def json_response(
    handler,
    status: int,
    body: Dict[str, Any],
    headers: Dict[str, str] | None = None,
):
    """
    Send a JSON response with common Assignment 5 headers.
    """

    raw = json.dumps(body).encode("utf-8")

    # gzip for sufficiently large JSON responses
    accept_encoding = handler.headers.get(
        "Accept-Encoding",
        ""
    )

    use_gzip = (
        len(raw) >= 512
        and "gzip" in accept_encoding.lower()
    )

    if use_gzip:
        raw = gzip.compress(raw)

    handler.send_response(status)

    handler.send_header(
        "Content-Type",
        "application/json"
    )

    handler.send_header(
        "Content-Length",
        str(len(raw))
    )

    handler.send_header(
        "X-Content-Type-Options",
        "nosniff"
    )

    handler.send_header(
        "Strict-Transport-Security",
        "max-age=31536000; includeSubDomains"
    )

    handler.send_header(
        "Access-Control-Allow-Origin",
        "*"
    )

    handler.send_header(
        "Access-Control-Expose-Headers",
        "ETag, Location, Retry-After, X-RateLimit-Limit, X-RateLimit-Remaining"
    )

    if use_gzip:
        handler.send_header(
            "Content-Encoding",
            "gzip"
        )

    if headers:
        for key, value in headers.items():
            handler.send_header(key, value)

    handler.end_headers()

    if status != 304:
        handler.wfile.write(raw)


class OrdersHandler(BaseHTTPRequestHandler):

    server_version = "CampusEatsOrders/1.0"

    def log_message(self, fmt, *args):
        return

    # ---------------------------------------------------------
    # Common helpers
    # ---------------------------------------------------------

    def client_id(self):
        """
        Identify a client for rate limiting.
        Uses Authorization when available, otherwise IP.
        """

        auth = self.headers.get("Authorization")

        if auth:
            return auth

        return self.client_address[0]

    def rate_limit_check(self):
        """
        Per-client fixed-window rate limiter.
        """

        client = self.client_id()
        now = time.time()

        with rate_lock:

            entry = rate_state.get(client)

            if entry is None:
                entry = {
                    "start": now,
                    "count": 0,
                }
                rate_state[client] = entry

            if now - entry["start"] >= RATE_WINDOW:
                entry["start"] = now
                entry["count"] = 0

            entry["count"] += 1

            remaining = max(
                RATE_LIMIT - entry["count"],
                0
            )

            if entry["count"] > RATE_LIMIT:

                retry_after = int(
                    RATE_WINDOW -
                    (now - entry["start"])
                ) + 1

                json_response(
                    self,
                    429,
                    problem(
                        429,
                        "Too Many Requests",
                        "Rate limit exceeded.",
                    ),
                    {
                        "X-RateLimit-Limit": str(RATE_LIMIT),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(retry_after),
                    },
                )

                return False

            self._rate_remaining = remaining

        return True

    def send_rate_headers(self, headers=None):

        if headers is None:
            headers = {}

        headers["X-RateLimit-Limit"] = str(
            RATE_LIMIT
        )

        headers["X-RateLimit-Remaining"] = str(
            getattr(
                self,
                "_rate_remaining",
                RATE_LIMIT
            )
        )

        return headers

    def authorized(self):
        """
        Header-only authorization.
        No real authentication system is required.
        """

        auth = self.headers.get("Authorization")

        expected = f"Bearer {AUTH_TOKEN}"

        if not auth or auth != expected:

            json_response(
                self,
                401,
                problem(
                    401,
                    "Unauthorized",
                    "A valid Authorization: Bearer <token> header is required.",
                ),
                self.send_rate_headers(),
            )

            return False

        return True

    def accept_json(self):

        accept = self.headers.get("Accept")

        if not accept:
            return True

        accepted = [
            part.strip().lower()
            for part in accept.split(",")
        ]

        if (
            "*/*" in accepted
            or "application/json" in accepted
        ):
            return True

        json_response(
            self,
            406,
            problem(
                406,
                "Not Acceptable",
                "This service only returns application/json.",
            ),
            self.send_rate_headers(),
        )

        return False

    def read_json(self):

        content_type = self.headers.get(
            "Content-Type",
            ""
        ).lower()

        if not content_type.startswith(
            "application/json"
        ):

            json_response(
                self,
                400,
                problem(
                    400,
                    "Malformed request",
                    "Request body must use Content-Type: application/json.",
                ),
                self.send_rate_headers(),
            )

            return None

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            raw = self.rfile.read(length)

            return json.loads(
                raw.decode("utf-8")
            )

        except (
            ValueError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):

            return None

    def method_override(self):

        override = self.headers.get(
            "X-HTTP-Method-Override"
        )

        if override:
            return override.upper()

        return None

    # ---------------------------------------------------------
    # OPTIONS
    # ---------------------------------------------------------

    def do_OPTIONS(self):

        if not self.rate_limit_check():
            return

        parsed = urlparse(self.path)

        if (
            parsed.path == "/orders"
            or parsed.path.startswith("/orders/")
        ):

            headers = {
                "Allow": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods":
                    "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers":
                    "Content-Type, Accept, Authorization, "
                    "If-None-Match, If-Match, Idempotency-Key, "
                    "X-HTTP-Method-Override",
                "Access-Control-Max-Age": "600",
            }

            headers = self.send_rate_headers(
                headers
            )

            self.send_response(204)

            for key, value in headers.items():
                self.send_header(key, value)

            self.end_headers()

            return

        self.not_found()

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    def do_POST(self):

        if not self.rate_limit_check():
            return

        override = self.method_override()

        if override in {
            "PUT",
            "PATCH",
            "DELETE",
        }:
            self.handle_overridden_method(
                override
            )
            return

        parsed = urlparse(self.path)

        parts = [
            p for p in parsed.path.split("/")
            if p
        ]

        if parts == ["orders"]:

            if not self.accept_json():
                return

            self.create_order()
            return

        if (
            len(parts) == 3
            and parts[0] == "orders"
            and parts[2] == "cancellation"
        ):

            if not self.authorized():
                return

            self.cancel_order(parts[1])
            return

        self.not_found()

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def do_GET(self):

        if not self.rate_limit_check():
            return

        if not self.accept_json():
            return

        parsed = urlparse(self.path)

        parts = [
            p for p in parsed.path.split("/")
            if p
        ]

        if parts == ["orders"]:

            self.list_orders(
                parse_qs(parsed.query)
            )

            return

        if (
            len(parts) == 2
            and parts[0] == "orders"
        ):

            self.get_order(parts[1])
            return

        self.not_found()

    # ---------------------------------------------------------
    # PUT
    # ---------------------------------------------------------

    def do_PUT(self):

        if not self.rate_limit_check():
            return

        if not self.authorized():
            return

        self.update_order(replace=True)

    # ---------------------------------------------------------
    # PATCH
    # ---------------------------------------------------------

    def do_PATCH(self):

        if not self.rate_limit_check():
            return

        if not self.authorized():
            return

        self.update_order(replace=False)

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def do_DELETE(self):

        if not self.rate_limit_check():
            return

        if not self.authorized():
            return

        parsed = urlparse(self.path)

        parts = [
            p for p in parsed.path.split("/")
            if p
        ]

        if (
            len(parts) == 2
            and parts[0] == "orders"
        ):

            self.delete_order(parts[1])
            return

        self.not_found()

    # ---------------------------------------------------------
    # Method override
    # ---------------------------------------------------------

    def handle_overridden_method(self, method):

        if not self.authorized():
            return

        if method == "PUT":
            self.update_order(replace=True)
            return

        if method == "PATCH":
            self.update_order(replace=False)
            return

        if method == "DELETE":
            self.delete_order_from_path()
            return

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    def create_order(self):

        key = self.headers.get(
            "Idempotency-Key"
        )

        if not key:

            json_response(
                self,
                400,
                problem(
                    400,
                    "Malformed request",
                    "Idempotency-Key header is required for order creation.",
                ),
                self.send_rate_headers(),
            )

            return

        # Same key = same result.
        with idempotency_lock:
            existing_id = idempotency_results.get(key)

        if existing_id:

            existing = store.get(existing_id)

            if existing:

                json_response(
                    self,
                    201,
                    existing.as_json(),
                    self.send_rate_headers({
                        "Location":
                            f"/orders/{existing.order_id}",
                        "ETag":
                            make_etag(existing),
                    }),
                )

                return

        existing = store.get_idempotent_order(key)

        if existing:

            json_response(
                self,
                201,
                existing.as_json(),
                self.send_rate_headers({
                    "Location":
                        f"/orders/{existing.order_id}",
                    "ETag":
                        make_etag(existing),
                }),
            )

            return

        payload = self.read_json()

        if payload is None:

            json_response(
                self,
                400,
                problem(
                    400,
                    "Malformed request",
                    "Request body contains invalid JSON.",
                ),
                self.send_rate_headers(),
            )

            return

        valid, detail = validate(payload)

        if not valid:

            json_response(
                self,
                400,
                problem(
                    400,
                    "Malformed request",
                    detail,
                ),
                self.send_rate_headers(),
            )

            return

        if payload["total_amount"] > 50000:

            json_response(
                self,
                422,
                problem(
                    422,
                    "Order refused",
                    "Orders above INR 50,000 require manual approval.",
                    "https://campuseats.example/errors/order-limit",
                ),
                self.send_rate_headers(),
            )

            return

        order = Order(
            internal_id=store.next_id(),
            order_id=
                f"CE-ORD-{uuid.uuid4().hex[:8].upper()}",
            customer_name=
                payload["customer_name"].strip(),
            customer_email=
                payload["customer_email"].strip(),
            items=payload["items"],
            total_amount=
                float(payload["total_amount"]),
            currency=
                payload["currency"].upper(),
        )

        try:

            payment = call_payments(
                order,
                key
            )

        except HTTPError:

            json_response(
                self,
                422,
                problem(
                    422,
                    "Payment refused",
                    "The Payments service refused the payment request.",
                    "https://campuseats.example/errors/payment-refused",
                ),
                self.send_rate_headers(),
            )

            return

        except RuntimeError:

            json_response(
                self,
                503,
                problem(
                    503,
                    "Payment service unavailable",
                    "The order was not created because payment confirmation could not be obtained.",
                    "https://campuseats.example/errors/payment-unavailable",
                ),
                self.send_rate_headers(),
            )

            return

        order.status = "CONFIRMED"
        order.payment_reference = payment.get(
            "transaction_id"
        )

        store.save(order)

        store.remember_idempotency(
            key,
            order.order_id
        )

        with idempotency_lock:
            idempotency_results[key] = order.order_id

        json_response(
            self,
            201,
            order.as_json(),
            self.send_rate_headers({
                "Location":
                    f"/orders/{order.order_id}",
                "ETag":
                    make_etag(order),
            }),
        )

    # ---------------------------------------------------------
    # GET single order
    # ---------------------------------------------------------

    def get_order(self, order_id):

        order = store.get(order_id)

        if not order:

            json_response(
                self,
                404,
                problem(
                    404,
                    "Order not found",
                    f"No order exists with id '{order_id}'.",
                    "https://campuseats.example/errors/not-found",
                ),
                self.send_rate_headers(),
            )

            return

        etag = make_etag(order)

        if_none_match = self.headers.get(
            "If-None-Match"
        )

        headers = self.send_rate_headers({
            "ETag": etag,
            "Cache-Control":
                "private, max-age=30",
        })

        if (
            if_none_match
            and if_none_match == etag
        ):

            self.send_response(304)

            for key, value in headers.items():
                self.send_header(key, value)

            self.end_headers()

            return

        json_response(
            self,
            200,
            order.as_json(),
            headers,
        )

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    def list_orders(self, query):

        status = query.get(
            "status",
            [None]
        )[0]

        allowed = {
            "PENDING",
            "CONFIRMED",
            "CANCELLED",
        }

        if (
            status
            and status.upper() not in allowed
        ):

            json_response(
                self,
                400,
                problem(
                    400,
                    "Malformed query",
                    "status must be one of PENDING, CONFIRMED, or CANCELLED.",
                ),
                self.send_rate_headers(),
            )

            return

        orders = store.list(
            status.upper()
            if status
            else None
        )

        json_response(
            self,
            200,
            {
                "orders": [
                    o.as_json()
                    for o in orders
                ]
            },
            self.send_rate_headers({
                "Cache-Control":
                    "no-store",
            }),
        )

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update_order(self, replace=False):

        parsed = urlparse(self.path)

        parts = [
            p for p in parsed.path.split("/")
            if p
        ]

        if (
            len(parts) != 2
            or parts[0] != "orders"
        ):

            self.not_found()
            return

        order_id = parts[1]

        order = store.get(order_id)

        if not order:

            json_response(
                self,
                404,
                problem(
                    404,
                    "Order not found",
                    f"No order exists with id '{order_id}'.",
                ),
                self.send_rate_headers(),
            )

            return

        current_etag = make_etag(order)

        supplied_etag = self.headers.get(
            "If-Match"
        )

        if (
            not supplied_etag
            or supplied_etag != current_etag
        ):

            json_response(
                self,
                412,
                problem(
                    412,
                    "Precondition Failed",
                    "If-Match does not match the current ETag.",
                ),
                self.send_rate_headers({
                    "ETag":
                        current_etag,
                }),
            )

            return

        payload = self.read_json()

        if payload is None:

            json_response(
                self,
                400,
                problem(
                    400,
                    "Malformed request",
                    "Request body contains invalid JSON.",
                ),
                self.send_rate_headers(),
            )

            return

        if replace:

            valid, detail = validate(payload)

            if not valid:

                json_response(
                    self,
                    400,
                    problem(
                        400,
                        "Malformed request",
                        detail,
                    ),
                    self.send_rate_headers(),
                )

                return

            order.customer_name = (
                payload["customer_name"].strip()
            )

            order.customer_email = (
                payload["customer_email"].strip()
            )

            order.items = payload["items"]

            order.total_amount = float(
                payload["total_amount"]
            )

            order.currency = (
                payload["currency"].upper()
            )

        else:

            if "customer_name" in payload:

                if (
                    not isinstance(
                        payload["customer_name"],
                        str
                    )
                    or not payload["customer_name"].strip()
                ):

                    json_response(
                        self,
                        400,
                        problem(
                            400,
                            "Malformed request",
                            "customer_name must be a non-empty string.",
                        ),
                        self.send_rate_headers(),
                    )

                    return

                order.customer_name = (
                    payload["customer_name"].strip()
                )

            if "customer_email" in payload:

                if (
                    not isinstance(
                        payload["customer_email"],
                        str
                    )
                    or "@"
                    not in payload["customer_email"]
                ):

                    json_response(
                        self,
                        400,
                        problem(
                            400,
                            "Malformed request",
                            "customer_email must be a valid email-like string.",
                        ),
                        self.send_rate_headers(),
                    )

                    return

                order.customer_email = (
                    payload["customer_email"].strip()
                )

            if "items" in payload:

                if (
                    not isinstance(
                        payload["items"],
                        list
                    )
                    or not payload["items"]
                ):

                    json_response(
                        self,
                        400,
                        problem(
                            400,
                            "Malformed request",
                            "items must be a non-empty array.",
                        ),
                        self.send_rate_headers(),
                    )

                    return

                order.items = payload["items"]

            if "total_amount" in payload:

                if (
                    not isinstance(
                        payload["total_amount"],
                        (int, float)
                    )
                    or isinstance(
                        payload["total_amount"],
                        bool
                    )
                    or payload["total_amount"] <= 0
                ):

                    json_response(
                        self,
                        400,
                        problem(
                            400,
                            "Malformed request",
                            "total_amount must be a positive number.",
                        ),
                        self.send_rate_headers(),
                    )

                    return

                order.total_amount = float(
                    payload["total_amount"]
                )

            if "currency" in payload:

                if (
                    not isinstance(
                        payload["currency"],
                        str
                    )
                    or len(payload["currency"]) != 3
                ):

                    json_response(
                        self,
                        400,
                        problem(
                            400,
                            "Malformed request",
                            "currency must be a three-letter code.",
                        ),
                        self.send_rate_headers(),
                    )

                    return

                order.currency = (
                    payload["currency"].upper()
                )

        new_etag = make_etag(order)

        json_response(
            self,
            200,
            order.as_json(),
            self.send_rate_headers({
                "ETag": new_etag,
                "Cache-Control":
                    "no-store",
            }),
        )

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_order_from_path(self):

        parsed = urlparse(self.path)

        parts = [
            p for p in parsed.path.split("/")
            if p
        ]

        if (
            len(parts) == 2
            and parts[0] == "orders"
        ):

            self.delete_order(parts[1])
            return

        self.not_found()

    def delete_order(self, order_id):

        order = store.get(order_id)

        if not order:

            json_response(
                self,
                404,
                problem(
                    404,
                    "Order not found",
                    f"No order exists with id '{order_id}'.",
                ),
                self.send_rate_headers(),
            )

            return

        current_etag = make_etag(order)

        supplied_etag = self.headers.get(
            "If-Match"
        )

        if (
            supplied_etag
            and supplied_etag != current_etag
        ):

            json_response(
                self,
                412,
                problem(
                    412,
                    "Precondition Failed",
                    "If-Match does not match the current ETag.",
                ),
                self.send_rate_headers({
                    "ETag": current_etag,
                }),
            )

            return

        # OrderStore from Assignment 4 does not necessarily
        # expose delete(), so remove by marking cancelled.
        order.status = "CANCELLED"

        self.send_response(204)

        headers = self.send_rate_headers({
            "Cache-Control":
                "no-store",
        })

        for key, value in headers.items():
            self.send_header(key, value)

        self.end_headers()

    # ---------------------------------------------------------
    # CANCEL
    # ---------------------------------------------------------

    def cancel_order(self, order_id):

        order = store.get(order_id)

        if not order:

            json_response(
                self,
                404,
                problem(
                    404,
                    "Order not found",
                    f"No order exists with id '{order_id}'.",
                    "https://campuseats.example/errors/not-found",
                ),
                self.send_rate_headers(),
            )

            return

        if order.status == "CANCELLED":

            json_response(
                self,
                409,
                problem(
                    409,
                    "State conflict",
                    "The order has already been cancelled.",
                    "https://campuseats.example/errors/state-conflict",
                ),
                self.send_rate_headers(),
            )

            return

        if order.status not in {
            "PENDING",
            "CONFIRMED",
        }:

            json_response(
                self,
                409,
                problem(
                    409,
                    "State conflict",
                    f"Order in state {order.status} cannot be cancelled.",
                    "https://campuseats.example/errors/state-conflict",
                ),
                self.send_rate_headers(),
            )

            return

        order.status = "CANCELLED"

        json_response(
            self,
            200,
            order.as_json(),
            self.send_rate_headers({
                "ETag":
                    make_etag(order),
                "Cache-Control":
                    "no-store",
            }),
        )

    # ---------------------------------------------------------
    # 404
    # ---------------------------------------------------------

    def not_found(self):

        json_response(
            self,
            404,
            problem(
                404,
                "Resource not found",
                "The requested URL does not exist.",
                "https://campuseats.example/errors/not-found",
            ),
            self.send_rate_headers(),
        )


def create_server(
    host="127.0.0.1",
    port=5000
):

    return ThreadingHTTPServer(
        (host, port),
        OrdersHandler
    )


if __name__ == "__main__":

    server = create_server(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
    )

    print(
        "CampusEats Orders service listening on "
        f"http://0.0.0.0:{server.server_port}"
    )

    server.serve_forever()