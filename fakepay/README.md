# FakePay (Paylov Merchant API Clone)

This service is a classroom-grade clone of Paylov's Merchant API flow:
- payment link generation via base64 query
- hosted checkout page
- merchant callback calls with JSON-RPC:
  - `transaction.check`
  - `transaction.perform`
- Basic Auth on callbacks
- Paylov-like statuses (`0`, `3`, `5`, `303`, `+1`)

Official docs used for parity:
- https://developer.paylov.uz/merchants/paylov-payment-gateway
- https://developer.paylov.uz/merchants/creating-payment-link
- https://developer.paylov.uz/merchants/transaction-check
- https://developer.paylov.uz/merchants/transaction-perform
- https://developer.paylov.uz/merchants/statuses

## Run

```bash
cd fakepay
uv run uvicorn main:app --reload --port 8001
```

Health check:

```bash
curl http://localhost:8001/health
```

## DB schema (`fakepay.db`)

Tables:
- `merchants`: callback/auth config for merchant systems
- `payment_sessions`: checkout session + transaction info + status
- `callback_logs`: each callback attempt payload/response

A demo merchant is seeded automatically:
- `merchant_id`: `571c06fb-6c61-4ef7-8567-5511abaf12b5`
- `login`: `uic_demo`

## 1) Register merchant (admin/demo endpoint)

```bash
curl -X POST http://localhost:8001/admin/merchants \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "My LMS",
    "login": "lms_merchant",
    "password": "merchant_secret",
    "callback_url": "http://localhost:8000/payment/callback",
    "callback_auth_username": "cb_user",
    "callback_auth_password": "cb_pass"
  }'
```

## 2) Generate Paylov-style checkout link

Paylov format:
`/checkout/create/{base64(query_string)}`

Query fields:
- `merchant_id` (required)
- `amount` (required)
- `return_url` (optional)
- `currency_id` (optional, `860` UZS default, or `840` USD)
- `amount_in_tiyin` (optional, default `False`)
- `account.*` (optional merchant-specific fields, e.g. `account.order_id`)

Python helper:

```python
import base64
import urllib.parse

base = "http://localhost:8001/checkout/create/"
params = {
    "merchant_id": "571c06fb-6c61-4ef7-8567-5511abaf12b5",
    "amount": "500",
    "currency_id": "860",
    "return_url": "http://localhost:3000/payment-result",
    "account.order_id": "ORD-1001",
}
encoded = base64.b64encode(urllib.parse.urlencode(params).encode()).decode()
print(base + encoded)
```

Open produced URL in browser. On payment confirmation, FakePay will call merchant callback.

## 3) Callback contract (merchant side)

FakePay sends JSON-RPC POST requests with Basic Auth:

### `transaction.check`

```json
{
  "jsonrpc": "2.0",
  "id": 1234567,
  "method": "transaction.check",
  "params": {
    "account": {"order_id": "ORD-1001"},
    "amount": 500,
    "amount_tiyin": 50000,
    "currency": 860
  }
}
```

### `transaction.perform`

```json
{
  "jsonrpc": "2.0",
  "id": 1234568,
  "method": "transaction.perform",
  "params": {
    "transaction_id": "UUID",
    "account": {"order_id": "ORD-1001"},
    "amount": 500,
    "amount_tiyin": 50000,
    "currency": 860
  }
}
```

### Merchant response format

```json
{
  "jsonrpc": "2.0",
  "id": 1234567,
  "result": {
    "status": "0",
    "statusText": "OK"
  }
}
```

Supported statuses:
- `0` success
- `3` maintenance
- `5` invalid amount
- `303` order not found
- `+1` custom business error (e.g. `monthly_limit_exceeded`)

## 4) Inspect transaction and callback logs

```bash
curl http://localhost:8001/admin/payment-sessions/<session_id>
```

Response includes session state and all callback attempts.

## Legacy compatibility endpoint

For existing toy integrations, `/checkout` is still available and returns a Paylov-style checkout URL.
