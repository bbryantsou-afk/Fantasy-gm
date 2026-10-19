import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import urlencode

import requests

AUTHORIZE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
API_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"


def build_authorization_url(client_id, client_secret, redirect_uri, theme=None):
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(24)
    if theme in ("light","tactics","mirror"):
        nonce = theme + "~" + nonce
    message = f"{timestamp}.{nonce}"
    signature = hmac.new(
        client_secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    state = f"{message}.{signature}"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "language": "en-us",
        "state": state,
    }
    url = f"{AUTHORIZE_URL}?{urlencode(params)}"
    return url, state



def exchange_code_for_token(
    code, returned_state, expected_state,
    client_id, client_secret, redirect_uri
):
    # 驗證 Yahoo 回傳的 state 簽章與有效期限。
    # 不依賴 Streamlit session_state 保存原始 state。
    if not returned_state:
        raise ValueError("Yahoo 沒有回傳 OAuth state，請重新授權。")

    try:
        timestamp, nonce, signature = returned_state.split(".", 2)
        age = int(time.time()) - int(timestamp)

        message = f"{timestamp}.{nonce}"
        expected_signature = hmac.new(
            client_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        if (
            age < 0
            or age > 600
            or not hmac.compare_digest(
                signature, expected_signature
            )
        ):
            raise ValueError(
                "OAuth 狀態已過期或驗證失敗，請重新授權。"
            )

    except (ValueError, TypeError):
        raise ValueError("OAuth 狀態無效，請重新授權。")

    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode("ascii")

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Yahoo Token 交換失敗（HTTP {response.status_code}）。"
            "請確認憑證、Redirect URI 及 API 存取權。"
        )

    return response.json()



def yahoo_api_get(access_token, resource="users;use/games;game_codes=nba"):
    resource = resource.lstrip("/")
    response = requests.get(
        f"{API_BASE}/{resource}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"format": "json"},
        timeout=30,
    )

    if not response.ok:
	    detail = response.text[:1000]
	    raise RuntimeError(
	        f"Yahoo Fantasy API 請求失敗（HTTP {response.status_code}）。"
	        f"Yahoo 回應內容：{detail}"
	    )
    return response.json()
