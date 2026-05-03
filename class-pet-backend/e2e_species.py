"""宠物物种 E2E：CRUD + Fallback 行为"""
import sys, io, time, httpx
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:5173/api/v1"


def step(n, desc):
    print(f"\n[{n}] {desc}")


def find_asset(species, level):
    """fallback：找该物种 ≤ level 中最大的资源"""
    best = None
    for a in species["assets"]:
        if a["level"] <= level and (best is None or a["level"] > best["level"]):
            best = a
    return best


def main():
    client = httpx.Client(base_url=BASE, timeout=10.0)
    suffix = str(int(time.time()))

    client.post("/auth/register", json={"username": f"sp{suffix}", "password": "test123", "display_name": "S"})
    r = client.post("/auth/login", data={"username": f"sp{suffix}", "password": "test123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    step(1, "GET 物种列表 → 应有 6 个预置物种 + 各等级资源")
    r = client.get("/pet-species", headers=auth)
    species_list = r.json()
    print(f"  count: {len(species_list)}")
    print(f"  codes: {[s['code'] for s in species_list]}")
    assert len(species_list) >= 6
    dragon = next(s for s in species_list if s["code"] == "dragon")
    print(f"  dragon assets: {[(a['level'], a['emoji']) for a in dragon['assets']]}")
    assert len(dragon["assets"]) == 4

    step(2, "Fallback 检查：dragon Lv1=🥚, Lv2=🦎, Lv4=🐉(回退), Lv6=🐲(>=5), Lv99=🐲")
    cases = [(1, '🥚'), (2, '🦎'), (3, '🐉'), (4, '🐉'), (5, '🐲'), (6, '🐲'), (99, '🐲')]
    for level, expected in cases:
        a = find_asset(dragon, level)
        actual = a["emoji"] if a else None
        ok = "PASS" if actual == expected else "FAIL"
        print(f"  {ok} dragon Lv.{level} = {actual} (expect {expected})")
        assert actual == expected

    step(3, "Fallback 边界：panda 只有 Lv1/Lv2，Lv99 应回退到 Lv2")
    panda = next(s for s in species_list if s["code"] == "panda")
    a = find_asset(panda, 99)
    print(f"  panda Lv99 = {a['emoji']} (level={a['level']})")
    assert a["level"] == 2

    step(4, "新建物种「凤凰」")
    r = client.post("/pet-species", json={
        "code": "phoenix", "name": "凤凰", "description": "传说中的不死鸟",
        "sort_order": 10,
    }, headers=auth)
    assert r.status_code in (200, 201)
    phoenix_id = r.json()["id"]

    step(5, "重复 code 应 400")
    r = client.post("/pet-species", json={"code": "phoenix", "name": "X"}, headers=auth)
    print(f"  status: {r.status_code}")
    assert r.status_code == 400

    step(6, "为凤凰添加 Lv1/Lv5/Lv10 三档资源")
    for level, emoji in [(1, '🥚'), (5, '🐦'), (10, '🦅')]:
        r = client.post(f"/pet-species/{phoenix_id}/assets", json={
            "level": level, "emoji": emoji,
        }, headers=auth)
        assert r.status_code in (200, 201), r.text

    step(7, "重复 level 应 400")
    r = client.post(f"/pet-species/{phoenix_id}/assets", json={
        "level": 5, "emoji": "🦜",
    }, headers=auth)
    print(f"  status: {r.status_code}")
    assert r.status_code == 400

    step(8, "GET 凤凰 fallback：Lv7 应回退到 Lv5（🐦）")
    r = client.get("/pet-species", headers=auth)
    phoenix = next(s for s in r.json() if s["code"] == "phoenix")
    a = find_asset(phoenix, 7)
    print(f"  phoenix Lv7 = {a['emoji']} (level={a['level']})")
    assert a["level"] == 5
    assert a["emoji"] == "🐦"

    step(9, "PATCH 编辑凤凰 Lv5 资源 → 改 emoji")
    lv5_asset = next(a for a in phoenix["assets"] if a["level"] == 5)
    r = client.patch(f"/pet-species/{phoenix_id}/assets/{lv5_asset['id']}", json={
        "emoji": "🔥",
    }, headers=auth)
    assert r.json()["emoji"] == "🔥"

    step(10, "DELETE 凤凰 Lv5 资源 → Lv7 应再回退到 Lv1")
    r = client.delete(f"/pet-species/{phoenix_id}/assets/{lv5_asset['id']}", headers=auth)
    assert r.status_code in (200, 204)
    r = client.get("/pet-species", headers=auth)
    phoenix = next(s for s in r.json() if s["code"] == "phoenix")
    a = find_asset(phoenix, 7)
    print(f"  phoenix Lv7 (Lv5 deleted) = {a['emoji']} (level={a['level']})")
    assert a["level"] == 1

    step(11, "PATCH 编辑物种名「凤凰」→「不死鸟」（code 不变）")
    r = client.patch(f"/pet-species/{phoenix_id}", json={"name": "不死鸟"}, headers=auth)
    j = r.json()
    print(f"  name: {j['name']}, code: {j['code']}")
    assert j["name"] == "不死鸟"
    assert j["code"] == "phoenix"

    step(12, "DELETE 物种 → 资源级联删除")
    r = client.delete(f"/pet-species/{phoenix_id}", headers=auth)
    assert r.status_code in (200, 204)
    r = client.get("/pet-species", headers=auth)
    codes = [s["code"] for s in r.json()]
    assert "phoenix" not in codes
    print("  已删除")

    print("\n=== 宠物物种 12 步通过 ===")


if __name__ == "__main__":
    main()
