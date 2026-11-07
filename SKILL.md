---
name: workbuddy-auto-checkin
slug: workbuddy-auto-checkin
displayName: "WorkBuddy 本地云端自动签到"
display_name: "WorkBuddy 本地云端自动签到"
display_name_en: "WorkBuddy Auto Check-in (Local + Cloud)"
version: "1.1.1"
summary: "在本机一键部署 WorkBuddy 每日自动签到（Windows 计划任务，不依赖客户端常驻），并说明云端 GitHub Actions 方案的配置入口"
description_zh: "配置 WorkBuddy 每日自动签到领积分。当用户说「帮我配置自动签到」「让签到全自动」「装一下自动签到」「每天自动领积分」「检查签到有没有在跑」，或提到本地/云端签到、计划任务、断签、连续签到天数时使用。本地方案通过 Windows 任务计划程序 + 本机登录态解密实现，全程本机、无需 GitHub 账号、无需授权、不耗 AI token。云端方案需要用户自己的 GitHub 账号与 Secrets，不能自动代劳，应引导到 README。"
description_en: "Set up WorkBuddy daily automatic check-in. Use when the user says 'set up auto check-in', 'make check-in fully automatic', 'install auto signin', 'claim points automatically every day', 'check if auto check-in is running', or mentions local/cloud check-in, scheduled tasks, broken streaks, or consecutive check-in days. The local option uses Windows Task Scheduler plus local credential decryption; it runs entirely on the machine with no GitHub account, no authorization, and no AI token cost. The cloud option needs the user's own GitHub account and Secrets and cannot be done on their behalf; point them to the README."
license: "MIT"
description: "配置 WorkBuddy 每日自动签到领积分。当用户说「帮我配置自动签到」「让签到全自动」「装一下自动签到」「每天自动领积分」「检查签到有没有在跑」，或提到本地/云端签到、计划任务、断签、连续签到天数时使用。本地方案通过 Windows 任务计划程序 + 本机登录态解密实现，全程本机、无需 GitHub 账号、无需授权、不耗 AI token。云端方案需要用户自己的 GitHub 账号与 Secrets，不能自动代劳，应引导到 README。"
agent_created: true
---

# WorkBuddy 本地云端自动签到

## 这个 Skill 解决什么

把「每天手动打开 WorkBuddy 点签到」变成「装一次，之后全自动」。

**本地方案**（本 Skill 能一键完成）：
- Windows 任务计划程序每天 00:00 准点签到，另有 6 个补签点兜底。
- 脚本用本机登录态直接调官方接口，**不需要 WorkBuddy 客户端常驻、不需要 GitHub 账号、不耗 AI token、无窗口**。
- 登录态由客户端后台自动滚动续期（每次刷新顺延 60 天），电脑常开即可长期无人值守。

**云端方案**（不能自动代劳）：需要用户自己的 GitHub 账号、**新建私有仓库并只上传 `cloud_checkin.py` 与 `checkin.yml` 两个文件**（不要 Fork 本仓库）、由用户本人填 `accessToken` 到 Secrets。`accessToken` 是完整账号凭据，涉及账号授权，**不要替用户执行**，只引导其阅读仓库 README 的「方案二」。

## 前提（执行前先确认）

| 条件 | 检查方式 | 不满足时 |
|---|---|---|
| Windows | `$PSVersionTable.PSVersion` | 云端方案或 88lin 仓库的 macOS/Linux 用法 |
| 已登录过 WorkBuddy 桌面端 | `%LOCALAPPDATA%\CodeBuddyExtension\Data\Public\auth\workbuddy-desktop.info` 存在 | 让用户打开客户端登录一次 |
| Python 3 | `python --version` | 引导安装 https://www.python.org/downloads/ （勾选 Add to PATH） |
| git | `git --version` | 脚本会自动改用手动下载 zip 的提示 |

## 一句话执行（主路径）

在 Skill 目录（即仓库根目录）下运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

脚本会依次完成：`clone 上游脚本 → 定位 Python → 离线自检 → 只读查签到状态 → 注册 2 个计划任务 → 回读验证`。
**先跑一遍自检模式**（不写系统任务，只验证链路）更稳妥：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -SkipRegister
```

自检通过后再去掉 `-SkipRegister` 正式注册。

## 脚本做了什么（便于你判断输出是否正常）

1. 定位 `pythonw.exe`（无窗口版），探测顺序：PATH → python.exe 同目录 → 常见安装目录 → `py` 启动器 → WorkBuddy 内置 Python。
2. 获取上游签到脚本：clone `https://github.com/88lin/workbuddy-auto-signin.git` 到 `%LOCALAPPDATA%\WorkBuddyAutoCheckin`；目录已存在则复用。
3. `python signin.py doctor`：离线检查凭据格式与解密能力（不联网、不领取）。
4. `python signin.py status`：真正解密 token 并查签到状态（**只读，不领取**）。输出应含连签天数与累计积分。
5. 注册计划任务：
   - `WorkBuddyAutoSignin`：每天 **00:00**，`silent`（签到 + 成长中心，静默写日志）。
   - `WorkBuddyGrowthPoll`：每天 01/05/09/13/17/21 点，`silent-poll`（未签才补签 + 成长中心）。
   - 均设 `StartWhenAvailable`（关机错过开机补跑）、`Hidden`、`ExecutionTimeLimit`。
6. 回读两个任务的状态与下次运行时间，全部成功才报告完成。

> 时间可用 `-MainAt "00:00"` 调整。上游 `install-windows.ps1` 默认 00:05，本脚本默认按用户要求的 00:00。

## 验证

```powershell
Get-ScheduledTaskInfo -TaskName "WorkBuddyAutoSignin" | Select LastRunTime, LastTaskResult, NextRunTime
Start-ScheduledTask -TaskName "WorkBuddyAutoSignin"   # 强制触发一次
Get-Content "$env:LOCALAPPDATA\WorkBuddyAutoCheckin\signin.log" -Tail 3
```

`LastTaskResult = 0` 表示成功；日志里出现 `"result": "ALREADY"` 或 `"OK"` 都属正常（幂等，不会重复领积分）。
首次注册但还没到触发时间时，`LastTaskResult` 可能是 `267011`（尚未运行），不是错误。

## 故障排查

| 现象 | 处理 |
|---|---|
| 找不到 pythonw | 装 Python 3 并勾选 Add to PATH；或用 `-Pythonw "C:\...\pythonw.exe"` 指定 |
| `doctor` 报 `RUNTIME_NOT_FOUND` | 用 `WORKBUDDY_EXE` 环境变量指定 `WorkBuddy.exe` 完整路径 |
| `status` 报登录态过期 / 401 | 让用户打开一次 WorkBuddy 客户端，停留几秒刷新登录态，再重跑 |
| 注册报拒绝访问 0x80070005 | 用同一 Windows 账号以管理员身份打开 PowerShell 重试 |
| git clone 失败 | 校园网/代理常见；手动下载上游 zip 解压到 `%LOCALAPPDATA%\WorkBuddyAutoCheckin` 后重跑 |
| 今天已签到 | 正常，幂等跳过，不是错误 |

## 安全红线（必须遵守）

- `accessToken` / `refreshToken` 等同账号密码：**只读、不打印、不上传、不写进任何对外内容或日志**。
- 不改写、不删除登录态文件；不结束 WorkBuddy 客户端进程；不切换账号。
- **不要替用户把 token 配置到任何 GitHub 仓库**，也不要把 token 贴到聊天里。云端方案让用户本人操作。
- 不向第三方地址发送凭据；脚本唯一网络目标是腾讯官方 `copilot.tencent.com`。
- 不要 clone 任何同名仓库；上游只认 `https://github.com/88lin/workbuddy-auto-signin.git`。

## 云端方案（用户主动要求时才讲）

明确告诉用户：云端不依赖本地电脑，但**必须用户本人**按 README「方案二」完成：
把 `https://github.com/Alice9245426/workbuddy-auto-checkin` clone 到本机（只为跑提取脚本，**不要 Fork**）→ 本机运行 `extract_token.py` 提取 uid/domain/token → **新建私有仓库，只上传 `cloud_checkin.py` 和 `checkin.yml` 两个文件** → 在自己仓库 Settings → Secrets 配置 `WB_TOKEN` / `WB_UID` / `WB_DOMAIN` → Actions 页手动触发验证。

同时如实告知以下代价，别只讲「关机也能签到」：

- `accessToken` 是**完整账号凭据**，不是受限令牌；本项目没有降权方案。
- 约 **30 天**过期（`expiresAt`），到期需重新提取；本机重新登录 / 换账号也可能让快照提前失效。
- GitHub 在仓库 **60 天无任何活动**时会自动禁用 scheduled workflow，需去 Actions 页重新启用。
- cron 在 UTC 16:00 整点（北京时间 00:00）属高负载时段，可能延迟或跳过；单次请求失败无重试、无补签，不配通知就会静默失败。
- 签到接口为客户端逆向，云端从 GitHub 境外 IP 发起，存在账号风控风险（见 README 免责声明）。

**默认推荐本地方案**：token 由客户端后台滚动续期、7 个触发点兜底、准点、凭据不出本机。详见 README「方案二」。

## 卸载

```powershell
Unregister-ScheduledTask -TaskName "WorkBuddyAutoSignin" -Confirm:$false
Unregister-ScheduledTask -TaskName "WorkBuddyGrowthPoll" -Confirm:$false
```

## 致谢与许可

本地解密与签到脚本来自 [88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin)（MIT），本项目仅引用其安装流程，未复制其代码。
