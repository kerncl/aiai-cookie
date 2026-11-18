"""Smoke-test the running site over real HTTP.

Start the app first (python app.py), then:  python scripts/smoke.py
Exits non-zero if anything is wrong, so CI can use it as a gate.
"""

import json
import re
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5000"
failures = []


def get(path: str) -> str:
    with urllib.request.urlopen(BASE + path) as r:
        return r.read().decode("utf-8")


def names(html: str) -> list[str]:
    """Cookie names only — scoped to cards so the empty-state heading doesn't count."""
    return re.findall(r'<div class="cookie-body">\s*<h2 lang="zh-CN">([^<]+)</h2>', html)


def check(label: str, got, want) -> None:
    ok = got == want
    failures.append(label) if not ok else None
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got}")
        print(f"        want: {want}")


print("=== Catalogue ===")
home = get("/")
zh = names(home)
en = re.findall(r'class="name-en" lang="en">([^<]+)<', home)
for a, b in zip(zh, en):
    print(f"  {a:<6} {b}")
check("7 cookies listed", len(zh), 7)

print("\n=== Allergen filters ===")
check(
    "hide 花生 peanut drops 花生酥",
    names(get("/?exclude=peanut")),
    ["牛油曲奇", "杏仁饼", "鸡蛋卷", "核桃桃酥", "绿豆糕", "芝麻薄脆"],
)
check(
    "hide 麸质+坚果 leaves only 绿豆糕",
    names(get("/?exclude=gluten&exclude=tree-nut")),
    ["绿豆糕"],
)
check(
    "hide 奶制品+鸡蛋 (dairy+egg)",
    names(get("/?exclude=dairy&exclude=egg")),
    ["杏仁饼", "花生酥", "绿豆糕"],
)

print("\n=== Search ===")
check(
    "Chinese ingredient 芝麻 finds both sesame users",
    names(get("/?q=" + urllib.parse.quote("芝麻"))),
    ["核桃桃酥", "芝麻薄脆"],
)
check("English 'walnut' finds 核桃桃酥", names(get("/?q=walnut")), ["核桃桃酥"])
# 杏仁饼 is made with 绿豆粉, so searching 绿豆 should surface it too — the search
# reads ingredients, not just names, which is the whole point.
check(
    "绿豆 finds 绿豆糕 AND 杏仁饼 (made with 绿豆粉)",
    names(get("/?q=" + urllib.parse.quote("绿豆"))),
    ["杏仁饼", "绿豆糕"],
)
check("no match yields empty", names(get("/?q=zzzz")), [])

print("\n=== Detail page: 核桃桃酥 ===")
d = get("/cookie/walnut-crumble")
ing_zh = re.findall(r'<span lang="zh-CN">([^<]+)</span>\s*<span class="ing-en"', d)
ing_en = re.findall(r'class="ing-en" lang="en">([^<]+)<', d)
for a, b in zip(ing_zh, ing_en):
    print(f"  {a:<5} {b}")
check("7 ingredients, both languages", (len(ing_zh), len(ing_en)), (7, 7))
check(
    "allergens listed",
    re.findall(r'tag-allergen">([^<]+?)\s*<span', d),
    ["麸质", "鸡蛋", "坚果", "芝麻"],
)

print("\n=== Pork-free / dietary ===")
almond = get("/cookie/almond-cookie")
# Substring checks are useless here: the page legitimately says 不含猪油, which
# contains 猪油. Pull the actual ingredient names and assert against those.
almond_ings = re.findall(r'<span lang="zh-CN">([^<]+)</span>\s*<span class="ing-en"', almond)
print(f"  配料: {'、'.join(almond_ings)}")
check("猪油 is not an ingredient of 杏仁饼", "猪油" not in almond_ings, True)
check("植物酥油 replaced it", "植物酥油" in almond_ings, True)
check("无猪油 marker on the detail page", "无猪油" in almond, True)
check("无猪油 tag on every card", home.count('tag tag-diet'), 7)
check("pork-free filter keeps all 7", len(names(get("/?dietary=pork-free"))), 7)
check(
    "dietary + allergen filters compose",
    names(get("/?dietary=pork-free&exclude=gluten&exclude=tree-nut")),
    ["绿豆糕"],
)

print("\n=== Allergen-free cookie shows the positive label ===")
check("绿豆糕 marked allergen-free", "不含八大类主要过敏原" in get("/cookie/mung-bean-cake"), True)

print("\n=== API encoding ===")
api = json.loads(get("/api/cookies"))
print(f"  {api[0]['name_zh']} / {api[0]['name_en']} | {api[0]['unit_zh']} | RM{api[0]['price']:.2f}")
raw = get("/api/cookies")
check("API serves real Chinese, not escapes", "\\u" not in raw, True)

print("\n=== Misc ===")
check("price renders as RM28.90", "RM28.90" in home, True)
check("no stray yen symbol left", "¥" not in home, True)
check("sold-out badge present", "售罄" in home, True)
check("lang is zh-CN", 'lang="zh-CN"' in home, True)

print()
if failures:
    print(f"{len(failures)} FAILURE(S): " + ", ".join(failures))
    sys.exit(1)
print("ALL GREEN")
