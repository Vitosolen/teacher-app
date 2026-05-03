"""成绩登记 + 作业订正 E2E"""
import sys, io, time, httpx
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:5173/api/v1"


def step(n, desc):
    print(f"\n[{n}] {desc}")


def main():
    client = httpx.Client(base_url=BASE, timeout=10.0)
    suffix = str(int(time.time()))

    client.post("/auth/register", json={
        "username": f"gc_{suffix}", "password": "test123", "display_name": "GC"
    })
    r = client.post("/auth/login",
                    data={"username": f"gc_{suffix}", "password": "test123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    cid = client.post("/classes", json={"name": "GC 班"}, headers=auth).json()["id"]
    sid = client.post(f"/classes/{cid}/students/batch",
                      json={"names": ["小张", "小李"]}, headers=auth).json()
    z, l = sid[0], sid[1]
    sub_id = client.post("/subjects", json={"name": "语文"}, headers=auth).json()["id"]

    step(1, "创建作业 → type 默认 homework")
    r = client.post("/homeworks", json={
        "class_id": cid, "subject_id": sub_id,
        "title": "作业 1", "content": "造句",
    }, headers=auth)
    hw = r.json()
    print(f"  type={hw['type']}, total={hw['total_count']}, pending_correct={hw['correction_pending_count']}")
    assert hw["type"] == "homework"
    assert hw["total_count"] == 2
    assert hw["correction_pending_count"] == 0
    hw_id = hw["id"]

    step(2, "创建成绩 → type=exam")
    r = client.post("/homeworks", json={
        "class_id": cid, "subject_id": sub_id,
        "type": "exam", "title": "2025 期中考", "content": "满分 100",
    }, headers=auth)
    exam = r.json()
    print(f"  type={exam['type']}, title={exam['title']}")
    assert exam["type"] == "exam"
    exam_id = exam["id"]

    step(3, "GET /homeworks?type=homework → 仅作业")
    r = client.get("/homeworks?type=homework", headers=auth)
    types = [h["type"] for h in r.json()]
    print(f"  types: {types}")
    assert all(t == "homework" for t in types)

    step(4, "GET /homeworks?type=exam → 仅成绩")
    r = client.get("/homeworks?type=exam", headers=auth)
    types = [h["type"] for h in r.json()]
    print(f"  types: {types}")
    assert all(t == "exam" for t in types)

    step(5, "批改作业小张 95 分（A+）→ needs_correction=False")
    detail = client.get(f"/homeworks/{hw_id}", headers=auth).json()
    rec_z = next(r for r in detail["records"] if r["student_name"] == "小张")
    rec_l = next(r for r in detail["records"] if r["student_name"] == "小李")
    r = client.patch(f"/homework-records/{rec_z['id']}", json={
        "score": 95, "comment": "Good",
    }, headers=auth)
    print(f"  小张 needs={r.json()['needs_correction']}, corrected={r.json()['corrected']}")
    assert r.json()["needs_correction"] is False
    assert r.json()["corrected"] is False

    step(6, "批改作业小李 75 分（<90）→ needs_correction=True")
    r = client.patch(f"/homework-records/{rec_l['id']}", json={
        "score": 75, "comment": "需订正",
    }, headers=auth)
    print(f"  小李 needs={r.json()['needs_correction']}, corrected={r.json()['corrected']}")
    assert r.json()["needs_correction"] is True
    assert r.json()["corrected"] is False

    step(7, "GET 作业列表 → correction_pending_count=1")
    r = client.get(f"/homeworks?type=homework", headers=auth)
    hw_now = next(h for h in r.json() if h["id"] == hw_id)
    print(f"  pending_correct={hw_now['correction_pending_count']}")
    assert hw_now["correction_pending_count"] == 1

    step(8, "标记小李已订正 → corrected=True, pending=0")
    r = client.patch(f"/homework-records/{rec_l['id']}", json={"corrected": True}, headers=auth)
    print(f"  小李 corrected={r.json()['corrected']}, corrected_at={r.json()['corrected_at']}")
    assert r.json()["corrected"] is True
    assert r.json()["corrected_at"] is not None
    r = client.get(f"/homeworks?type=homework", headers=auth)
    hw_now = next(h for h in r.json() if h["id"] == hw_id)
    print(f"  pending_correct now={hw_now['correction_pending_count']}")
    assert hw_now["correction_pending_count"] == 0

    step(9, "重新批改小李改成 60 分 → 已订正状态自动重置")
    r = client.patch(f"/homework-records/{rec_l['id']}", json={"score": 60}, headers=auth)
    j = r.json()
    print(f"  needs={j['needs_correction']}, corrected={j['corrected']}")
    assert j["needs_correction"] is True
    assert j["corrected"] is False  # 重新批改重置

    step(10, "登记成绩：小张 92、小李 78 → 不触发 needs_correction（type=exam）")
    edetail = client.get(f"/homeworks/{exam_id}", headers=auth).json()
    erec_z = next(r for r in edetail["records"] if r["student_name"] == "小张")
    erec_l = next(r for r in edetail["records"] if r["student_name"] == "小李")
    r = client.patch(f"/homework-records/{erec_z['id']}", json={"score": 92}, headers=auth)
    assert r.json()["needs_correction"] is False
    r = client.patch(f"/homework-records/{erec_l['id']}", json={"score": 78}, headers=auth)
    print(f"  小李 exam needs={r.json()['needs_correction']} (应 False，考试不订正)")
    assert r.json()["needs_correction"] is False

    step(11, "成绩列表 correction_pending_count 始终 0（考试不算订正）")
    r = client.get(f"/homeworks?type=exam", headers=auth)
    e_now = next(h for h in r.json() if h["id"] == exam_id)
    print(f"  exam pending_correct={e_now['correction_pending_count']}")
    assert e_now["correction_pending_count"] == 0

    step(12, "type 非法 → 400")
    r = client.post("/homeworks", json={
        "class_id": cid, "subject_id": sub_id, "type": "invalid", "title": "x",
    }, headers=auth)
    print(f"  status={r.status_code}")
    assert r.status_code == 400

    print("\n=== 成绩登记 + 作业订正 12 步通过 ===")


if __name__ == "__main__":
    main()
