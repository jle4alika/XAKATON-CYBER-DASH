import httpx


async def test_register_login_me(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "pass12345"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "id" in body

    r = await client.post("/api/auth/login", json={"username": "alice", "password": "pass12345"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    r = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["username"] == "alice"
    assert me["email"] == "alice@example.com"


async def test_register_duplicate_username(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob1@example.com", "password": "pass12345"},
    )
    assert r.status_code == 201, r.text

    r = await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob2@example.com", "password": "pass12345"},
    )
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Username already registered"


async def test_login_wrong_password(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "pass12345"},
    )
    assert r.status_code == 201, r.text

    r = await client.post("/api/auth/login", json={"username": "carol", "password": "bad"})
    assert r.status_code == 401, r.text
    assert r.json()["detail"] == "Incorrect username or password"


async def test_users_me_requires_auth(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/users/me")
    assert r.status_code == 401, r.text
    # Обычно FastAPI/OAuth2PasswordBearer возвращает "Not authenticated"
    assert r.json()["detail"] in {"Not authenticated", "Unauthorized"}
