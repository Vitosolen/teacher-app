"""通过 Vite dev server 的 /api 代理走完整业务流，模拟前端真实调用路径。"""
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
    username = f"e2e_{suffix}"
    password = "test123"

    step(1, "注册老师")
    r = client.post("/auth/register", json={
        "username": username, "password": password, "display_name": "E2E 老师"
    })
    print("status:", r.status_code)
    assert r.status_code in (200, 201), r.text

    step(2, "登录获取 JWT (form-urlencoded)")
    r = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    print("token len:", len(token))
    auth = {"Authorization": f"Bearer {token}"}

    step(3, "获取当前老师 /auth/me")
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200, r.text
    print("display_name:", r.json()["display_name"])

    step(4, "创建班级")
    r = client.post("/classes", json={"name": "E2E 五年级三班", "grade": "五年级"}, headers=auth)
    assert r.status_code in (200, 201), r.text
    class_id = r.json()["id"]
    print("class_id:", class_id)

    step(5, "班级列表（含 student_count）")
    r = client.get("/classes", headers=auth)
    classes = r.json()
    me_class = [c for c in classes if c["id"] == class_id][0]
    print("name=", me_class["name"], "count=", me_class["student_count"])
    assert me_class["student_count"] == 0

    step(6, "批量导入 5 名学生")
    r = client.post(
        f"/classes/{class_id}/students/batch",
        json={"names": ["张三", "李四", "王五", "赵六", "钱七"]},
        headers=auth,
    )
    assert r.status_code in (200, 201), r.text
    students = r.json()
    assert len(students) == 5
    for s in students:
        assert s["pet"] is not None
        assert s["pet"]["level"] == 1
    zhangsan = [s for s in students if s["name"] == "张三"][0]
    lisi = [s for s in students if s["name"] == "李四"][0]
    print("张三 pet:", zhangsan["pet"]["name"], "Lv", zhangsan["pet"]["level"])

    step(7, "给张三 +5（学习积极）")
    r = client.post("/behaviors", json={
        "student_id": zhangsan["id"], "score": 5, "category": "学习", "reason": "课堂积极发言"
    }, headers=auth)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    print("pet:", j["pet"]["exp"], "exp,", j["pet"]["mood"], "mood,", j["pet"]["hunger"], "hunger")
    assert j["pet"]["exp"] == 50
    assert j["pet"]["mood"] == 100  # 80 + 5*5 = 105，封顶 100
    assert j["pet"]["hunger"] == 75  # 60 + 5*3 = 75

    step(8, "连续 +10 +10 +10，触发升级")
    pet_state = None
    for i in range(3):
        r = client.post("/behaviors", json={
            "student_id": zhangsan["id"], "score": 10, "category": "学习", "reason": f"作业优秀 {i+1}"
        }, headers=auth)
        pet_state = r.json()["pet"]
        print(f"  第 {i+1} 次：Lv{pet_state['level']}, exp={pet_state['exp']}, leveled_up={r.json()['leveled_up']}")
    assert pet_state["level"] >= 2, f"应升至少 1 级，实际 Lv{pet_state['level']}"

    step(9, "给李四 -5（违纪）")
    r = client.post("/behaviors", json={
        "student_id": lisi["id"], "score": -5, "category": "纪律", "reason": "课堂讲话"
    }, headers=auth)
    j = r.json()
    print("李四 pet:", "exp=", j["pet"]["exp"], "mood=", j["pet"]["mood"], "hunger=", j["pet"]["hunger"])
    assert j["pet"]["exp"] == 0  # 减分不扣经验
    assert j["pet"]["mood"] == 55  # 80 + (-5)*5 = 55
    assert j["pet"]["hunger"] == 50  # 60 + (-5)*2 = 50

    step(10, "继续给李四 -10，验证 status 转为难过/虚弱")
    r = client.post("/behaviors", json={
        "student_id": lisi["id"], "score": -10, "category": "纪律", "reason": "顶撞老师"
    }, headers=auth)
    j = r.json()
    print("李四 status:", j["pet"]["status"], "mood=", j["pet"]["mood"])
    assert j["pet"]["status"] in ("难过", "虚弱"), f"unexpected status: {j['pet']['status']}"

    step(11, "查李四的行为时间线（应有 2 条）")
    r = client.get(f"/students/{lisi['id']}/behaviors", headers=auth)
    bs = r.json()
    print("count:", len(bs))
    assert len(bs) == 2

    step(12, "改宠物名")
    pet_id = zhangsan["pet"]["id"]
    r = client.patch(f"/pets/{pet_id}", json={"name": "小龙"}, headers=auth)
    assert r.status_code in (200, 201), r.text
    print("renamed:", r.json()["name"])
    assert r.json()["name"] == "小龙"

    step(13, "权限校验：未带 token 401")
    r = client.get("/classes")
    print("status:", r.status_code)
    assert r.status_code in (401, 403)

    step(14, "权限校验：另一个老师无法访问别人的班级")
    other_user = f"other_{suffix}"
    client.post("/auth/register", json={"username": other_user, "password": password, "display_name": "B"})
    r2 = client.post("/auth/login", data={"username": other_user, "password": password},
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    other_token = r2.json()["access_token"]
    r = client.get(f"/classes/{class_id}/students", headers={"Authorization": f"Bearer {other_token}"})
    print("status:", r.status_code)
    assert r.status_code in (403, 404)

    step(15, "删除学生 -> 宠物级联删除（再 GET 应 404）")
    r = client.delete(f"/students/{zhangsan['id']}", headers=auth)
    assert r.status_code in (200, 204), r.text
    r = client.get(f"/students/{zhangsan['id']}", headers=auth)
    print("get deleted student:", r.status_code)
    assert r.status_code == 404

    step(16, "删除班级 -> 全部学生与宠物级联")
    r = client.delete(f"/classes/{class_id}", headers=auth)
    assert r.status_code in (200, 204)
    r = client.get(f"/classes/{class_id}/students", headers=auth)
    print("after delete:", r.status_code)
    assert r.status_code in (403, 404)

    print("\n=== 全部 16 步通过（经 Vite 代理实际调通前后端链路）===")


if __name__ == "__main__":
    main()
