from datetime import datetime, timedelta, timezone
from jose import jwt
import jose
from functools import wraps
from flask import jsonify, request
import os

# SECRET_KEY = "super secret key"
SECRET_KEY = os.environ.get("SECRET_KEY") or "super secret secrets"


def encode_token(customer_id):
    # using unique pieces of info to make our tokens user specific
    payload = {
        "exp": datetime.now(timezone.utc)
        + timedelta(days=0, hours=1),  # Setting the expiration time to an hour past NOW
        "iat": datetime.now(timezone.utc),  # iat = Issued at
        "sub": str(
            customer_id
        ),  # This needs to be a string or the token will be malformed and won't be able to be decoded.
    }

    token = jwt.encode(
        payload, SECRET_KEY, algorithm="HS256"
    )  # algorithm to encode the token
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            # Accept "Bearer <token>" or a bare token (Swagger UI does not add "Bearer")
            parts = request.headers["Authorization"].split()
            if len(parts) == 1:
                token = parts[0]
            elif len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
            elif parts:
                return jsonify({"message": "Token format invalid"}), 401

        if not token:
            return jsonify({"message": "Required token missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            customer_id = data["sub"]
        except jose.exceptions.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jose.exceptions.JWTError:
            return jsonify({"message": "Invalid token"}), 401

        # ✅ Execute the wrapped function with decoded customer ID
        return f(customer_id, *args, **kwargs)

    return decorated
