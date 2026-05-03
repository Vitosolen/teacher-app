"""迭代 2 端到端验证：经 Vite 代理走完整新功能业务流"""
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
    username = f"iter2_{suffix}"

    step(1, "注册老师（应自动复制 9 条默认积分规则）")
    r = client.post("/auth/register", json={
        "username": username, "password": "test123", "display_name": "迭代2 老师"
    })
    assert r.status_code in (200, 201), r.text

    step(2, "登录")
    r = client.post(
        "/auth/login",
        data={"username": username, "password": "test123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    step(3, "校验默认积分规则已自动复制")
    r = client.get("/score-rules", headers=auth)
    rules = r.json()
    print(f"规则数: {len(rules)}")
    assert len(rules) == 9, f"期望 9 条默认规则，实际 {len(rules)}"
    answer_rule = next(r for r in rules if r["label"] == "回答问题")
    assert answer_rule["score"] == 1
    print(f"  「回答问题」 score={answer_rule['score']}")

    step(4, "创建班级")
    r = client.post("/classes", json={"name": "迭代2 五年级三班", "grade": "五年级"}, headers=auth)
    class_id = r.json()["id"]

    step(5, "PATCH 编辑班级名 -> 「迭代2 班级A」")
    r = client.patch(f"/classes/{class_id}", json={"name": "迭代2 班级A"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["name"] == "迭代2 班级A"

    step(6, "批量导入 5 名学生")
    r = client.post(f"/classes/{class_id}/students/batch",
                    json={"names": ["张三", "李四", "王五", "赵六", "钱七"]}, headers=auth)
    students = r.json()
    assert len(students) == 5
    zhangsan = next(s for s in students if s["name"] == "张三")
    print(f"  张三 points 初始值: {zhangsan['points']}")
    assert zhangsan["points"] == 0

    step(7, "PATCH 编辑学生 -> 改张三学号为 001")
    r = client.patch(f"/students/{zhangsan['id']}", json={"student_no": "001"}, headers=auth)
    assert r.json()["student_no"] == "001"

    step(8, "创建科目「语文」「数学」")
    r1 = client.post("/subjects", json={"name": "语文", "color": "#67C23A"}, headers=auth)
    r2 = client.post("/subjects", json={"name": "数学", "color": "#409EFF"}, headers=auth)
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)
    subj_yuwen = r1.json()["id"]
    print(f"  语文 id={subj_yuwen}")

    step(9, "重复创建「语文」 → 应 400")
    r = client.post("/subjects", json={"name": "语文"}, headers=auth)
    assert r.status_code == 400

    step(10, "创建积分规则「考试 90 以上」 +2")
    r = client.post("/score-rules", json={
        "label": "考试90以上", "category": "学习", "score": 2, "sort_order": 99,
    }, headers=auth)
    assert r.status_code in (200, 201)
    new_rule_id = r.json()["id"]

    step(11, "用积分规则给张三打分（+1 回答问题）→ 验证 student.points 累加")
    r = client.post("/behaviors", json={
        "student_id": zhangsan["id"],
        "score_rule_id": answer_rule["id"],
    }, headers=auth)
    assert r.status_code in (200, 201), r.text
    res = r.json()
    print(f"  pet exp={res['pet']['exp']}, student_points={res['student_points']}")
    assert res["student_points"] == 1
    assert res["behavior"]["score_rule_id"] == answer_rule["id"]

    step(12, "用新创建的「考试90以上」+2 → points 变 3")
    r = client.post("/behaviors", json={
        "student_id": zhangsan["id"],
        "score_rule_id": new_rule_id,
    }, headers=auth)
    res = r.json()
    print(f"  student_points={res['student_points']}")
    assert res["student_points"] == 3

    step(13, "扣分（-3 违纪）→ points 不变（仍是 3）")
    weiji = next(r for r in rules if r["label"] == "违纪")
    r = client.post("/behaviors", json={
        "student_id": zhangsan["id"],
        "score_rule_id": weiji["id"],
    }, headers=auth)
    res = r.json()
    print(f"  扣分后 student_points={res['student_points']}")
    assert res["student_points"] == 3

    step(14, "创建作业（语文，班级A，「作文 500 字」）→ 应自动为 5 名学生建 records")
    r = client.post("/homeworks", json={
        "class_id": class_id, "subject_id": subj_yuwen,
        "title": "作文 500 字", "content": "题目自定",
    }, headers=auth)
    assert r.status_code in (200, 201), r.text
    hw = r.json()
    print(f"  total={hw['total_count']}, graded={hw['graded_count']}")
    assert hw["total_count"] == 5
    assert hw["graded_count"] == 0
    hw_id = hw["id"]

    step(15, "GET 作业详情 → 验证 5 条 records")
    r = client.get(f"/homeworks/{hw_id}", headers=auth)
    detail = r.json()
    assert len(detail["records"]) == 5
    zs_record = next(rec for rec in detail["records"] if rec["student_name"] == "张三")
    print(f"  张三 record id={zs_record['id']}, status={zs_record['status']}")

    step(16, "批改张三作业：95 分 + 评语 → status 自动转 已批改")
    r = client.patch(f"/homework-records/{zs_record['id']}", json={
        "score": 95, "comment": "立意新颖，结构紧凑",
    }, headers=auth)
    assert r.json()["status"] == "已批改"
    assert r.json()["score"] == 95

    step(17, "GET 作业列表 → 验证 graded_count=1")
    r = client.get("/homeworks", headers=auth)
    hw_list = r.json()
    assert hw_list[0]["graded_count"] == 1
    print(f"  作业进度: {hw_list[0]['graded_count']}/{hw_list[0]['total_count']}")

    step(18, "GET 商品列表 → 应有 12 件预置商品")
    r = client.get("/shop-items", headers=auth)
    items = r.json()
    print(f"  商品数: {len(items)}")
    assert len(items) == 12
    apple = next(i for i in items if i["name"] == "苹果")
    hat = next(i for i in items if i["name"] == "礼帽")
    print(f"  苹果 price={apple['price']}, 礼帽 price={hat['price']}")

    step(19, "张三给宠物加分到 60 积分（避免兑换不够）")
    # 当前 points=3，要兑换 50 积分礼帽就要再加 47 → 用 5 分规则 10 次或者 +5 分类的
    youxiu = next(r for r in rules if r["label"] == "作业优秀")  # +5
    for _ in range(20):
        client.post("/behaviors", json={
            "student_id": zhangsan["id"], "score_rule_id": youxiu["id"],
        }, headers=auth)
    r = client.get(f"/students/{zhangsan['id']}", headers=auth)
    print(f"  张三 points={r.json()['points']}")
    assert r.json()["points"] >= 60

    step(20, "兑换苹果 → student.points 扣减 10")
    r = client.post(f"/shop-items/{apple['id']}/redeem", json={
        "student_id": zhangsan["id"],
    }, headers=auth)
    redeem = r.json()
    apple_owned_id = redeem["owned_item"]["id"]
    print(f"  剩余 points={redeem['student_points']}, owned_id={apple_owned_id}")

    step(21, "食用苹果 → pet.hunger 上涨 +5")
    r = client.get(f"/students/{zhangsan['id']}", headers=auth)
    pet_id = r.json()["pet"]["id"]
    hunger_before = r.json()["pet"]["hunger"]
    r = client.post(f"/pets/{pet_id}/consume", json={
        "owned_item_id": apple_owned_id,
    }, headers=auth)
    cr = r.json()
    print(f"  hunger {hunger_before} → {cr['hunger']}")
    assert cr["hunger"] >= min(100, hunger_before + 5) or cr["hunger"] == 100

    step(22, "兑换礼帽 + 装备 → equipped=true")
    r = client.post(f"/shop-items/{hat['id']}/redeem", json={
        "student_id": zhangsan["id"],
    }, headers=auth)
    hat_owned_id = r.json()["owned_item"]["id"]
    r = client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": hat_owned_id}, headers=auth)
    owned = r.json()
    hat_record = next(o for o in owned if o["id"] == hat_owned_id)
    assert hat_record["equipped"] is True
    print("  礼帽已装备")

    step(23, "再兑换一件衣服 + 装备 → 礼帽自动卸下（同时只能装备一件衣服）")
    sash = next(i for i in items if i["name"] == "围巾")
    r = client.post(f"/shop-items/{sash['id']}/redeem", json={
        "student_id": zhangsan["id"],
    }, headers=auth)
    sash_owned_id = r.json()["owned_item"]["id"]
    r = client.post(f"/pets/{pet_id}/equip", json={"owned_item_id": sash_owned_id}, headers=auth)
    owned = r.json()
    hat_now = next(o for o in owned if o["id"] == hat_owned_id)
    sash_now = next(o for o in owned if o["id"] == sash_owned_id)
    print(f"  礼帽 equipped={hat_now['equipped']}, 围巾 equipped={sash_now['equipped']}")
    assert hat_now["equipped"] is False
    assert sash_now["equipped"] is True

    step(24, "随机点名抽 3 人 → 返回 3 名班内学生")
    r = client.post(f"/classes/{class_id}/random-pick", json={"count": 3}, headers=auth)
    picked = r.json()
    print(f"  抽中: {[s['name'] for s in picked]}")
    assert len(picked) == 3
    names = [s["name"] for s in picked]
    assert all(n in ["张三", "李四", "王五", "赵六", "钱七"] for n in names)

    step(25, "删除作业 → records 级联")
    r = client.delete(f"/homeworks/{hw_id}", headers=auth)
    assert r.status_code in (200, 204)
    r = client.get(f"/homeworks/{hw_id}", headers=auth)
    assert r.status_code == 404

    step(26, "权限校验：另一老师无法访问别人的科目")
    other = f"other_{suffix}"
    client.post("/auth/register", json={"username": other, "password": "test123", "display_name": "B"})
    r2 = client.post("/auth/login", data={"username": other, "password": "test123"},
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    other_token = r2.json()["access_token"]
    other_auth = {"Authorization": f"Bearer {other_token}"}
    r = client.patch(f"/subjects/{subj_yuwen}", json={"name": "X"}, headers=other_auth)
    print(f"  跨老师改科目: {r.status_code}")
    assert r.status_code in (403, 404)

    print("\n=== 迭代 2 全部 26 步通过 ===")


if __name__ == "__main__":
    main()
