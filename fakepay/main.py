import sqlite3
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="FakePay Gateway Simulation")

DB_FILE = "fakepay.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_sessions (
            id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            callback_url TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


class CheckoutRequest(BaseModel):
    amount: float
    currency: str
    callback_url: Optional[str] = None
    # Add any additional fields Django expects if it sends them, or we can just ignore them


@app.post("/checkout")
def create_checkout(data: CheckoutRequest):
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payment_sessions (id, amount, currency, status, callback_url) VALUES (?, ?, ?, ?, ?)",
        (session_id, data.amount, data.currency, "PENDING", data.callback_url),
    )
    conn.commit()
    conn.close()

    return {"session_id": session_id, "checkout_url": f"http://localhost:8001/checkout/{session_id}"}


@app.get("/checkout/{session_id}", response_class=HTMLResponse)
def get_checkout_page(session_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT amount, currency, status FROM payment_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Payment session not found")

    amount, currency, status = row

    if status != "PENDING":
        return f"<h1>Payment already processed. Status: {status}</h1>"

    html_content = f"""
    <html>
        <head>
            <title>FakePay Checkout</title>
            <style>
                body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f9; }}
                .card {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
                button {{ background: #28a745; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; }}
                button:hover {{ background: #218838; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>FakePay Gateway</h2>
                <p>You are about to pay <strong>{amount} {currency}</strong>.</p>
                <form action="/confirm/{session_id}" method="post">
                    <button type="submit">Pay Now</button>
                </form>
            </div>
        </body>
    </html>
    """
    return html_content


@app.post("/confirm/{session_id}")
def confirm_payment(session_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT callback_url FROM payment_sessions WHERE id = ? AND status = 'PENDING'", (session_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Pending payment session not found or already processed.")

    callback_url = row[0]

    cursor.execute("UPDATE payment_sessions SET status = 'SUCCESS' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

    if callback_url:
        try:
            # We could send a POST with status here
            # Make sure it's non-blocking or just fire and forget for this mock
            # requests.post(callback_url, json={"session_id": session_id, "status": "SUCCESS"}, timeout=2)
            pass  # Keep it simple and let the instructor implement the webhook handling in their own way or we can enable it
        except Exception:
            pass

    # Simple success page
    html_content = """
    <html>
        <head>
            <title>Payment Successful</title>
            <style>
                body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #e8f5e9; color: #2e7d32; text-align: center;}}
                .card {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Payment Successful!</h2>
                <p>Thank you for your purchase. The transaction has been confirmed.</p>
                <p>You may now close this window or return to the application.</p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
