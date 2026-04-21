import base64
import json
import os
import sqlite3
import urllib.parse
import uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
DB_FILE = Path(os.getenv("FAKEPAY_DB_FILE", APP_DIR / "fakepay.db"))

STATUS_SUCCESS = "0"
STATUS_MAINTENANCE = "3"
STATUS_INVALID_AMOUNT = "5"
STATUS_ORDER_NOT_FOUND = "303"
STATUS_CUSTOM = "+1"

CURRENCY_UZS = 860
CURRENCY_USD = 840
SUPPORTED_CURRENCIES = {CURRENCY_UZS, CURRENCY_USD}

app = FastAPI(title="FakePay Merchant API Clone")


class MerchantCreateRequest(BaseModel):
    merchant_id: str | None = None
    name: str = Field(min_length=1)
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)
    callback_url: str = Field(min_length=1)
    callback_auth_username: str = Field(min_length=1)
    callback_auth_password: str = Field(min_length=1)
    is_active: bool = True


class LegacyCheckoutRequest(BaseModel):
    merchant_id: str
    amount: Decimal
    currency_id: int = CURRENCY_UZS
    return_url: str | None = None
    account: dict[str, Any] = Field(default_factory=dict)
    amount_in_tiyin: bool = False


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS merchants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            callback_url TEXT NOT NULL,
            callback_auth_username TEXT NOT NULL,
            callback_auth_password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_sessions (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL UNIQUE,
            merchant_id TEXT NOT NULL,
            account_json TEXT NOT NULL,
            amount TEXT NOT NULL,
            amount_tiyin INTEGER NOT NULL,
            currency_id INTEGER NOT NULL,
            amount_in_tiyin INTEGER NOT NULL,
            return_url TEXT,
            encoded_query TEXT NOT NULL,
            status TEXT NOT NULL,
            status_code TEXT,
            status_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (merchant_id) REFERENCES merchants(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS callback_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_session_id TEXT NOT NULL,
            method TEXT NOT NULL,
            request_json TEXT NOT NULL,
            response_status INTEGER,
            response_body TEXT,
            success INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (payment_session_id) REFERENCES payment_sessions(id)
        )
        """
    )

    _migrate_legacy_schema(conn)
    _ensure_callback_logs_fk(conn)
    _seed_demo_merchant(conn)

    conn.commit()
    conn.close()


def _column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _migrate_legacy_schema(conn: sqlite3.Connection) -> None:
    # Old toy schema had only: id, amount, currency, status, callback_url.
    # If detected, migrate to new table shape and preserve old rows best-effort.
    if not _table_exists(conn, "payment_sessions"):
        return

    if _column_exists(conn, "payment_sessions", "transaction_id"):
        return

    conn.execute("ALTER TABLE payment_sessions RENAME TO payment_sessions_old")
    conn.execute(
        """
        CREATE TABLE payment_sessions (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL UNIQUE,
            merchant_id TEXT NOT NULL,
            account_json TEXT NOT NULL,
            amount TEXT NOT NULL,
            amount_tiyin INTEGER NOT NULL,
            currency_id INTEGER NOT NULL,
            amount_in_tiyin INTEGER NOT NULL,
            return_url TEXT,
            encoded_query TEXT NOT NULL,
            status TEXT NOT NULL,
            status_code TEXT,
            status_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (merchant_id) REFERENCES merchants(id)
        )
        """
    )

    default_merchant_id = _ensure_legacy_merchant(conn)
    old_rows = conn.execute("SELECT id, amount, currency, status, callback_url FROM payment_sessions_old").fetchall()

    for row in old_rows:
        amount_decimal = Decimal(str(row[1]))
        currency_id = CURRENCY_UZS if str(row[2]).upper() == "UZS" else CURRENCY_USD
        amount_tiyin = int((amount_decimal * Decimal("100")).quantize(Decimal("1")))
        created = now_iso()
        conn.execute(
            """
            INSERT INTO payment_sessions (
                id, transaction_id, merchant_id, account_json, amount, amount_tiyin,
                currency_id, amount_in_tiyin, return_url, encoded_query, status,
                status_code, status_text, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row[0],
                str(uuid.uuid4()),
                default_merchant_id,
                "{}",
                str(amount_decimal),
                amount_tiyin,
                currency_id,
                0,
                row[4],
                "",
                row[3],
                None,
                None,
                created,
                created,
            ),
        )

    conn.execute("DROP TABLE payment_sessions_old")


def _ensure_callback_logs_fk(conn: sqlite3.Connection) -> None:
    # SQLite table rename may rewrite FK target to payment_sessions_old.
    # Recreate callback_logs with the correct FK target.
    schema_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='callback_logs'",
    ).fetchone()
    if not schema_row:
        return

    schema_sql = (schema_row[0] or "").lower()
    if "payment_sessions_old" not in schema_sql:
        return

    existing_logs = conn.execute(
        """
        SELECT id, payment_session_id, method, request_json, response_status, response_body, success, created_at
        FROM callback_logs
        ORDER BY id ASC
        """
    ).fetchall()

    conn.execute("DROP TABLE callback_logs")
    conn.execute(
        """
        CREATE TABLE callback_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_session_id TEXT NOT NULL,
            method TEXT NOT NULL,
            request_json TEXT NOT NULL,
            response_status INTEGER,
            response_body TEXT,
            success INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (payment_session_id) REFERENCES payment_sessions(id)
        )
        """
    )

    existing_session_ids = {
        row[0]
        for row in conn.execute("SELECT id FROM payment_sessions").fetchall()
    }
    for log in existing_logs:
        if log["payment_session_id"] not in existing_session_ids:
            continue
        conn.execute(
            """
            INSERT INTO callback_logs (
                id, payment_session_id, method, request_json, response_status, response_body, success, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log["id"],
                log["payment_session_id"],
                log["method"],
                log["request_json"],
                log["response_status"],
                log["response_body"],
                log["success"],
                log["created_at"],
            ),
        )


def _ensure_legacy_merchant(conn: sqlite3.Connection) -> str:
    merchant_id = "00000000-0000-0000-0000-000000000001"
    row = conn.execute("SELECT id FROM merchants WHERE id = ?", (merchant_id,)).fetchone()
    if row:
        return merchant_id

    created = now_iso()
    conn.execute(
        """
        INSERT INTO merchants (
            id, name, login, password, callback_url,
            callback_auth_username, callback_auth_password,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            merchant_id,
            "Legacy Merchant",
            "legacy",
            "legacy",
            "http://localhost:8000/api/v1/payments/callback/",
            "legacy",
            "legacy",
            1,
            created,
            created,
        ),
    )
    return merchant_id


def _seed_demo_merchant(conn: sqlite3.Connection) -> None:
    merchant_id = "571c06fb-6c61-4ef7-8567-5511abaf12b5"
    row = conn.execute("SELECT id FROM merchants WHERE id = ?", (merchant_id,)).fetchone()
    if row:
        return

    created = now_iso()
    conn.execute(
        """
        INSERT INTO merchants (
            id, name, login, password, callback_url,
            callback_auth_username, callback_auth_password,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            merchant_id,
            "UIC Demo Merchant",
            "uic_demo",
            "uic_demo_pass",
            "http://localhost:8000/api/v1/payments/callback/",
            "uic_callback",
            "uic_callback_pass",
            1,
            created,
            created,
        ),
    )


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/admin/merchants")
def create_merchant(payload: MerchantCreateRequest) -> dict[str, Any]:
    merchant_id = payload.merchant_id or str(uuid.uuid4())

    try:
        uuid.UUID(merchant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="merchant_id must be UUID4/UUID") from exc

    created = now_iso()

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO merchants (
                id, name, login, password, callback_url,
                callback_auth_username, callback_auth_password,
                is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                merchant_id,
                payload.name,
                payload.login,
                payload.password,
                payload.callback_url,
                payload.callback_auth_username,
                payload.callback_auth_password,
                1 if payload.is_active else 0,
                created,
                created,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="merchant id or login already exists") from exc
    finally:
        conn.close()

    return {"merchant_id": merchant_id}


@app.get("/admin/merchants")
def list_merchants() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, name, login, callback_url, callback_auth_username, is_active, created_at
        FROM merchants
        ORDER BY created_at DESC
        """
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/admin/payment-sessions/{session_id}")
def get_payment_session(session_id: str) -> dict[str, Any]:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, transaction_id, merchant_id, account_json, amount, amount_tiyin, currency_id,
               amount_in_tiyin, return_url, status, status_code, status_text, created_at, updated_at
        FROM payment_sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="payment session not found")

    logs = conn.execute(
        """
        SELECT method, request_json, response_status, response_body, success, created_at
        FROM callback_logs
        WHERE payment_session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    ).fetchall()
    conn.close()

    data = dict(row)
    data["account"] = json.loads(data.pop("account_json"))
    data["callback_logs"] = [dict(log) for log in logs]
    return data


@app.post("/checkout")
def legacy_checkout(data: LegacyCheckoutRequest) -> dict[str, str]:
    query_params: dict[str, Any] = {
        "merchant_id": data.merchant_id,
        "amount": str(data.amount),
        "currency_id": str(data.currency_id),
    }
    if data.return_url:
        query_params["return_url"] = data.return_url
    if data.amount_in_tiyin:
        query_params["amount_in_tiyin"] = "True"

    for key, value in data.account.items():
        query_params[f"account.{key}"] = str(value)

    query = urllib.parse.urlencode(query_params)
    encoded = base64.b64encode(query.encode()).decode()
    return {
        "checkout_url": f"http://localhost:8001/checkout/create/{encoded}",
        "encoded_query": encoded,
    }


@app.get("/checkout/create/{encoded_params}")
def create_checkout_from_link(encoded_params: str):
    parsed = _decode_checkout_params(encoded_params)

    merchant = _get_active_merchant(parsed["merchant_id"])
    amount, amount_tiyin = _normalize_amount(
        parsed["amount"],
        parsed["currency_id"],
        parsed["amount_in_tiyin"],
    )

    session_id = str(uuid.uuid4())
    transaction_id = str(uuid.uuid4())
    created = now_iso()

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO payment_sessions (
            id, transaction_id, merchant_id, account_json, amount, amount_tiyin,
            currency_id, amount_in_tiyin, return_url, encoded_query, status,
            status_code, status_text, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            transaction_id,
            merchant["id"],
            json.dumps(parsed["account"]),
            str(amount),
            amount_tiyin,
            parsed["currency_id"],
            1 if parsed["amount_in_tiyin"] else 0,
            parsed["return_url"],
            encoded_params,
            "PENDING",
            None,
            None,
            created,
            created,
        ),
    )
    conn.commit()
    conn.close()

    return HTMLResponse(content=_render_checkout_page(session_id, transaction_id, amount, parsed["currency_id"]))


@app.post("/checkout/{session_id}/confirm")
def confirm_payment(session_id: str):
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, transaction_id, merchant_id, account_json, amount, amount_tiyin,
               currency_id, return_url, status
        FROM payment_sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="payment session not found")

    if row["status"] != "PENDING":
        conn.close()
        return HTMLResponse(content=f"<h2>Payment already processed: {row['status']}</h2>", status_code=200)

    merchant = conn.execute(
        """
        SELECT id, callback_url, callback_auth_username, callback_auth_password
        FROM merchants
        WHERE id = ? AND is_active = 1
        """,
        (row["merchant_id"],),
    ).fetchone()

    if not merchant:
        _mark_session_status(conn, session_id, "FAILED", STATUS_MAINTENANCE, "Merchant unavailable")
        conn.commit()
        conn.close()
        return _redirect_or_message(row["return_url"], STATUS_MAINTENANCE, "Merchant unavailable", row["transaction_id"])

    account = json.loads(row["account_json"])
    amount_decimal = Decimal(row["amount"])
    amount_number = _amount_for_payload(amount_decimal)

    check_payload = {
        "jsonrpc": "2.0",
        "id": int(uuid.uuid4().int % 10_000_000),
        "method": "transaction.check",
        "params": {
            "account": account,
            "amount": amount_number,
            "amount_tiyin": row["amount_tiyin"],
            "currency": row["currency_id"],
        },
    }

    check_result = _call_merchant(
        conn=conn,
        session_id=session_id,
        merchant=dict(merchant),
        method_name="transaction.check",
        payload=check_payload,
    )

    if check_result["status"] != STATUS_SUCCESS:
        _mark_session_status(conn, session_id, "FAILED", check_result["status"], check_result["statusText"])
        conn.commit()
        conn.close()
        return _redirect_or_message(
            row["return_url"],
            check_result["status"],
            check_result["statusText"],
            row["transaction_id"],
        )

    perform_payload = {
        "jsonrpc": "2.0",
        "id": int(uuid.uuid4().int % 10_000_000),
        "method": "transaction.perform",
        "params": {
            "transaction_id": row["transaction_id"],
            "account": account,
            "amount": amount_number,
            "amount_tiyin": row["amount_tiyin"],
            "currency": row["currency_id"],
        },
    }

    perform_result = _call_merchant(
        conn=conn,
        session_id=session_id,
        merchant=dict(merchant),
        method_name="transaction.perform",
        payload=perform_payload,
    )

    if perform_result["status"] == STATUS_SUCCESS:
        _mark_session_status(conn, session_id, "SUCCESS", STATUS_SUCCESS, perform_result["statusText"])
        conn.commit()
        conn.close()
        return _redirect_or_message(row["return_url"], STATUS_SUCCESS, perform_result["statusText"], row["transaction_id"])

    _mark_session_status(conn, session_id, "FAILED", perform_result["status"], perform_result["statusText"])
    conn.commit()
    conn.close()
    return _redirect_or_message(row["return_url"], perform_result["status"], perform_result["statusText"], row["transaction_id"])


@app.post("/checkout/{session_id}/cancel")
def cancel_payment(session_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, transaction_id, return_url, status FROM payment_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="payment session not found")

    if row["status"] == "PENDING":
        _mark_session_status(conn, session_id, "CANCELED", STATUS_CUSTOM, "user_canceled")
        conn.commit()

    conn.close()
    return _redirect_or_message(row["return_url"], STATUS_CUSTOM, "user_canceled", row["transaction_id"])


@app.get("/checkout/{session_id}")
def get_checkout_status(session_id: str):
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, transaction_id, amount, amount_tiyin, currency_id, status, status_code, status_text, return_url
        FROM payment_sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="payment session not found")

    return dict(row)


def _decode_checkout_params(encoded_params: str) -> dict[str, Any]:
    try:
        decoded = base64.b64decode(encoded_params).decode()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid base64 payment params") from exc

    pairs = urllib.parse.parse_qs(decoded, keep_blank_values=True)

    def pick(name: str, default: str | None = None) -> str | None:
        values = pairs.get(name)
        if not values:
            return default
        return values[0]

    merchant_id = pick("merchant_id")
    amount_str = pick("amount")

    if not merchant_id or not amount_str:
        raise HTTPException(status_code=400, detail="merchant_id and amount are required")

    amount_in_tiyin = (pick("amount_in_tiyin", "False") or "False").lower() in {"true", "1", "yes"}

    try:
        currency_id = int(pick("currency_id", str(CURRENCY_UZS)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="currency_id must be integer") from exc

    if currency_id not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail="currency_id must be 860 or 840")

    try:
        uuid.UUID(merchant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="merchant_id must be UUID") from exc

    account: dict[str, Any] = {}
    for key, values in pairs.items():
        if key.startswith("account."):
            account[key.removeprefix("account.")] = values[0]

    return {
        "merchant_id": merchant_id,
        "amount": amount_str,
        "amount_in_tiyin": amount_in_tiyin,
        "currency_id": currency_id,
        "return_url": pick("return_url"),
        "account": account,
    }


def _get_active_merchant(merchant_id: str) -> sqlite3.Row:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, is_active FROM merchants WHERE id = ?",
        (merchant_id,),
    ).fetchone()
    conn.close()

    if not row or not row["is_active"]:
        raise HTTPException(status_code=404, detail="merchant not found or inactive")

    return row


def _normalize_amount(amount_str: str, currency_id: int, amount_in_tiyin: bool) -> tuple[Decimal, int]:
    try:
        raw_amount = Decimal(str(amount_str))
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="invalid amount") from exc

    if raw_amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")

    if amount_in_tiyin:
        amount_tiyin = int(raw_amount)
        if Decimal(amount_tiyin) != raw_amount:
            raise HTTPException(status_code=400, detail="amount_in_tiyin requires integer amount")
        amount = (Decimal(amount_tiyin) / Decimal("100")).quantize(Decimal("0.01"))
    else:
        amount = raw_amount.quantize(Decimal("0.01"))
        amount_tiyin = int((amount * Decimal("100")).quantize(Decimal("1")))

    if currency_id not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail="unsupported currency")

    if amount < Decimal("500") and currency_id == CURRENCY_UZS:
        raise HTTPException(status_code=400, detail="minimum amount for UZS is 500")

    return amount, amount_tiyin


def _amount_for_payload(amount: Decimal) -> int | float:
    as_int = int(amount)
    if Decimal(as_int) == amount:
        return as_int
    return float(amount)


def _call_merchant(
    conn: sqlite3.Connection,
    session_id: str,
    merchant: dict[str, Any],
    method_name: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    try:
        response = requests.post(
            merchant["callback_url"],
            json=payload,
            auth=(merchant["callback_auth_username"], merchant["callback_auth_password"]),
            timeout=5,
        )
        response_body = response.text
        response_status = response.status_code

        parsed = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

        result = parsed.get("result", {}) if isinstance(parsed, dict) else {}
        status = str(result.get("status", STATUS_MAINTENANCE))
        status_text = str(result.get("statusText", "maintenance"))

        success = 1 if response.ok else 0
    except Exception as exc:  # noqa: BLE001
        response_status = None
        response_body = str(exc)
        status = STATUS_MAINTENANCE
        status_text = "callback_unreachable"
        success = 0

    conn.execute(
        """
        INSERT INTO callback_logs (
            payment_session_id, method, request_json, response_status,
            response_body, success, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            method_name,
            json.dumps(payload),
            response_status,
            response_body,
            success,
            now_iso(),
        ),
    )

    return {
        "status": status,
        "statusText": status_text,
    }


def _mark_session_status(
    conn: sqlite3.Connection,
    session_id: str,
    status: str,
    status_code: str,
    status_text: str,
) -> None:
    conn.execute(
        """
        UPDATE payment_sessions
        SET status = ?, status_code = ?, status_text = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, status_code, status_text, now_iso(), session_id),
    )


def _render_checkout_page(session_id: str, transaction_id: str, amount: Decimal, currency_id: int) -> str:
    currency = "UZS" if currency_id == CURRENCY_UZS else "USD"
    return f"""
    <html>
      <head>
        <title>FakePay Checkout</title>
        <style>
          body {{ font-family: sans-serif; background: #f4f6fb; margin: 0; height: 100vh; display: grid; place-items: center; }}
          .card {{ background: #fff; border-radius: 12px; box-shadow: 0 12px 30px rgba(0,0,0,.08); width: 480px; padding: 24px; }}
          .meta {{ font-size: 13px; color: #475467; }}
          .amount {{ font-size: 30px; margin: 12px 0; }}
          .actions {{ display: flex; gap: 12px; margin-top: 20px; }}
          button {{ border: 0; border-radius: 8px; padding: 10px 14px; cursor: pointer; font-weight: 600; }}
          .pay {{ background: #16a34a; color: white; }}
          .cancel {{ background: #ef4444; color: white; }}
        </style>
      </head>
      <body>
        <div class="card">
          <h2>Paylov Clone Checkout</h2>
          <div class="meta">Session: {session_id}</div>
          <div class="meta">Transaction: {transaction_id}</div>
          <div class="amount">{amount} {currency}</div>
          <p>
            On pay, FakePay will call merchant callback using JSON-RPC methods
            <code>transaction.check</code> and <code>transaction.perform</code>.
          </p>
          <div class="actions">
            <form action="/checkout/{session_id}/confirm" method="post">
              <button class="pay" type="submit">Pay</button>
            </form>
            <form action="/checkout/{session_id}/cancel" method="post">
              <button class="cancel" type="submit">Cancel</button>
            </form>
          </div>
        </div>
      </body>
    </html>
    """


def _redirect_or_message(return_url: str | None, status_code: str, status_text: str, transaction_id: str):
    if return_url:
        target = f"{return_url}?status={urllib.parse.quote(status_code)}&statusText={urllib.parse.quote(status_text)}&transaction_id={transaction_id}"
        return RedirectResponse(url=target, status_code=302)

    return HTMLResponse(
        content=(
            "<html><body><h2>Payment flow completed</h2>"
            f"<p>Status: {status_code}</p>"
            f"<p>Message: {status_text}</p>"
            f"<p>Transaction: {transaction_id}</p>"
            "</body></html>"
        )
    )
