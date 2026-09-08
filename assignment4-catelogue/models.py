from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Order:
    """Internal order record. Internal fields are intentionally not published."""
    internal_id: int
    order_id: str
    customer_name: str
    customer_email: str
    items: List[Dict[str, Any]]
    total_amount: float
    currency: str
    status: str = "PENDING"
    payment_reference: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_json(self) -> Dict[str, Any]:
        """Public representation; internal_id and customer_email are not exposed."""
        return {
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "items": self.items,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at,
        }
