"""领养系统 E2E：新学生无宠物 → 领养 → 重复领养 400"""
import sys
import io
import time
import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "http://127.0.0.1:5173/api/v1"


def step(n, desc):
    print(f"\n[{n}] {desc}")


def main():
    client = httpx.Client(base_url=BASE, timeout=10.0)
    suffix = str(int(time.time()))
    username = f"adopt_{suffix}"

    client.post("/auth/register", json={
        "username": username, "password": "test123", "display_name": "领养测试"
    })
    r = client.post("/auth/login",
                    data={"username": username, "password": "test123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post("/classes", json={"name": "领养班"}, headers=auth)
    cid = r.json()["id"]

    step(1, "添加学生「小明」→ 应没有宠物（pet=null）")
    r = client.post(f"/classes/{cid}/students",
                    json={"name": "小明"}, headers=auth)
    assert r.status_code in (200, 201), r.text
    stu = r.json()
    print(f"  pet: {stu['pet']}")
    assert stu["pet"] is None, "新学生不应自动建宠物"

    step(2, "批量导入 3 名学生 → 都没有宠物")
    r = client.post(f"/classes/{cid}/students/batch",
                    json={"names": ["李四", "王五", "赵六"]}, headers=auth)
    batch = r.json()
    print(f"  pets: {[s['pet'] for s in batch]}")
    assert all(s["pet"] is None for s in batch)

    step(3, "GET 学生详情 → pet=null")
    r = client.get(f"/students/{stu['id']}", headers=auth)
    assert r.json()["pet"] is None

    step(4, "领养：选 cat 物种，起名「咪咪」")
    r = client.post(f"/students/{stu['id']}/adopt-pet", json={
        "name": "咪咪", "species": "cat",
    }, headers=auth)
    assert r.status_code in (200, 201), r.text
    after = r.json()
    print(f"  pet: name={after['pet']['name']}, species={after['pet']['species']}, level={after['pet']['level']}")
    assert after["pet"] is not None
    assert after["pet"]["name"] == "咪咪"
    assert after["pet"]["species"] == "cat"
    assert after["pet"]["level"] == 1

    step(5, "重复领养 → 应 400")
    r = client.post(f"/students/{stu['id']}/adopt-pet", json={
        "name": "新猫", "species": "dog",
    }, headers=auth)
    print(f"  status: {r.status_code}, detail: {r.json().get('detail')}")
    assert r.status_code == 400

    step(6, "其他物种领养 → 各 1 只（dog/dragon/rabbit）")
    species_for = {"李四": "dog", "王五": "dragon", "赵六": "rabbit"}
    for s in batch:
        sp = species_for[s["name"]]
        r = client.post(f"/students/{s['id']}/adopt-pet", json={
            "name": f"{s['name']}的{sp}", "species": sp,
        }, headers=auth)
        assert r.status_code in (200, 201), r.text
        print(f"  {s['name']} 领养了 species={r.json()['pet']['species']}")

    step(7, "班级学生列表 → 全部已领养")
    r = client.get(f"/classes/{cid}/students", headers=auth)
    rows = r.json()
    species_list = [s["pet"]["species"] for s in rows]
    print(f"  species: {species_list}")
    assert all(s["pet"] is not None for s in rows)
    assert set(species_list) == {"cat", "dog", "dragon", "rabbit"}

    step(8, "给小明的猫加分 → 升级后 species 不变")
    rules = client.get("/score-rules", headers=auth).json()
    youxiu = next(r for r in rules if r["label"] == "作业优秀")
    for _ in range(15):
        client.post("/behaviors", json={
            "student_id": stu["id"], "score_rule_id": youxiu["id"],
        }, headers=auth)
    r = client.get(f"/students/{stu['id']}", headers=auth)
    pet = r.json()["pet"]
    print(f"  level={pet['level']}, species={pet['species']} (期望 cat 不变)")
    assert pet["species"] == "cat"
    assert pet["level"] >= 3

    step(9, "权限：跨老师领养 → 403")
    other = f"oth_{suffix}"
    client.post("/auth/register", json={"username": other, "password": "test123", "display_name": "B"})
    r2 = client.post("/auth/login", data={"username": other, "password": "test123"},
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    other_auth = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    # 给 other 也建一个学生
    r = client.post("/classes", json={"name": "B 班"}, headers=other_auth)
    other_cid = r.json()["id"]
    r = client.post(f"/classes/{other_cid}/students", json={"name": "B 学生"}, headers=other_auth)
    other_sid = r.json()["id"]
    # 用 other 的 token 想给小明领养 → 应 403
    r = client.post(f"/students/{stu['id']}/adopt-pet",
                    json={"name": "x", "species": "cat"},
                    headers=other_auth)
    print(f"  跨老师领养 status: {r.status_code}")
    assert r.status_code in (403, 404)

    print("\n=== 领养系统 9 步通过 ===")


if __name__ == "__main__":
    main()
