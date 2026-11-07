#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WorkBuddy 云端每日签到（GitHub Actions 专用）。

只依赖 Python 标准库，从环境变量读取 token/uid/domain，调用官方接口完成签到。
幂等：先查状态，今天已签则直接跳过。全程不打印 token。
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

ENDPOINT = "https://copilot.tencent.com"
STATUS_EP = "/v2/billing/meter/checkin-activity-status"
CHECKIN_EP = "/v2/billing/meter/daily-checkin"

BEIJING = timezone(timedelta(hours=8))


def _headers(token, uid, domain):
    h = {
        "Accept": "application/json",
        "Authorization": "Bearer %s" % token,
        "Content-Type": "application/json",
        "X-User-Id": uid or "",
        "User-Agent": "WorkBuddy",
    }
    if domain:
        h["X-Domain"] = domain
    return h


def _post(path, headers):
    req = urllib.request.Request(ENDPOINT + path, data=b"{}", headers=headers, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:300]}
    except Exception as e:
        return -1, {"error": str(e)}


def _pick(obj, *keys):
    if isinstance(obj, dict):
        for k in keys:
            if obj.get(k) not in (None, "", []):
                return obj.get(k)
        for v in obj.values():
            r = _pick(v, *keys)
            if r not in (None, ""):
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _pick(v, *keys)
            if r not in (None, ""):
                return r
    return None


def main():
    token = (os.environ.get("WB_TOKEN") or "").strip()
    uid = (os.environ.get("WB_UID") or "").strip()
    domain = (os.environ.get("WB_DOMAIN") or "").strip()
    if not token:
        print(json.dumps({"ok": False, "error": "WB_TOKEN 未设置"}, ensure_ascii=False))
        return 2

    now = datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M:%S")
    h = _headers(token, uid, domain)

    # 1. 查状态
    st_code, st = _post(STATUS_EP, h)
    if st_code != 200 or _pick(st, "code") not in (0, "0", None):
        print(json.dumps({"ok": False, "error": "状态查询失败", "http": st_code, "body": st}, ensure_ascii=False))
        return 3

    checked = bool(_pick(st, "today_checked_in", "todayCheckedIn") or False)
    streak = _pick(st, "streak_days", "streakDays")
    total = _pick(st, "total_credits", "totalCredits")

    if checked:
        print(json.dumps({
            "ok": True, "action": "skip", "message": "今天已签到",
            "streak_days": streak, "total_credits": total, "time": now,
        }, ensure_ascii=False))
        return 0

    # 2. 签到
    ck_code, ck = _post(CHECKIN_EP, h)
    ck_code_num = _pick(ck, "code")
    if ck_code == 200 and ck_code_num in (0, "0", None):
        gained = _pick(ck, "today_credit", "credit", "points", "reward") or _pick(st, "today_credit", "daily_credit")
        print(json.dumps({
            "ok": True, "action": "checkin", "message": "签到成功",
            "today_credit": gained, "streak_days": _pick(ck, "streak_days") or streak,
            "time": now,
        }, ensure_ascii=False))
        return 0
    elif ck_code_num == 10001 or "已签到" in str(_pick(ck, "msg", "message") or ""):
        print(json.dumps({"ok": True, "action": "skip", "message": "今天已签到（幂等）", "time": now}, ensure_ascii=False))
        return 0
    else:
        print(json.dumps({"ok": False, "error": "签到失败", "http": ck_code, "body": ck}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main())
