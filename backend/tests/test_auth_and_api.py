import pytest

from app.core import security
from app.services.auth_service import create_user

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture()
def admin(db):
    try:
        create_user(db, email=ADMIN_EMAIL, password=ADMIN_PASSWORD, role="platform_admin")
    except ValueError:
        pass  # already created by a previous test of the session


@pytest.mark.parametrize(
    ("password", "reason"),
    [
        ("short", "at least 10 characters"),
        ("alllowercase123!", "uppercase"),
    ],
)
def test_weak_passwords_are_refused(password, reason):
    with pytest.raises(ValueError, match=reason):
        security.validate_password_strength(password)


def test_a_strong_password_is_accepted():
    security.validate_password_strength(ADMIN_PASSWORD)


def test_passwords_are_hashed_and_verified():
    hashed = security.hash_password(ADMIN_PASSWORD)

    assert ADMIN_PASSWORD not in hashed
    assert security.verify_password(ADMIN_PASSWORD, hashed) is True
    assert security.verify_password("wrong", hashed) is False


def test_token_round_trip_and_tampering():
    token = security.create_access_token(subject="42", extra_claims={"role": "client_admin"})
    claims = security.decode_access_token(token)

    assert claims["sub"] == "42"
    assert claims["role"] == "client_admin"
    with pytest.raises(ValueError):
        security.decode_access_token(token[:-2] + "xx")


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}


@pytest.mark.parametrize(
    "path",
    ["/api/v1/history", "/api/v1/alerts/", "/api/v1/auth/me", "/api/v1/clients"],
)
def test_protected_routes_require_a_token(client, path):
    assert client.get(path).status_code in (401, 403)


def test_login_then_read_own_profile(client, admin):
    login = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL
    assert me.json()["role"] == "platform_admin"
    assert "password" not in str(me.json()).lower()


def test_wrong_password_is_rejected(client, admin):
    response = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "Wrong!Passw0rd1"}
    )
    assert response.status_code == 401


def test_analysis_needs_a_client_account(client, admin):
    token = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    ).json()["access_token"]

    # A platform administrator is not a tenant: uploading data is refused.
    response = client.post(
        "/api/v1/analysis/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("t.csv", b"transaction_id,amount\nT1,10\n", "text/csv")},
    )
    assert response.status_code == 403
