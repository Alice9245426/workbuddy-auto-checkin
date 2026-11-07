#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WorkBuddy 云端每日签到（GitHub Actions 专用）。

只依赖 Python 标准库，从环境变量读取 token/uid/domain，调用官方接口完成签到。

功能：
- 幂等签到：先查当天状态，已签则跳过，不会重复领取。
- 可选 token 自动续期：设置 WB_REFRESH_TOKEN 后，签到前先用 refreshToken 刷新
  accessToken（把云端有效期从 30 天延长到约 60 天；刷新失败时自动回退用原 token）。
- 可选结果通知：设置通知环境变量后，签到结果推送到 Telegram / Server酱 / 通用 webhook。

全程不打印 token / refreshToken。
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
REFRESH_EP = "/v2/auth/token/refresh"

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


def _post(path, headers, body=b"{}"):
    req = urllib.request.Request(ENDPOINT + path, data=body, headers=headers, method="POST")
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


def _post_external(url, payload):
    """向外部通知服务发 POST JSON（失败静默忽略，不阻断签到主流程）。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=15, context=ctx):
        pass


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


def _refresh_token(refresh_token, access_token, uid, domain):
    """用 refreshToken 刷新 accessToken，返回 (新 accessToken, 新 refreshToken)。

    刷新接口从客户端逆向而来：POST /v2/auth/token/refresh，body 空对象，
    请求头额外带 X-Refresh-Token + X-Auth-Refresh-Source: plugin。
    失败返回 (None, None)，由调用方回退到原 token。
    """
    h = _headers(access_token, uid, domain)
    h["X-Refresh-Token"] = refresh_token
    h["X-Auth-Refresh-Source"] = "plugin"
    code, body = _post(REFRESH_EP, h)
    if code != 200:
        return None, None
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        data = body
    new_access = data.get("accessToken")
    new_refresh = data.get("refreshToken")
    return (new_access or None), (new_refresh or None)


def _notify(title, body_text):
    """把结果推送到配置好的通知渠道（都配置了则都推，互不冲突）。"""
    # Telegram
    bot = (os.environ.get("TG_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TG_CHAT_ID") or "").strip()
    if bot and chat:
        try:
            _post_external(
                "https://api.telegram.org/bot%s/sendMessage" % bot,
                {"chat_id": chat, "text": title + "\n" + body_text},
            )
        except Exception:
            pass
    # Server酱（微信推送）
    sckey = (os.environ.get("SERVERCHAN_KEY") or "").strip()
    if sckey:
        try:
            _post_external(
                "https://sctapi.ftqq.com/%s.send" % sckey,
                {"title": title, "desp": body_text},
            )
        except Exception:
            pass
    # 通用 webhook（POST 原始 JSON 文本）
    webhook = (os.environ.get("NOTIFY_WEBHOOK") or "").strip()
    if webhook:
        try:
            _post_external(webhook, {"title": title, "text": body_text})
        except Exception:
            pass


def main():
    token = (os.environ.get("WB_TOKEN") or "").strip()
    uid = (os.environ.get("WB_UID") or "").strip()
    domain = (os.environ.get("WB_DOMAIN") or "").strip()
    refresh = (os.environ.get("WB_REFRESH_TOKEN") or "").strip()
    if not token:
        print(json.dumps({"ok": False, "error": "WB_TOKEN 未设置"}, ensure_ascii=False))
        _notify("WorkBuddy 签到失败", "WB_TOKEN 未设置")
        return 2

    # 0. 可选：先刷新 accessToken
    refreshed = False
    if refresh:
        new_access, _new_refresh = _refresh_token(refresh, token, uid, domain)
        if new_access:
            token = new_access
            refreshed = True

    now = datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M:%S")
    h = _headers(token, uid, domain)

    # 1. 查当天签到状态
    st_code, st = _post(STATUS_EP, h)
    if st_code != 200 or _pick(st, "code") not in (0, "0", None):
        msg = "状态查询失败 (http=%s)" % st_code
        print(json.dumps({"ok": False, "error": msg, "body": st}, ensure_ascii=False))
        _notify("WorkBuddy 签到失败", msg)
        return 3

    checked = bool(_pick(st, "today_checked_in", "todayCheckedIn") or False)
    streak = _pick(st, "streak_days", "streakDays")
    total = _pick(st, "total_credits", "totalCredits")

    if checked:
        msg = "今日已签到（连签 %s 天，累计 %s 积分）" % (streak, total)
        print(json.dumps({
            "ok": True, "action": "skip", "message": "今天已签到",
            "streak_days": streak, "total_credits": total,
            "refreshed": refreshed, "time": now,
        }, ensure_ascii=False))
        _notify("WorkBuddy 签到（已签）", msg)
        return 0

    # 2. 执行签到
    ck_code, ck = _post(CHECKIN_EP, h)
    ck_code_num = _pick(ck, "code")
    if ck_code == 200 and ck_code_num in (0, "0", None):
        gained = _pick(ck, "today_credit", "credit", "points", "reward") or _pick(st, "today_credit", "daily_credit")
        msg = "签到成功：+%s 积分（连签 %s 天）" % (gained, _pick(ck, "streak_days") or streak)
        print(json.dumps({
            "ok": True, "action": "checkin", "message": "签到成功",
            "today_credit": gained, "streak_days": _pick(ck, "streak_days") or streak,
            "refreshed": refreshed, "time": now,
        }, ensure_ascii=False))
        _notify("WorkBuddy 签到成功", msg)
        return 0
    elif ck_code_num == 10001 or "已签到" in str(_pick(ck, "msg", "message") or ""):
        msg = "今日已签到（幂等跳过）"
        print(json.dumps({"ok": True, "action": "skip", "message": msg, "refreshed": refreshed, "time": now}, ensure_ascii=False))
        _notify("WorkBuddy 签到（已签）", msg)
        return 0
    else:
        msg = "签到失败 (http=%s)" % ck_code
        print(json.dumps({"ok": False, "error": msg, "body": ck}, ensure_ascii=False))
        _notify("WorkBuddy 签到失败", msg)
        return 3


if __name__ == "__main__":
    sys.exit(main())
