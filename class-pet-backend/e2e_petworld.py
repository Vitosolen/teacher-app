"""宠物世界 E2E：5 类商品 + 房子/家具装备规则验证（经 Vite 代理）"""
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
    username = f"world_{suffix}"

    # —— 准备 ——
    client.post("/auth/register", json={
        "username": username, "password": "test123", "display_name": "宠物世界老师"
    })
    r = client.post("/auth/login",
                    data={"username": username, "password": "test123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post("/classes", json={"name": "测试班"}, headers=auth)
    cid = r.json()["id"]
    r = client.post(f"/classes/{cid}/students/batch",
                    json={"names": ["小明"]}, headers=auth)
    stu = r.json()[0]
    pet_id = stu["pet"]["id"]

    step(1, "GET 商品列表 → 应有 5 类共 20 件")
    r = client.get("/shop-items", headers=auth)
    items = r.json()
    by_type: dict[str, list] = {}
    for it in items:
        by_type.setdefault(it["item_type"], []).append(it)
    print(f"  共 {len(items)} 件，分类: " + ", ".join(f"{t}={len(v)}" for t, v in sorted(by_type.items())))
    assert len(items) == 20
    assert "房子" in by_type and len(by_type["房子"]) == 3
    assert "家具" in by_type and len(by_type["家具"]) == 5

    step(2, "给小明刷 3000 积分（用于扫货）")
    rules = client.get("/score-rules", headers=auth).json()
    youxiu = next(r for r in rules if r["label"] == "作业优秀")  # +5
    for _ in range(600):
        client.post("/behaviors", json={
            "student_id": stu["id"], "score_rule_id": youxiu["id"],
        }, headers=auth)
    r = client.get(f"/students/{stu['id']}", headers=auth)
    print(f"  积分: {r.json()['points']}")
    assert r.json()["points"] >= 2000

    step(3, "兑换 2 件房子 + 3 件家具 + 1 件衣服")
    house_a = next(i for i in by_type["房子"] if i["name"] == "简易木屋")
    house_b = next(i for i in by_type["房子"] if i["name"] == "温馨小屋")
    chair = next(i for i in by_type["家具"] if i["name"] == "椅子")
    plant = next(i for i in by_type["家具"] if i["name"] == "盆栽")
    sofa = next(i for i in by_type["家具"] if i["name"] == "沙发")
    hat = next(i for i in by_type["衣服"] if i["name"] == "礼帽")

    house_a_owned = client.post(f"/shop-items/{house_a['id']}/redeem",
                                json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    house_b_owned = client.post(f"/shop-items/{house_b['id']}/redeem",
                                json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    chair_owned = client.post(f"/shop-items/{chair['id']}/redeem",
                              json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    plant_owned = client.post(f"/shop-items/{plant['id']}/redeem",
                              json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    sofa_owned = client.post(f"/shop-items/{sofa['id']}/redeem",
                             json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    hat_owned = client.post(f"/shop-items/{hat['id']}/redeem",
                            json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    print(f"  6 件物品已兑换")

    step(4, "装备 木屋 + 礼帽 + 椅子（3 类同时装备）")
    client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": house_a_owned}, headers=auth)
    client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": hat_owned}, headers=auth)
    client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": chair_owned}, headers=auth)
    r = client.get(f"/pets/{pet_id}/owned-items", headers=auth)
    owned = r.json()
    house_now = next(o for o in owned if o["id"] == house_a_owned)
    hat_now = next(o for o in owned if o["id"] == hat_owned)
    chair_now = next(o for o in owned if o["id"] == chair_owned)
    print(f"  房子equipped={house_now['equipped']}, 衣服equipped={hat_now['equipped']}, 椅子equipped={chair_now['equipped']}")
    assert all([house_now["equipped"], hat_now["equipped"], chair_now["equipped"]])

    step(5, "再装备「温馨小屋」→ 木屋自动卸下（房子互斥）")
    client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": house_b_owned}, headers=auth)
    owned = client.get(f"/pets/{pet_id}/owned-items", headers=auth).json()
    house_a_now = next(o for o in owned if o["id"] == house_a_owned)
    house_b_now = next(o for o in owned if o["id"] == house_b_owned)
    print(f"  木屋equipped={house_a_now['equipped']}, 小屋equipped={house_b_now['equipped']}")
    assert house_a_now["equipped"] is False
    assert house_b_now["equipped"] is True

    step(6, "再装备 盆栽 + 沙发 → 与椅子并存（家具不互斥）")
    client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": plant_owned}, headers=auth)
    client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": sofa_owned}, headers=auth)
    owned = client.get(f"/pets/{pet_id}/owned-items", headers=auth).json()
    placed = [o for o in owned if o["equipped"] and o["item"]["item_type"] == "家具"]
    print(f"  已摆放家具: {[o['item']['name'] for o in placed]}")
    assert len(placed) == 3

    step(7, "卸下沙发 → 剩 2 件家具")
    client.post(f"/pets/{pet_id}/unequip", json={"owned_item_id": sofa_owned}, headers=auth)
    owned = client.get(f"/pets/{pet_id}/owned-items", headers=auth).json()
    placed = [o for o in owned if o["equipped"] and o["item"]["item_type"] == "家具"]
    print(f"  剩余家具: {[o['item']['name'] for o in placed]}")
    assert len(placed) == 2

    step(8, "校验：食品/玩具不能 equip → 应 400")
    apple = next(i for i in by_type["食品"] if i["name"] == "苹果")
    apple_owned = client.post(f"/shop-items/{apple['id']}/redeem",
                              json={"student_id": stu["id"]}, headers=auth).json()["owned_item"]["id"]
    r = client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": apple_owned}, headers=auth)
    print(f"  食品 equip 状态: {r.status_code}")
    assert r.status_code == 400

    step(9, "最终场景快照：列出当前激活的所有装备")
    owned = client.get(f"/pets/{pet_id}/owned-items", headers=auth).json()
    snapshot = {
        "房子": [o["item"]["name"] for o in owned if o["equipped"] and o["item"]["item_type"] == "房子"],
        "衣服": [o["item"]["name"] for o in owned if o["equipped"] and o["item"]["item_type"] == "衣服"],
        "家具": [o["item"]["name"] for o in owned if o["equipped"] and o["item"]["item_type"] == "家具"],
    }
    print(f"  {snapshot}")
    assert len(snapshot["房子"]) == 1
    assert len(snapshot["衣服"]) == 1
    assert len(snapshot["家具"]) == 2

    print("\n=== 宠物世界 9 步通过 ===")


if __name__ == "__main__":
    main()
