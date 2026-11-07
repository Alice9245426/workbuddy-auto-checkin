# 贡献指南 / Contributing Guide

感谢你对 **WorkBuddy Auto Check-in** 的关注！无论是提交 Issue、修复 Bug、改进文档还是提出新功能，都欢迎你的参与。

## 目录

- [行为准则](#行为准则)
- [如何报告问题](#如何报告问题)
- [如何提交代码](#如何提交代码)
- [开发环境](#开发环境)
- [代码规范](#代码规范)
- [提交信息规范](#提交信息规范)

---

## 行为准则

请遵守我们的 [行为准则](./CODE_OF_CONDUCT.md)，保持友好、专业、互相尊重。

## 如何报告问题

在提交 Issue 前，请：

1. **先搜索**已有的 [Issues](https://github.com/Alice9245426/workbuddy-auto-checkin/issues)，确认问题未被报告过。
2. 使用对应的 Issue 模板（Bug 报告 / 功能请求）。
3. 提供尽可能完整的信息：
   - 操作系统与版本（如 Windows 11）
   - Python 版本
   - WorkBuddy 客户端版本
   - 复现步骤
   - 预期行为 vs 实际行为
   - 相关日志（⚠️ **务必先脱敏**，删除 token、uid 等敏感信息）

## 如何提交代码

1. **Fork** 本仓库到你的账号下。
2. 创建一个特性分支：

   ```bash
   git checkout -b feat/my-feature
   ```

3. 提交改动，并保持提交信息清晰（见下方规范）。
4. 推送到你的 Fork，然后提交 **Pull Request**。
5. 在 PR 描述中说明改动目的、影响范围与测试情况。

### PR 检查清单

- [ ] 已阅读并同意行为准则
- [ ] 代码通过本地测试
- [ ] 文档已同步更新
- [ ] 无硬编码的 token / uid 等敏感信息
- [ ] 提交信息符合规范

## 开发环境

```bash
git clone https://github.com/<you>/workbuddy-auto-checkin.git
cd workbuddy-auto-checkin
python -m py_compile cloud_checkin.py   # 语法检查
```

云端脚本仅依赖 Python 标准库（3.8+），无需安装第三方依赖。

本地调试云端脚本：

```bash
# 用环境变量传入（不要硬编码到代码里）
WB_TOKEN=xxx WB_UID=xxx WB_DOMAIN=www.workbuddy.cn python cloud_checkin.py
```

## 代码规范

- 保持纯标准库实现，避免引入第三方依赖。
- 敏感信息（token、uid）一律从环境变量读取，**严禁硬编码**。
- 日志输出**禁止打印 token**，必要时脱敏。
- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 风格。

## 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：

```
feat: 新增某功能
fix: 修复某问题
docs: 更新文档
chore: 杂项改动
refactor: 重构
```

---

再次感谢你的贡献！🎉
