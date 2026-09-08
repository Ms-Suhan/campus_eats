# CS543 Web Services — Assignment 4
## Rebuilding a CampusEats service in REST

**Chosen service:** Orders  
**Team:**
- M S Suhan — 20252651036
- Gaurav Vyas — 20252651020
- Shubham Parmar — 20252651054
- Manish Sexena — 20252650133
- Kunal Roy — 20252651031

> **Source note:** Assignment 2 was not included in the supplied files, so this submission keeps the CampusEats **Orders** boundary as the working assumption rather than claiming to reproduce an unseen Assignment 2 design. The supplied Assignment 3 materials establish the payment integration and the PaySecure fault vocabulary used in the comparison below.

## Part A — Model the service

### A2. Operations that could have been written as SOAP

The starting operations are expressed in the style requested by the brief:

1. `createOrder(...)`
2. `getOrder(...)`
3. `getOrdersByStatus(...)`
4. `cancelOrder(...)`

These verbs are deliberately removed from the REST URLs in favour of the durable resource **orders**.

### A4. Resource table

| Method | URL | What it does | Success code | Failure codes |
|---|---|---|---:|---|
| POST | `/orders` | Creates an order and confirms payment through the Payments service | 201 | 400, 422, 503 |
| GET | `/orders/{order_id}` | Reads one durable order resource | 200 | 404 |
| GET | `/orders?status=CONFIRMED` | Returns a filtered collection of orders | 200 | 400 |
| POST | `/orders/{order_id}/cancellation` | Changes an order's state to CANCELLED | 200 | 404, 409 |

### A5. Hard choice

`cancelOrder(...)` was the least comfortable operation to map directly to a REST resource because cancellation looks like an action rather than a durable noun. I rejected `/orders/{id}/cancel` because the assignment explicitly asks that verbs such as `add`, `set`, or `get` do not survive into URLs. I modelled cancellation as the state-changing sub-resource `/orders/{order_id}/cancellation`; the durable thing being created is the cancellation record/event associated with the order, while the order itself moves to `CANCELLED`. This preserves a resource-oriented URL while still making the state transition explicit.

## Part B — OpenAPI contract

`openapi.yaml` was written before the handler implementation. It defines the four required endpoints, reusable schemas under `components.schemas`, parameters, request bodies, success responses, and documented failure responses.

Validation command:

```bash
python -m openapi_spec_validator openapi.yaml
```

Expected result for the submitted file:

```text
openapi.yaml: validation successful (0 errors)
```

If the validator package is not installed, install it with `pip install openapi-spec-validator` before running the command.

## Part C — Implementation

The service follows the requested Tutorial 4 layout:

```text
CampusEats-Orders/
├── openapi.yaml
├── app.py
├── models.py
├── store.py
├── errors.py
├── requirements.txt
├── NOTES.md
└── tests/
    └── test_app.py
```

### C2. Record vs representation

`models.py` stores an internal `Order` record containing `internal_id`, `customer_email`, and `payment_reference` in addition to the public order fields. `Order.as_json()` deliberately publishes only the API representation. Thus the internal identifier, customer email, and payment-provider reference do not leak into the response.

### C4. Manual request validation

The function carrying the responsibility formerly provided by the Assignment 3 XML Schema is:

```text
validate(payload)
```

It is called before any request-body field is accessed. Without it, a request such as `{"customer_name":"Only a name"}` could reach code that assumes `items`, `total_amount`, or `currency` exists, producing an unintended server error instead of the required 400 response.

### C5/C6. Status codes and one error shape

All failures use the single `problem()` helper in `errors.py`, producing exactly:

```json
{
  "type": "about:blank",
  "title": "...",
  "status": 400,
  "detail": "..."
}
```

The implementation uses 201 + `Location` for creation, 200 for reads, 400 for malformed requests, 404 for missing resources, 409 for state conflicts, 422 for valid domain/payment refusals, and 503 when the payment dependency cannot be reached.

### C7. Idempotent create

`POST /orders` requires `Idempotency-Key`. The key is stored with the created order. A repeated request with the same key returns the original order and its original `Location` rather than creating or charging again.

## Part D — Network resilience

### D1. Outbound service

The Orders service makes an HTTP `POST` call to the CampusEats Payments service. Its address is read from:

```text
PAYMENTS_SERVICE_URL
```

No payment-service URL is hard-coded in the service logic. The default is only a local development value and can be replaced by the environment in which the services run.

### D2. Timeout, retry, backoff and jitter

The Payments call uses a bounded timeout. Network failures and 5xx responses can be retried up to three times using exponential backoff plus random jitter. 4xx responses are not retried. Because the outbound operation is a create/charge-like operation, the same `Idempotency-Key` is sent on every retry.

### D3. Fallback decision

The service **fails closed** when Payments is unreachable and returns HTTP 503. Degrading by creating an apparently confirmed order without payment confirmation would leave CampusEats with an order that may never have been paid, creating a financial and state-consistency problem. Therefore the safer fallback is to refuse creation until payment confirmation can be obtained.

## Required comparison with Assignment 3

### 1. WSDL lines vs OpenAPI lines

The supplied Assignment 3 `partner.wsdl` contains 124 physical lines including comments and blank lines, while this `openapi.yaml` contains a much smaller resource-oriented contract. The difference is mainly structural: WSDL explicitly describes XML namespaces/types, messages, the abstract port type, SOAP binding, SOAP action and service/port endpoint. OpenAPI can describe HTTP paths, methods, parameters, request/response schemas and status codes directly without reproducing SOAP's message/binding layers.

Two things the WSDL declared that this OpenAPI contract does not need are:

1. The SOAP `binding` and `soap:operation`/`SOAPAction` declaration.
2. Separate WSDL `message`, `portType`, `service`, and `port` constructs for wrapping an operation over SOAP.

The Assignment 3 WSDL explicitly defined a document-style SOAP-over-HTTP binding and the Charge SOAP action. Those constructs are not needed for the REST resource contract.

### 2. SOAP Fault mapping

Assignment 3's supplied `soap-fault.xml` contains the SOAP fault with `faultcode` `soapenv:Server`, `faultstring` `Charge could not be completed`, and a structured `PaySecureFault` whose `ErrorCode` is `card_declined` and whose message says that the card issuer declined the transaction. The supplied Assignment 3 report says CampusEats maps this partner-specific error to its own domain error `PAYMENT_DECLINED` rather than exposing the PaySecure vocabulary.

The REST replacement is an HTTP error response such as:

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/json
```

```json
{
  "type": "https://campuseats.example/errors/payment-refused",
  "title": "Payment refused",
  "status": 422,
  "detail": "The Payments service refused the payment request."
}
```

Returning a payment failure inside a `200 OK` response is a problem because intermediaries, clients, monitoring systems, caches, load balancers, and generic HTTP tooling interpret 200 as successful transport/application completion. A proper 4xx status makes failure visible to the network and allows standard retry/alert/handling policies to distinguish success from failure.

### 3. UDDI: publish, find, bind

The Assignment 3 report described a modern service catalogue as the discovery mechanism for PaySecure: the catalogue provided the service name, endpoint and pointer to the WSDL, after which CampusEats obtained the contract and used it to determine operations, message formats, binding, SOAPAction and endpoint.

In the REST setup, **find** still exists as service discovery/configuration: the Payments service address is supplied through `PAYMENTS_SERVICE_URL` rather than embedded in application logic. **Bind** still exists in a simpler HTTP sense: the Orders service binds to the discovered base URL and sends an HTTP request conforming to the API contract. The explicit UDDI **publish** operation disappears as a protocol-level requirement; deployment/configuration and an organisational service catalogue take over publication and endpoint discovery.

### 4. XML Schema vs `validate()`

The specific function replacing the validation responsibility of Assignment 3's XML Schema is:

```text
validate(payload)
```

It checks required fields and basic types/constraints before the handler reads the body fields. Without it, a body such as:

```json
{"customer_name":"Suhan"}
```

could pass into the handler and fail later when code tries to use missing `items`, `total_amount`, or `currency`, producing an unintended error instead of a controlled 400 response.

### 5. Where SOAP would still be preferable

I would still choose the SOAP stack for the **external payment-gateway integration** when the partner requires a formal WSDL contract, message-level credentials, XML Schema validation and structured SOAP faults. The guarantee being purchased is a strongly specified message contract and interoperability model in which the exact request/response/fault structures, binding and operation are formally described before runtime. This is consistent with the Assignment 3 PaySecure integration, where the WSDL defined `ChargeRequest`, `ChargeResponse`, `PaySecureFault`, the SOAP binding and the `Charge` action.

For the internal CampusEats Orders service, REST is preferable because the service is resource-oriented and benefits directly from HTTP methods, status codes, query filtering and resource URLs.

## Conclusion

The REST version moves the Orders service from operation-oriented thinking to resource-oriented design. The main contract is expressed through `/orders` resources and HTTP semantics rather than SOAP envelopes and WSDL message/binding constructs. Idempotency protects order creation from duplicate requests, while the Payments call uses timeout, exponential backoff and jitter and fails closed when the dependency is unavailable.

