"""端到端 smoke test：覆盖完整业务流"""
import sys
import io
import httpx

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "http://127.0.0.1:8000/api/v1"


def banner(title):
    print(f"\n=== {title} ===")


def main():
    client = httpx.Client(base_url=BASE, timeout=10.0)

    banner("1. 注册老师")
    # 用唯一用户名避免重复注册冲突
    import time
    uname = f"smoke_{int(time.time())}"
    r = client.post("/auth/register", json={
        "username": uname, "password": "123456", "display_name": "烟雾测试老师"
    })
    print(r.status_code, r.json())
    assert r.status_code == 201

    banner("2. 登录")
    r = client.post("/auth/login", data={"username": uname, "password": "123456"})
    print(r.status_code, "token =", r.json()["access_token"][:30] + "...")
    assert r.status_code == 200
    token = r.json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    banner("3. /me 验证 token")
    r = client.get("/auth/me", headers=H)
    print(r.status_code, r.json())
    assert r.status_code == 200

    banner("4. 创建班级")
    r = client.post("/classes", headers=H, json={"name": "六年级二班", "grade": "六年级"})
    print(r.status_code, r.json())
    assert r.status_code == 201
    cid = r.json()["id"]

    banner("5. 批量加学生")
    r = client.post(f"/classes/{cid}/students/batch", headers=H,
                    json={"names": ["张三", "李四", "王五"]})
    print(r.status_code)
    students = r.json()
    for s in students:
        p = s["pet"]
        print(f"  {s['name']}: {p['name']} L{p['level']} h={p['hunger']} m={p['mood']}")
    assert len(students) == 3
    assert all(s["pet"] is not None for s in students)
    sid_zhang = next(s["id"] for s in students if s["name"] == "张三")
    sid_li = next(s["id"] for s in students if s["name"] == "李四")
    sid_wang = next(s["id"] for s in students if s["name"] == "王五")

    banner("6. 张三 +10 学习积极")
    r = client.post("/behaviors", headers=H, json={
        "student_id": sid_zhang, "score": 10, "category": "学习", "reason": "主动回答"
    })
    print(r.status_code)
    p = r.json()["pet"]
    print(f"  L{p['level']} exp={p['exp']}/{p['exp_to_next_level']} h={p['hunger']} m={p['mood']} status={p['status']} leveled_up={r.json()['leveled_up']}")
    assert p["mood"] == 100  # 80 + 10*5 -> capped
    assert p["hunger"] == 90  # 60 + 10*3 -> capped at 100? 60+30=90
    assert r.json()["leveled_up"] is True  # 100 exp 直接升一级
    assert p["level"] == 2

    banner("7. 张三 +10 再来一次（验证多次累积）")
    r = client.post("/behaviors", headers=H, json={
        "student_id": sid_zhang, "score": 10, "category": "学习", "reason": "作业全对"
    })
    p = r.json()["pet"]
    print(f"  L{p['level']} exp={p['exp']}/{p['exp_to_next_level']} h={p['hunger']} m={p['mood']}")
    # exp = 100, level 2 阈值 = 200，不升级
    assert p["level"] == 2
    assert p["exp"] == 100

    banner("8. 李四 -5 违纪")
    r = client.post("/behaviors", headers=H, json={
        "student_id": sid_li, "score": -5, "category": "纪律", "reason": "上课讲话"
    })
    p = r.json()["pet"]
    print(f"  L{p['level']} exp={p['exp']} h={p['hunger']} m={p['mood']} status={p['status']}")
    assert p["exp"] == 0  # 减分不扣经验
    assert p["mood"] == 80 + (-5) * 5  # 55
    assert p["hunger"] == 60 + (-5) * 2  # 50

    banner("9. 王五 -10 把心情打到虚弱")
    r = client.post("/behaviors", headers=H, json={
        "student_id": sid_wang, "score": -10, "category": "纪律", "reason": "严重违纪"
    })
    p = r.json()["pet"]
    print(f"  L{p['level']} h={p['hunger']} m={p['mood']} status={p['status']}")
    # mood = 80 - 50 = 30 -> 难过；hunger = 60 - 20 = 40
    assert p["mood"] == 30
    assert p["status"] == "难过"

    banner("10. 张三的行为时间线")
    r = client.get(f"/students/{sid_zhang}/behaviors", headers=H)
    print(r.status_code, f"behaviors={len(r.json())}")
    for b in r.json():
        print(f"  [{b['category']}] {b['score']:+d} {b['reason']}")
    assert len(r.json()) == 2

    banner("11. 班级学生列表（最终状态）")
    r = client.get(f"/classes/{cid}/students", headers=H)
    for s in r.json():
        p = s["pet"]
        print(f"  {s['name']}: L{p['level']} exp={p['exp']} h={p['hunger']} m={p['mood']} ({p['status']})")

    banner("12. 删除班级（连带级联删）")
    r = client.delete(f"/classes/{cid}", headers=H)
    assert r.status_code == 204
    print("  204 No Content")

    banner("13. 验证已删除（再读应 404 或空列表）")
    r = client.get(f"/classes/{cid}/students", headers=H)
    print(f"  GET /classes/{cid}/students -> {r.status_code}")
    assert r.status_code == 404

    banner("14. 权限边界：他人无法操作我的资源")
    # 注册第二个老师
    uname2 = uname + "_other"
    client.post("/auth/register", json={
        "username": uname2, "password": "123456", "display_name": "他人"
    })
    r = client.post("/auth/login", data={"username": uname2, "password": "123456"})
    H2 = {"Authorization": f"Bearer {r.json()['access_token']}"}
    # 第一个老师再建一个班级，第二个老师不能删
    r = client.post("/classes", headers=H, json={"name": "私有班"})
    cid_priv = r.json()["id"]
    r = client.delete(f"/classes/{cid_priv}", headers=H2)
    print(f"  其他老师删别人班级 -> {r.status_code}")
    assert r.status_code == 403
    # 清理
    client.delete(f"/classes/{cid_priv}", headers=H)

    print("\n✅ 所有 14 步全部通过")


if __name__ == "__main__":
    main()
