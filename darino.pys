import requests, json

BASE = "https://api.darino.vip"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "origin": "https://darino.vip"
}

def clean_json(text):
    if "{" in text:
        text = text[text.find("{"):]
    if "}" in text:
        text = text[:text.rfind("}")+1]
    return json.loads(text)

def register(email, password, promo=None):
    payload = {
        "email": email,
        "password": password,
        "confirmPassword": password,
        "promo_code": promo or ""
    }

    r = requests.post(
        f"{BASE}/h5/taskBase/biz3/register",
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=15
    )

    result = clean_json(r.text)
    return result.get("code") == 0, result

def login(email, password):
    payload = {"email": email, "password": password}
    r = requests.post(f"{BASE}/h5/taskBase/login",
                      headers=HEADERS,
                      data=json.dumps(payload))
    return clean_json(r.text)

def request_phone_code(uuid, phone, token):
    h = HEADERS.copy()
    h["x-token"] = token

    payload = {
        "uuid": uuid,
        "phone": phone.replace("+", ""),
        "type": 2
    }

    r = requests.post(
        f"{BASE}/h5/taskUser/phoneCode",
        headers=h,
        data=json.dumps(payload)
    )

    return clean_json(r.text)

def scan_result(uuid, token):
    h = HEADERS.copy()
    h["x-token"] = token

    r = requests.post(
        f"{BASE}/h5/taskUser/scanCodeResult",
        headers=h,
        data=json.dumps({"uuid": uuid})
    )

    return clean_json(r.text)
