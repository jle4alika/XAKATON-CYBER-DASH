import httpx


async def test_agents_list_empty(client: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.get("/api/agents", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json() == []


async def test_agents_create_and_get(client: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
    payload = {
        "name": "Agent Smith",
        "mood": 0.6,
        "energy": 90,
        "traits": ["calm", "strategic"],
        "persona": "Security analyst",
        "current_task": "monitoring",
    }
    r = await client.post("/api/agents", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    agent = r.json()
    assert agent["name"] == payload["name"]
    assert "id" in agent

    agent_id = agent["id"]

    r = await client.get("/api/agents", headers=auth_headers)
    assert r.status_code == 200, r.text
    agents = r.json()
    assert len(agents) == 1
    assert agents[0]["id"] == agent_id

    r = await client.get(f"/api/agents/{agent_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    detailed = r.json()
    assert detailed["id"] == agent_id
    assert isinstance(detailed.get("plans"), list)
    assert isinstance(detailed.get("memories"), list)
    assert isinstance(detailed.get("interactions"), list)
