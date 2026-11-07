# 更新日志 / Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 格式，并使用 [Semantic Versioning](https://semver.org/lang/zh-CN/) 版本号。

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
