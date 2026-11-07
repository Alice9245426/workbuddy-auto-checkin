# WorkBuddy 自动签到

让 WorkBuddy（腾讯 AI 编程助手）的每日签到领积分全自动完成，无需手动打开客户端。提供 **本地** 与 **云端** 两套独立方案，可单独使用，也可互为兜底。

> ⚠️ 本项目仅供技术学习与交流，请遵守 WorkBuddy 的服务条款。使用产生的任何后果（包括账号风控、积分损失等）由使用者自行承担。

---

## ✨ 功能特性

- **本地方案**：Windows 任务计划程序 + 脚本，每天 00:00 准点自动签到，静默无窗口、不耗 AI token。
- **云端方案**：GitHub Actions 定时运行，不依赖本地电脑，关机也能签到。
- **幂等**：先查当天是否已签到，已签则跳过，不会重复领取。
- **破解登录态加密**：新版 WorkBuddy 对本地 token 做了信封加密，本项目给出了在客户端运行时内解密的完整思路。
- **零敏感信息落盘**：token 全程走内存 / 环境变量 / GitHub Secrets，脚本不打印、不落盘。

---

## 📁 目录结构

```
workbuddy-auto-checkin/
├── cloud_checkin.py              # 云端签到脚本（纯 Python 标准库，零依赖）
├── .github/
│   └── workflows/
│       └── checkin.yml           # GitHub Actions 定时配置
├── LICENSE                       # MIT
└── README.md
```

---

## 🧠 核心原理：新版 WorkBuddy 的登录态加密

WorkBuddy **5.6.2+** 把本地登录态文件（`workbuddy-desktop.info`）里的 `accessToken`、`refreshToken`、`nickname` 做了**信封加密**，社区里大量早期签到脚本因此失效——它们读到的 token 是空字符串或 `$wbEncrypted` 占位。

逆向其客户端（`app.asar`）后确认的加密结构：

- 算法：**AES-256-GCM**
- 附加认证数据（AAD）：`WB-AAD\0`
- 密钥来源：由 `keyblob` 文件 + `protectorKey`（系统凭据，DPAPI 保护）派生，**密钥不落盘**
- 解密入口：客户端原生绑定 `electron_browser_workbuddy_storage.loggerGet()`，仅在客户端运行时内可用

因此正确的解密方式不是手动逆向 DPAPI，而是**让客户端自己在运行时解密**：

```bash
ELECTRON_RUN_AS_NODE=1 "WorkBuddy.exe" -e <js>
```

在客户端原生运行时里调用 `loggerGet()` 取 at-rest 密钥，`sha256` 派生 AES-256-GCM 密钥，配合 AAD `WB-AAD\0` 解 envelope。全程内存管道、密钥用完清零。

> 本地方案的解密实现参考了开源项目 [88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin)（MIT），该项目已验证此思路，推荐直接使用。

---

## 🔑 签到接口

签到接口从桌面端逆向而来（域 `copilot.tencent.com`）：

| 用途 | 接口 |
|---|---|
| 查签到状态 | `POST /v2/billing/meter/checkin-activity-status` |
| 执行签到 | `POST /v2/billing/meter/daily-checkin` |

请求头（`domain` 为你的登录域，通常是 `www.workbuddy.cn`）：

```
Authorization: Bearer <accessToken>
X-User-Id: <uid>
X-Domain: <domain>
Content-Type: application/json
```

---

## 🖥️ 方案一：本地（Windows 任务计划）

### 原理

由 Windows「任务计划程序」定时调用脚本，脚本用本机登录态调官方接口签到。**不依赖 WorkBuddy 进程、不耗 AI token、无窗口**。

### 部署步骤

1. **获取脚本**：`git clone https://github.com/88lin/workbuddy-auto-signin.git`（MIT，已内置解密逻辑）。
2. **离线自检**：`python signin.py doctor` —— 验证你机器上的解密链路。
3. **只读验证**：`python signin.py status` —— 真正解密 token 并查签到状态（不领取）。
4. **注册计划任务**（以每天 00:00 为例）：

   ```powershell
   $pythonw = "C:\path\to\pythonw.exe"   # 用无窗口的 pythonw
   $signin = "D:\path\to\signin.py"

   $act  = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$signin`" silent"
   $tri  = New-ScheduledTaskTrigger -Daily -At "00:00"
   $set  = New-ScheduledTaskSettingsSet -StartWhenAvailable -Hidden
   Register-ScheduledTask -TaskName "WorkBuddyAutoSignin" `
     -Action $act -Trigger $tri -Settings $set
   ```

5. **验证**：`Start-ScheduledTask -TaskName "WorkBuddyAutoSignin"` 强制触发一次，检查 `signin.log`。

> 建议额外加一个「补签兜底」任务（如每天 06:00 / 12:00 / 18:00 各跑一次 `silent-poll`），防止 00:00 撞上关机/睡眠导致断签。

---

## ☁️ 方案二：云端（GitHub Actions）

### 原理

把 `accessToken` 存到 GitHub Secrets，GitHub Actions 每天定时跑 `cloud_checkin.py` 调接口签到。**完全不依赖本地电脑**。

### 部署步骤

#### 1. 提取 accessToken

本地方案脚本（88lin）已具备解密能力，可写一个 3 行脚本复用其解密函数导出 token（核心是调 `loggerGet()` 解 `$wbEncrypted`），得到一段 JWT 形式的 `accessToken` 与你的 `uid`、`domain`。

#### 2. 创建私有仓库并上传

```bash
gh repo create workbuddy-cloud-checkin --private
gh api -X PUT repos/<you>/workbuddy-cloud-checkin/contents/cloud_checkin.py \
  -f message="add script" -f content="$(base64 -w0 cloud_checkin.py)"
gh api -X PUT "repos/<you>/workbuddy-cloud-checkin/contents/.github/workflows/checkin.yml" \
  -f message="add workflow" -f content="$(base64 -w0 .github/workflows/checkin.yml)"
```

#### 3. 配置 Secrets

在仓库 **Settings → Secrets and variables → Actions** 里新增三个仓库密钥：

| 名称 | 值 |
|---|---|
| `WB_TOKEN` | 你的 accessToken |
| `WB_UID` | 你的 uid |
| `WB_DOMAIN` | `www.workbuddy.cn` |

或命令行：

```bash
gh secret set WB_TOKEN  --repo <you>/workbuddy-cloud-checkin < token.txt
gh secret set WB_UID    --repo <you>/workbuddy-cloud-checkin --body "<uid>"
gh secret set WB_DOMAIN --repo <you>/workbuddy-cloud-checkin --body "www.workbuddy.cn"
```

#### 4. 触发验证

仓库 **Actions** 页 → 选中工作流 → **Run workflow**，观察日志输出 `{"ok": true, ...}` 即成功。

### 定时说明

`checkin.yml` 里的 cron `0 16 * * *` 对应 **北京时间 00:00**（UTC+8）。GitHub Actions 的 schedule 不保证准点，通常有几到十几分钟延迟。

---

## 🔄 token 续期机制（重要发现）

登录态里的 token 有效期：

| 字段 | 有效期 | 说明 |
|---|---|---|
| `accessToken` | 30 天 | 调用接口用 |
| `refreshToken` | 60 天 | **滚动续期**：每刷新一次顺延 60 天 |

关键结论：

- `refreshExpiresAt = lastRefreshTime + 60 天`，**每次刷新都会顺延**，不是固定的绝对过期时间。
- 刷新由 **WorkBuddy 客户端后台**自动触发（无需手动登录）。
- 因此：**电脑常开 + 客户端后台常驻 → 本地 token 自动续期、永不失效**，本地方案可无限期自动运行。

云端 Secrets 里的 `accessToken` 是一次性快照（30 天后过期），如需云端也长期有效，可进一步扩展为「存 `refreshToken` + 每天先刷新再签到」的自动续期循环（注意：可能与本地客户端产生令牌竞争）。

---

## ❓ 常见问题

**Q：签到会重复领积分吗？**
不会。脚本先查状态，当天已签则直接跳过（幂等）。

**Q：本地和云端同时跑会冲突吗？**
不会。同一天谁先到谁签，另一个幂等跳过，积分不会重复。

**Q：登录态过期了怎么办？**
本地：打开一次 WorkBuddy 客户端即可恢复（后台会自动刷新）。
云端：需要重新提取一次 accessToken 更新 Secrets。

**Q：腾讯改版/加风控了怎么办？**
接口从桌面端逆向，存在失效可能。若脚本报错，通常需重新逆向接口；若账号被风控要求重新登录，任何方案都无法绕过。

---

## ⚖️ 免责声明

- 本项目仅用于**技术学习与研究**，请勿用于违反 WorkBuddy 服务条款的行为。
- 接口与加密机制可能随 WorkBuddy 版本更新而变化，不保证长期可用。
- 使用者应自行评估账号安全与合规风险，作者不承担任何责任。

---

## 🙏 致谢

- [88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin)（MIT）—— 本地解密与签到思路的主要参考。

## 📄 许可证

[MIT](./LICENSE)
