# 更新日志 / Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 格式，并使用 [Semantic Versioning](https://semver.org/lang/zh-CN/) 版本号。

## [1.1.2] - 2026-11-08

### 修复（可靠性，真机验证）

- `.github/workflows/checkin.yml`：cron 从 UTC 整点 `0 16 * * *` 改为三个错峰时点（北京时间 00:13 / 00:37 / 01:07）。2026-11-08 实测整点那次**当天 0 次 `schedule` 运行**，而 `workflow_dispatch` 一直正常 —— 整点高负载会直接跳过。错峰 + 多时点互为兜底，脚本先查状态再签到，幂等不重复领。
- `.github/workflows/checkin.yml`：单次请求失败时在同一 job 内重试 3 次（间隔 30 秒），缓解网络抖动 / 接口 5xx 导致的当天漏签。

### 文档

- 删除「分享给朋友」里要求 AI 代跑 `extract_token.py`、代写 Secrets 的整段提示词（与 `SKILL.md` 安全红线直接冲突），改为默认推荐本地方案的纯链接推荐语。
- 云端部署路径统一为「新建私有仓库 + 只上传 2 个文件」，不再引导 Fork（Fork 会把提取脚本带进去，将来同步上游等于新代码带着完整凭据跑）。
- 补充长期维护风险表：30 天 token 到期、客户端重登、GitHub 60 天无活动自动禁用 schedule、境外 IP / 逆向接口的账号风控。
- 新增「本地任务报 `NETWORK` / SSL EOF」排查：计划任务读注册表系统代理，与终端会话的 `HTTPS_PROXY` 不同；可用用户级 `NO_PROXY` 让腾讯域绕过有问题的代理。
- 以上同步 `README.md` / `README_EN.md` / `SKILL.md`。

## [1.1.1] - 2026-11-07

### 修复（全面审计 + 真机/真实接口验证）

- `cloud_checkin.py`：修复刷新接口路径（`/v2/auth/token/refresh` 在真实网关上 404，客户端实际路由为 `/v2/plugin/auth/token/refresh`，经真机探测验证）；此前「自动续期」从未真正生效，仅靠静默回退掩盖。
- `.gitignore` 补充忽略 `wb_refresh_token.txt`：提取脚本会写入两个 txt，此前只忽略了其一，`git add .` 可能误提交 refreshToken。
- `cloud_checkin.py`：签到活动未开启（`active: false`）时明确跳过并报告，不再误报为「签到失败」。
- `cloud_checkin.py`：配置 `WB_REFRESH_TOKEN` 但刷新失败时，输出附带 `refresh_error`（仅 HTTP 状态码，不含任何 token），便于排查。
- `extract_token.py`：登录态文件损坏或无法读取时给出友好提示，不再抛出原始堆栈。
- `setup_windows.ps1`：`pythonw` 探测与 `python` 一致，跳过 Microsoft Store 的 0 字节占位别名，避免误导新用户。
- 特性表「零敏感信息落盘」措辞修正为与提取脚本实际行为一致（中英双语）。
- `SKILL.md` 版本号与仓库版本对齐（1.1.1）。

## [1.1.0] - 2026-11-07

### 新增

- **WorkBuddy Skill**（`SKILL.md`）：把本地方案封装成可一句话触发的技能，用户说「帮我配置自动签到」即可由 AI 完成部署，无需 GitHub 账号与授权。
- **一键安装脚本**（`scripts/setup_windows.ps1`）：自动定位 `pythonw.exe`、获取上游脚本、`doctor` 自检、`status` 只读验证、注册 2 个计划任务并回读校验；支持 `-SkipRegister` 自检模式与 git clone 失败时的 GitHub API zip 兜底。
- **登录信息提取脚本**（`extract_token.py`）：一条命令提取 uid / domain / accessToken / refreshToken，自动从注册表探测 `WorkBuddy.exe`。

### 文档

- 新增「分享给朋友：一句话让 AI 帮你部署」章节，说明为何不能只说「帮我安装 github 上的 workbuddy-auto-checkin」（同名仓库 30 个、本项目非可安装包）。
- 云端部署步骤改为直接使用 `extract_token.py`，不再要求用户自行编写解密脚本。

### 修复（全面审计）

- `SKILL.md` 版本号与 CHANGELOG 对齐（1.1.0）。
- CI 自检补充覆盖 `extract_token.py`（语法编译 + 导入）。
- `setup_windows.ps1` 抑制 `Invoke-WebRequest` / `Expand-Archive` 的进度条输出，避免全新安装时满屏刷屏被误认为卡死。
- 通知请求头 `Content-Type` 补充 `charset=utf-8`，与 Server酱官方示例一致，避免中文通知在部分网关下乱码。
- 新增「用 Skill 一句话跑起来」章节（双语），修正「分享给朋友」中已过时的「没有 SKILL.md」描述。

## [1.0.0] - 2026-11-07

### 新增

- 云端签到脚本 `cloud_checkin.py`（纯 Python 标准库，零依赖，幂等签到）。
- GitHub Actions 定时工作流 `checkin.yml`（每日北京时间 00:00）。
- 完整中文文档 `README.md` 与英文文档 `README_EN.md`。
- 社区规范文件：贡献指南、行为准则、安全政策。
- Issue 模板（Bug 报告 / 功能请求）与 PR 模板。
- 项目 logo（`assets/logo.png`）与社交预览图（`assets/social-preview.png`）。
- CI 自检工作流 `ci.yml`（语法 / 导入 / 无 token 干跑，push 与 PR 触发）。
- 签到结果通知（可选：Telegram / Server酱 / 通用 webhook）。
- 云端 token 自动续期（可选：`WB_REFRESH_TOKEN`，签到前刷新 accessToken）。
- 赞助入口 `FUNDING.yml`。

### 文档

- 记录新版 WorkBuddy 登录态加密（AES-256-GCM + `$wbEncrypted`）的逆向思路。
- 记录 token 滚动续期机制（accessToken 30 天 / refreshToken 60 天滑动续期）。
- 本地（Windows 任务计划）与云端（GitHub Actions）双方案部署步骤。

### 致谢

- 本地解密与签到思路参考 [88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin)（MIT）。
