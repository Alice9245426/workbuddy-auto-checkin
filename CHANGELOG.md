# 更新日志 / Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 格式，并使用 [Semantic Versioning](https://semver.org/lang/zh-CN/) 版本号。

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
