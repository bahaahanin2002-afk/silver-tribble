📌 سكيمة API (JSON Blueprint)
{
  "endpoints": [
    {
      "method": "POST",
      "path": "/auth/google",
      "description": "تسجيل الدخول عبر Google OAuth",
      "request": { "id_token": "string" },
      "response": { "access_token": "jwt_token" }
    },
    {
      "method": "POST",
      "path": "/auth/phone",
      "description": "تسجيل برقم الهاتف + OTP",
      "request": { "phone": "+123456789", "otp": "123456" },
      "response": { "access_token": "jwt_token" }
    },
    {
      "method": "POST",
      "path": "/binance/connect",
      "description": "ربط حساب Binance بمفاتيح API",
      "request": { "api_key": "string", "api_secret": "string" },
      "response": { "status": "connected" }
    },
    {
      "method": "GET",
      "path": "/binance/balances",
      "description": "جلب أرصدة الحساب من Binance",
      "response": {
        "balances": [
          { "asset": "USDT", "free": "100.0", "locked": "0.0" },
          { "asset": "BTC", "free": "0.01", "locked": "0.0" }
        ]
      }
    },
    {
      "method": "POST",
      "path": "/binance/order",
      "description": "تنفيذ أمر شراء/بيع",
      "request": {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 0.01
      },
      "response": {
        "orderId": 123456,
        "status": "FILLED"
      }
    }
  ]
}

📌 قالب كود FastAPI (أساسي)
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import jwt
import time
import hmac, hashlib
import requests

app = FastAPI()

# مفاتيح JWT (لتبسيط المثال)
SECRET_KEY = "mysecret"
ALGORITHM = "HS256"

# نموذج بيانات Binance
class BinanceConnect(BaseModel):
    api_key: str
    api_secret: str

class OrderRequest(BaseModel):
    symbol: str
    side: str
    type: str
    quantity: float

# ذاكرة مؤقتة (بدل DB)
user_binance = {}

# 🔑 إصدار JWT
def create_token(user_id: str):
    payload = {"sub": user_id, "exp": time.time() + 3600}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ✅ تسجيل دخول تجريبي
@app.post("/auth/phone")
def login_phone(phone: str, otp: str):
    if otp == "123456":  # هنا لازم ربط مع Twilio/Firebase
        token = create_token(phone)
        return {"access_token": token}
    raise HTTPException(401, "OTP غير صحيح")

# 🔗 ربط Binance
@app.post("/binance/connect")
def connect_binance(data: BinanceConnect):
    user_binance["api_key"] = data.api_key
    user_binance["api_secret"] = data.api_secret
    return {"status": "connected"}

# 📊 جلب أرصدة من Binance
@app.get("/binance/balances")
def get_balances():
    if "api_key" not in user_binance:
        raise HTTPException(401, "اربط Binance أولاً")

    api_key = user_binance["api_key"]
    api_secret = user_binance["api_secret"]

    url = "https://api.binance.com/api/v3/account"
    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {"X-MBX-APIKEY": api_key}
    r = requests.get(f"{url}?{query_string}&signature={signature}", headers=headers)

    if r.status_code != 200:
        raise HTTPException(400, "فشل الاتصال ببايننس")

    data = r.json()
    balances = [{"asset": b["asset"], "free": b["free"], "locked": b["locked"]}
                for b in data["balances"] if float(b["free"]) > 0]
    return {"balances": balances}

# 💸 تنفيذ أمر
@app.post("/binance/order")
def place_order(order: OrderRequest):
    if "api_key" not in user_binance:
        raise HTTPException(401, "اربط Binance أولاً")

    api_key = user_binance["api_key"]
    api_secret = user_binance["api_secret"]

    url = "https://api.binance.com/api/v3/order"
    timestamp = int(time.time() * 1000)
    query_string = f"symbol={order.symbol}&side={order.side}&type={order.type}&quantity={order.quantity}&timestamp={timestamp}"
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {"X-MBX-APIKEY": api_key}
    r = requests.post(f"{url}?{query_string}&signature={signature}", headers=headers)

    if r.status_code != 200:
        raise HTTPException(400, "فشل تنفيذ الأمر")

    return r.json()


📌 هذا القالب:

يدعم تسجيل دخول بالهاتف (بشكل مبسط).

ربط حساب Binance وتخزين المفاتيح (مؤقتًا في ذاكرة، تقدر تربط DB لاحقًا).

جلب أرصدة Binance.

تنفيذ أوامر شراء/بيع.
