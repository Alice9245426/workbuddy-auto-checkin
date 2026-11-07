#!/usr/bin/env python3
"""WorkBuddy 登录信息提取脚本（用于配置 GitHub Actions 云端签到）

本脚本读取本机 WorkBuddy 桌面端的登录态，通过客户端运行时在内存中解密
accessToken / refreshToken，并打印 uid / domain，供配置云端签到的 GitHub Secrets 使用。

作者：本项目贡献者
解密逻辑参考 88lin/workbuddy-auto-signin（MIT）：
  https://github.com/88lin/workbuddy-auto-signin

用法：
  python extract_token.py            # 提取 uid/domain，token 写入文件（不打印明文）
  python extract_token.py --print    # 额外把 token 完整打印到终端（注意终端历史泄露风险）

安全说明：
  - 全程不联网、不修改任何文件（只新增两个 txt）。
  - token 默认不打印到终端，只写入本地 txt 文件，用完记得删除。
  - 解密通过 WorkBuddy 客户端原生接口在内存中完成，密钥不落盘。
"""

import base64
import json
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# 以下 AUTH_HELPER_JS 与运行时探测逻辑，参考 88lin/workbuddy-auto-signin（MIT）
# 作用：以 ELECTRON_RUN_AS_NODE 方式启动 WorkBuddy.exe，调用其原生存储接口
#       loggerGet() 取得 at-rest 密钥，再用 AES-256-GCM 解 envelope（AAD 为 WB-AAD\0）。
# ---------------------------------------------------------------------------

AUTH_HELPER_JS = r"""
'use strict';
const crypto = require('crypto');
const inputLimit = 65536;
const failure = reason => { throw {reason}; };
const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
function base64(value, length) {
  if (typeof value !== 'string' || value.length > inputLimit) failure('INVALID_FORMAT');
  const bytes = Buffer.from(value, 'base64');
  if (bytes.toString('base64') !== value || (length !== undefined && bytes.length !== length))
    failure('INVALID_FORMAT');
  return bytes;
}
function utf8(bytes) {
  const text = bytes.toString('utf8');
  if (!Buffer.from(text, 'utf8').equals(bytes)) failure('INVALID_FORMAT');
  return text;
}
function decode(value) {
  if (!object(value) || Object.keys(value).sort().join(',') !== '$wbEncrypted,envelope' || value.$wbEncrypted !== 1)
    failure('UNSUPPORTED_ENVELOPE');
  let envelope;
  try { envelope = JSON.parse(utf8(base64(value.envelope))); }
  catch (e) { failure(e.reason || 'INVALID_FORMAT'); }
  if (!object(envelope) || !Number.isInteger(envelope.suite)) failure('INVALID_FORMAT');
  if (envelope.suite !== 1) failure('UNSUPPORTED_ENVELOPE');
  if (Object.keys(envelope).sort().join(',') !== 'authTag,ciphertext,keyId,nonce,suite' ||
      typeof envelope.keyId !== 'string' || !/^[0-9a-f]{16}$/.test(envelope.keyId)) failure('INVALID_FORMAT');
  return {keyId: envelope.keyId, nonce: base64(envelope.nonce, 12),
    tag: base64(envelope.authTag, 16), ciphertext: base64(envelope.ciphertext)};
}
function nativeStorage() {
  try {
    const storage = process._linkedBinding('electron_browser_workbuddy_storage');
    if (typeof storage.loggerGet !== 'function') failure('RUNTIME_UNAVAILABLE');
    return storage;
  } catch (_) { failure('RUNTIME_UNAVAILABLE'); }
}
function decrypt(envelope) {
  let payload;
  try { payload = JSON.parse(nativeStorage().loggerGet()); }
  catch (_) { failure('RUNTIME_UNAVAILABLE'); }
  let key;
  let plaintext;
  try {
    if (!object(payload) || payload.version !== 1) failure('RUNTIME_UNAVAILABLE');
    let secret;
    try { secret = base64(payload.atRestSecretKey, 32); }
    catch (_) { failure('RUNTIME_UNAVAILABLE'); }
    const empty = secret.every(b => b === 0);
    secret.fill(0);
    if (empty) failure('RUNTIME_UNAVAILABLE');
    key = crypto.createHash('sha256').update(payload.atRestSecretKey, 'utf8').digest();
    payload = null;
    if (crypto.createHash('sha256').update(key).digest('hex').slice(0, 16) !== envelope.keyId)
      failure('KEY_MISMATCH');
    const lp = s => {
      const bytes = Buffer.from(s, 'utf8');
      const length = Buffer.alloc(4); length.writeUInt32BE(bytes.length);
      return Buffer.concat([length, bytes]);
    };
    const aad = Buffer.concat([Buffer.from('WB-AAD\0', 'ascii'), Buffer.from([1]),
      lp('WBEV1'), lp('sym-v1'), Buffer.from([0, 0, 0, 1]), lp(envelope.keyId), Buffer.from([2, 0, 0])]);
    try {
      const cipher = crypto.createDecipheriv('aes-256-gcm', key, envelope.nonce, {authTagLength: 16});
      cipher.setAAD(aad); cipher.setAuthTag(envelope.tag);
      plaintext = Buffer.concat([cipher.update(envelope.ciphertext), cipher.final()]);
    } catch (_) { failure('DECRYPT_FAILED'); }
    const token = utf8(plaintext);
    if (!token.length || token.length > 32768 || !/^[A-Za-z0-9._~+\/-]+=*$/.test(token))
      failure('INVALID_FORMAT');
    return token;
  } finally {
    if (key) key.fill(0);
    if (plaintext) plaintext.fill(0);
  }
}
let chunks = [], size = 0;
function reply(value) {
  process.stdout.write(JSON.stringify({version: 1, ...value}), () => process.exit(value.ok ? 0 : 1));
}
process.stdin.on('data', chunk => {
  size += chunk.length;
  if (size > inputLimit) reply({ok: false, reason: 'INVALID_FORMAT'});
  else chunks.push(chunk);
});
process.stdin.on('error', () => reply({ok: false, reason: 'HELPER_PROTOCOL'}));
process.stdin.on('end', () => {
  try {
    const request = JSON.parse(utf8(Buffer.concat(chunks))); chunks = [];
    if (!object(request) || request.version !== 1) failure('HELPER_PROTOCOL');
    if (request.operation === 'probe') {
      nativeStorage();
      if (!crypto.getCiphers().includes('aes-256-gcm')) failure('RUNTIME_UNAVAILABLE');
      reply({ok: true, electron: process.versions.electron || 'unknown'});
    } else if (request.operation === 'decrypt') {
      reply({ok: true, accessToken: decrypt(decode(request.value))});
    } else failure('HELPER_PROTOCOL');
  } catch (e) {
    const reasons = ['INVALID_FORMAT','UNSUPPORTED_ENVELOPE','RUNTIME_UNAVAILABLE',
      'KEY_MISMATCH','DECRYPT_FAILED','HELPER_PROTOCOL'];
    reply({ok: false, reason: reasons.includes(e.reason) ? e.reason : 'HELPER_PROTOCOL'});
  }
});
"""

AUTH_BASENAME = os.path.join("CodeBuddyExtension", "Data", "Public", "auth",
                            "workbuddy-desktop.info")


def _find_session_file():
    override = os.environ.get("WORKBUDDY_AUTH_FILE")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return os.path.join(local, AUTH_BASENAME)
    return os.path.join(os.path.expanduser("~"), "AppData", "Local", AUTH_BASENAME)


def _parse_exe_path(value, is_icon):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.startswith('"'):
        end = value.find('"', 1)
        if end < 0:
            return None
        value = value[1:end]
    elif is_icon:
        # DisplayIcon 形如 C:\...\WorkBuddy.exe,0
        value = value.split(",")[0].strip()
    if is_icon:
        path = value
    else:
        path = os.path.join(value, "WorkBuddy.exe")
    path = os.path.normpath(path)
    if os.path.basename(path).lower() != "workbuddy.exe":
        return None
    return path if os.path.isfile(path) else None


def _windows_registry_runtime():
    """从注册表卸载项探测 WorkBuddy.exe（Windows 专用，装到非默认目录也能找到）。"""
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:
        return None
    subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | view) as root:
                    count = winreg.QueryInfoKey(root)[0]
                    for index in range(count):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, index),
                                                0, winreg.KEY_READ | view) as entry:
                                try:
                                    name = winreg.QueryValueEx(entry, "DisplayName")[0]
                                except OSError:
                                    continue
                                if not isinstance(name, str) or "WorkBuddy" not in name:
                                    continue
                                for field in ("InstallLocation", "DisplayIcon"):
                                    try:
                                        value = winreg.QueryValueEx(entry, field)[0]
                                    except OSError:
                                        continue
                                    path = _parse_exe_path(value, field == "DisplayIcon")
                                    if path:
                                        return path
                        except OSError:
                            continue
            except OSError:
                continue
    return None


def _find_runtime():
    override = os.environ.get("WORKBUDDY_EXE")
    if override:
        path = os.path.abspath(os.path.expanduser(override))
        if os.path.isfile(path):
            return path
        raise SystemExit("WORKBUDDY_EXE 指向的文件不存在：" + path)
    local = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    pf = os.environ.get("ProgramFiles") or r"C:\Program Files"
    pfx = os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)"
    candidates = [
        os.path.join(local, "Programs", "WorkBuddy", "WorkBuddy.exe"),
        os.path.join(pf, "WorkBuddy", "WorkBuddy.exe"),
        os.path.join(pfx, "WorkBuddy", "WorkBuddy.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    registered = _windows_registry_runtime()
    if registered:
        return registered
    raise SystemExit(
        "找不到 WorkBuddy.exe，请先安装并登录 WorkBuddy 客户端；"
        "或用 WORKBUDDY_EXE 环境变量指定其完整路径。")


def _run_auth_helper(exe, request):
    data = json.dumps(dict(request, version=1), ensure_ascii=True).encode("ascii")
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("NODE_", "ELECTRON_", "WORKBUDDY_"))}
    env["ELECTRON_RUN_AS_NODE"] = "1"
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        proc = subprocess.run([exe, "-e", AUTH_HELPER_JS], input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=env, timeout=20, creationflags=creationflags)
    except FileNotFoundError:
        raise SystemExit("无法启动 WorkBuddy.exe，请核对路径")
    except subprocess.TimeoutExpired:
        raise SystemExit("解密超时，请重试")
    if proc.returncode != 0:
        raise SystemExit("解密失败，请确认 WorkBuddy 客户端已登录且版本兼容")
    try:
        reply = json.loads(proc.stdout.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SystemExit("解密进程返回异常，请检查客户端版本")
    if reply.get("ok") is not True:
        raise SystemExit("解密失败：" + str(reply.get("reason", "未知原因")))
    return reply


def _decrypt_field(exe, value):
    reply = _run_auth_helper(exe, {"operation": "decrypt", "value": value})
    token = reply.get("accessToken")
    if not isinstance(token, str) or not token:
        raise SystemExit("解密结果为空，请检查客户端登录状态")
    return token


def main():
    print_plain = "--print" in sys.argv

    session_path = _find_session_file()
    if not os.path.isfile(session_path):
        raise SystemExit("未找到登录态文件，请先登录一次 WorkBuddy 客户端。\n预期路径：" + session_path)

    try:
        with open(session_path, encoding="utf-8") as f:
            session = json.load(f)
    except (ValueError, OSError) as e:
        raise SystemExit(
            "登录态文件读取失败（%s: %s），请重新登录一次 WorkBuddy 客户端。" % (type(e).__name__, e))
    if not isinstance(session, dict):
        raise SystemExit("登录态文件格式异常，请重新登录一次 WorkBuddy 客户端。")

    auth = session.get("auth") or {}
    account = session.get("account") or {}

    uid = account.get("uid")
    domain = auth.get("domain") or "www.workbuddy.cn"
    if not uid:
        raise SystemExit("登录态中缺少 uid，请确认已正常登录客户端")

    runtime = _find_runtime()

    access_token = auth.get("accessToken")
    refresh_token = auth.get("refreshToken")
    if isinstance(access_token, dict):
        access_token = _decrypt_field(runtime, access_token)
    if isinstance(refresh_token, dict):
        refresh_token = _decrypt_field(runtime, refresh_token)

    if not isinstance(access_token, str) or not access_token:
        raise SystemExit("accessToken 提取失败")

    print("=" * 56)
    print("WorkBuddy 登录信息（已成功解密）")
    print("=" * 56)
    print("uid          :", uid)
    print("domain       :", domain)
    print("accessToken  : 已提取（长度 %d）" % len(access_token))
    if isinstance(refresh_token, str) and refresh_token:
        print("refreshToken : 已提取（长度 %d）" % len(refresh_token))

    if print_plain:
        print("-" * 56)
        print("accessToken  :", access_token)
        if isinstance(refresh_token, str) and refresh_token:
            print("refreshToken :", refresh_token)

    with open("wb_cloud_token.txt", "w", encoding="utf-8") as f:
        f.write(access_token)
    if isinstance(refresh_token, str) and refresh_token:
        with open("wb_refresh_token.txt", "w", encoding="utf-8") as f:
            f.write(refresh_token)

    print("-" * 56)
    print("已写入文件：")
    print("  wb_cloud_token.txt    -> 用于 WB_TOKEN")
    if isinstance(refresh_token, str) and refresh_token:
        print("  wb_refresh_token.txt  -> 用于 WB_REFRESH_TOKEN（可选，自动续期）")
    print()
    print("下一步：把 uid / domain / token 配置到 GitHub 仓库 Secrets，")
    print("详见 README「方案二」第 2~3 步。")
    print()
    print("提醒：这两个 txt 含账号凭据，配好后请及时删除。")


if __name__ == "__main__":
    main()
