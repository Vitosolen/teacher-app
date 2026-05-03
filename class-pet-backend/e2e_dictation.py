"""单词听写功能端到端验证（经 Vite 代理）"""
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
    username = f"dict_{suffix}"

    step(1, "注册并登录")
    client.post("/auth/register", json={
        "username": username, "password": "test123", "display_name": "听写老师"
    })
    r = client.post("/auth/login",
                    data={"username": username, "password": "test123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    step(2, "新建词库「Unit 1 学校用品」（en-US）")
    r = client.post("/word-groups", json={
        "name": "Unit 1 学校用品", "description": "五年级上册",
        "lang": "en-US", "sort_order": 1,
    }, headers=auth)
    assert r.status_code in (200, 201), r.text
    g = r.json()
    print(f"  id={g['id']}, lang={g['lang']}, word_count={g['word_count']}")
    assert g["word_count"] == 0
    gid = g["id"]

    step(3, "重复创建同名词库 → 应 400")
    r = client.post("/word-groups", json={"name": "Unit 1 学校用品", "lang": "en-US"}, headers=auth)
    assert r.status_code == 400

    step(4, "批量导入 6 个单词（含混合分隔符格式）")
    r = client.post(f"/word-groups/{gid}/words/batch", json={
        "lines": [
            "apple 苹果",
            "banana,香蕉",
            "cat\t猫",
            "dog",
            "  pencil  铅笔  ",
            "",  # 空行应被忽略
        ],
    }, headers=auth)
    assert r.status_code in (200, 201), r.text
    created = r.json()
    print(f"  导入数: {len(created)}")
    assert len(created) == 5  # 空行不算
    cat = next(w for w in created if w["text"] == "cat")
    assert cat["translation"] == "猫"
    dog = next(w for w in created if w["text"] == "dog")
    assert dog["translation"] == ""

    step(5, "GET 词库详情 → 验证 word_count + words 列表")
    r = client.get(f"/word-groups/{gid}", headers=auth)
    detail = r.json()
    print(f"  word_count={detail['word_count']}, words={[w['text'] for w in detail['words']]}")
    assert detail["word_count"] == 5
    assert len(detail["words"]) == 5

    step(6, "单条新增「orange 橙子」")
    r = client.post(f"/word-groups/{gid}/words", json={
        "text": "orange", "translation": "橙子",
    }, headers=auth)
    assert r.status_code in (200, 201)
    orange_id = r.json()["id"]

    step(7, "PATCH 编辑「dog」 → 加上释义「狗」")
    r = client.patch(f"/words/{dog['id']}", json={"translation": "狗"}, headers=auth)
    assert r.json()["translation"] == "狗"

    step(8, "PATCH 编辑词库 → 改名「Unit 1 文具」、改 lang 到 en-GB")
    r = client.patch(f"/word-groups/{gid}", json={
        "name": "Unit 1 文具", "lang": "en-GB",
    }, headers=auth)
    assert r.json()["name"] == "Unit 1 文具"
    assert r.json()["lang"] == "en-GB"

    step(9, "GET 词库列表 → 1 个词库 + 6 个单词")
    r = client.get("/word-groups", headers=auth)
    groups = r.json()
    assert len(groups) == 1
    assert groups[0]["word_count"] == 6
    print(f"  '{groups[0]['name']}' word_count={groups[0]['word_count']}")

    step(10, "删除单词 orange → 词库剩 5 个")
    r = client.delete(f"/words/{orange_id}", headers=auth)
    assert r.status_code in (200, 204)
    r = client.get(f"/word-groups/{gid}", headers=auth)
    assert r.json()["word_count"] == 5

    step(11, "权限校验：另一老师无法访问别人的词库")
    other = f"other_{suffix}"
    client.post("/auth/register", json={"username": other, "password": "test123", "display_name": "B"})
    r2 = client.post("/auth/login", data={"username": other, "password": "test123"},
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    other_auth = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    r = client.get(f"/word-groups/{gid}", headers=other_auth)
    print(f"  跨老师查看: {r.status_code}")
    assert r.status_code in (403, 404)
    r = client.post(f"/word-groups/{gid}/words", json={"text": "x"}, headers=other_auth)
    print(f"  跨老师写入: {r.status_code}")
    assert r.status_code in (403, 404)

    step(12, "删除词库 → 单词级联删除")
    r = client.delete(f"/word-groups/{gid}", headers=auth)
    assert r.status_code in (200, 204)
    r = client.get(f"/word-groups/{gid}", headers=auth)
    assert r.status_code == 404

    print("\n=== 单词听写 12 步通过 ===")


if __name__ == "__main__":
    main()
