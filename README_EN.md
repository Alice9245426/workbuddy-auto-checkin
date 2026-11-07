<div align="center">

<img src="assets/logo.png" width="140" alt="WorkBuddy Auto Check-in logo" />

# 🔧 WorkBuddy Auto Check-in

**Fully automate WorkBuddy (Tencent AI assistant) daily check-in to earn credits — no need to manually open the client.**

[简体中文](./README.md) | English

<p>

[![GitHub stars](https://img.shields.io/github/stars/Alice9245426/workbuddy-auto-checkin?style=flat-square&logo=github)](https://github.com/Alice9245426/workbuddy-auto-checkin/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Alice9245426/workbuddy-auto-checkin?style=flat-square&logo=github)](https://github.com/Alice9245426/workbuddy-auto-checkin/network)
[![GitHub issues](https://img.shields.io/github/issues/Alice9245426/workbuddy-auto-checkin?style=flat-square&logo=github)](https://github.com/Alice9245426/workbuddy-auto-checkin/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/Alice9245426/workbuddy-auto-checkin?style=flat-square&logo=github)](https://github.com/Alice9245426/workbuddy-auto-checkin/pulls)
[![GitHub last commit](https://img.shields.io/github/last-commit/Alice9245426/workbuddy-auto-checkin?style=flat-square&logo=github)](https://github.com/Alice9245426/workbuddy-auto-checkin/commits)
[![License](https://img.shields.io/github/license/Alice9245426/workbuddy-auto-checkin?style=flat-square)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](./CONTRIBUTING.md)

</p>

</div>

> ⚠️ **Disclaimer**: This project is for technical learning and research only. Please comply with WorkBuddy's Terms of Service. The check-in API is **reversed from the desktop client, not an official public API**; the cloud option calls it daily from GitHub Actions' overseas IPs, unlike your usual local login location. The user assumes all consequences (including account risk control, forced re-login, credit loss, etc.). **If you recommend this project to others, tell them about these risks first.**

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [One Prompt to Set It Up (Skill)](#-one-prompt-to-set-it-up-skill)
- [Share with a Friend: A Safe Recommendation Guide](#-share-with-a-friend-a-safe-recommendation-guide)
- [Project Structure](#-project-structure)
- [How It Works: Encrypted Credentials](#-how-it-works-encrypted-credentials)
- [Option 1: Local (Windows Task Scheduler)](#-option-1-local-windows-task-scheduler)
- [Option 2: Cloud (GitHub Actions)](#-option-2-cloud-github-actions)
- [Local vs Cloud](#-local-vs-cloud)
- [Token Renewal Mechanism](#-token-renewal-mechanism)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [Acknowledgements](#-acknowledgements)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🖥️ **Local option** | Windows Task Scheduler + script, checks in at 00:00 sharp, silent, no AI token cost |
| ☁️ **Cloud option** | Runs on GitHub Actions, works even when your PC is off |
| 🔁 **Idempotent** | Checks today's status first; skips if already checked in |
| 🔐 **Breaks credential encryption** | Provides a complete approach to decrypt WorkBuddy's new envelope-encrypted tokens |
| 🛡️ **Zero credential leak** | Check-in script keeps tokens in memory / env vars / GitHub Secrets and never prints them; the extractor only writes two local txt files that you delete right after |
| 🔄 **Auto-renewal** | Optional: with a refreshToken, refresh the accessToken before check-in (extends cloud validity to ~60 days) |
| 📣 **Result notification** | Optional: push results to Telegram / ServerChan (WeChat) / generic webhook |
| 🤖 **WorkBuddy Skill** | Ships `SKILL.md`: one sentence ("set up auto check-in") lets an AI deploy the local option |
| 🚀 **Zero dependencies** | Cloud script uses only the Python standard library |

---

## 🚀 Quick Start

**🗣️ Easiest: let WorkBuddy do it (one sentence, recommended)**

Copy `SKILL.md` into your WorkBuddy skills folder (or hand the repo URL to your AI assistant), then say "set up WorkBuddy auto check-in for me". The local option runs entirely on your machine — **no GitHub account, no authorization**. See [One Prompt to Set It Up](#-one-prompt-to-set-it-up-skill).

**Local only (manual, PC usually on)**:

```powershell
# One-shot: self-check + register scheduled tasks (run from the repo root)
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Or follow ["Option 1"](#-option-1-local-windows-task-scheduler) step by step.

**Cloud only (PC-independent fallback)**:

```bash
# 1. On a logged-in WorkBuddy machine, extract credentials
python extract_token.py            # gives uid / domain / token

# 2. Create a NEW private repo and upload ONLY cloud_checkin.py + checkin.yml
# 3. Configure WB_TOKEN / WB_UID / WB_DOMAIN in Settings → Secrets
# 4. Trigger manually from the Actions tab to verify
```

> ⚠️ **Do the cloud option yourself**: `accessToken` is a full account credential — never delegate it to an AI, and **do not Fork this repo** (that pulls in the extractor and other unrelated files). Full steps in ["Option 2"](#-option-2-cloud-github-actions). If your PC is usually on, prefer the local option above.

---

## 🤖 One Prompt to Set It Up (Skill)

This repo ships a **WorkBuddy Skill** (`SKILL.md`) that turns the local deployment into AI-executable instructions.

### Install the skill (pick one)

- **Option A (recommended)**: copy `SKILL.md` and `scripts/` from the repo root into your user-level skills folder:
  ```
  %USERPROFILE%\.workbuddy\skills\workbuddy-auto-checkin\
  ```
  Keep `SKILL.md` at the top level and `scripts/setup_windows.ps1` in the subfolder.
- **Option B**: hand the repo URL to your AI assistant and let it read `SKILL.md` and follow it.

### Then say one sentence

> "Set up WorkBuddy auto check-in for me"

The skill will: locate `pythonw.exe` → fetch the upstream script → `doctor` self-check → read-only `status` check → register 2 scheduled tasks → read back and verify. **Everything stays on your machine: no GitHub account, no authorization, no AI token cost.**

Or run the command directly (self-check first):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -SkipRegister  # check only
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1                # install
```

> Verified end-to-end: `doctor` detects `sym-v1` credentials, `status` returns HTTP 200, forced task run gives `LastTaskResult=0`, and the log is written.
>
> ⚠️ **The skill covers the local option only.** The cloud option needs your own GitHub account and token; an AI should not do that on your behalf — follow ["Option 2"](#-option-2-cloud-github-actions) manually.

---

## 🎁 Share with a Friend: A Safe Recommendation Guide

> ⚠️ **Do not** just say "help me install workbuddy-auto-checkin from GitHub", and **do not** let an AI handle your credentials. See below.

### Why that phrasing goes wrong

1. **"Install" sends the AI down the wrong path**: this is not a pip / npm package (no `setup.py`, `pyproject.toml`, `package.json`). The local option means **running a one-shot script to register Windows scheduled tasks** (or loading `SKILL.md`); the cloud option means **create a new private repo + upload only 2 files + configure Secrets**. Neither is an "install".
2. **Many repos share this name**: a GitHub search for `workbuddy-auto-checkin` returns **30** same/near-name repos (plus an underscore variant `workbuddy_auto_checkin`), some with more stars than this one. With only the project name, an AI may well clone **someone else's repo**.
3. **It really can land in someone else's project**: if the AI searches and forks/clones without an explicit owner, it will use whatever result it finds first. If your token ends up in a stranger's repo, you have handed your account credential to someone else's code — the single most important thing to avoid.
4. **Never delegate cloud credentials to an AI**: the `accessToken` produced by `extract_token.py` is a **full account credential** (equivalent to your password), not a scoped token. Asking an AI to extract it, write Secrets, and trigger Actions hands that credential to an automated flow. This project's own `SKILL.md` "safety red lines" explicitly say **do not configure a user's token into any GitHub repo on their behalf**. Do the cloud option yourself.

### ✅ What to actually send your friend

**Recommend the local option by default** — no GitHub account, no credentials leaving the machine, token auto-renews via the client:

```text
I made a small WorkBuddy auto check-in tool. The local option is easiest:
on Windows, first run scripts/setup_windows.ps1 -SkipRegister as a self-check,
then run it again without that flag to install. Everything stays on your machine,
no GitHub account needed.

The cloud option stores a full account token, needs re-extraction every 30 days,
uses a reversed API from GitHub's overseas IPs, and carries account risk-control
risk. I would not start with it. If you do try it, follow README "Option 2"
manually and do not hand it to an AI.

Repo (plain link, no bold, no backticks):
https://github.com/Alice9245426/workbuddy-auto-checkin
```

### Even simpler: just share the link

Send the repo link to your friend — they can follow the README, or paste the link into their own AI assistant:

```text
https://github.com/Alice9245426/workbuddy-auto-checkin
```

> 💡 Do **not** wrap the URL in Markdown bold (`**`) or backticks — paste the plain address. Copying stray `**` into the address bar causes a GitHub 404.
>
> ⚠️ If your friend's AI assistant reads the repo, **give it only the link** — do not attach instructions like "deploy the cloud option / configure my Secrets". Your friend should follow ["Option 2"](#-option-2-cloud-github-actions) personally.

---

## 📁 Project Structure

```
workbuddy-auto-checkin/
├── SKILL.md                      # WorkBuddy Skill: one sentence deploys the local option
├── scripts/
│   └── setup_windows.ps1         # One-shot installer (self-check + register tasks)
├── cloud_checkin.py              # Cloud check-in script (pure stdlib, zero deps, +renewal +notify)
├── extract_token.py              # Credential extractor for cloud Secrets
├── .github/
│   ├── workflows/
│   │   ├── checkin.yml           # Check-in schedule (00:00 Beijing time daily)
│   │   └── ci.yml                # CI self-check (syntax / import / no-token dry run)
│   ├── ISSUE_TEMPLATE/           # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md  # PR template
│   └── FUNDING.yml               # Funding entry
├── assets/                       # Logo and social preview
├── CONTRIBUTING.md               # Contribution guide
├── CHANGELOG.md                  # Changelog
├── CODE_OF_CONDUCT.md            # Code of conduct
├── SECURITY.md                   # Security policy
├── LICENSE                       # MIT
├── README.md                     # 中文文档
└── README_EN.md                  # English docs
```

---

## 🧠 How It Works: Encrypted Credentials

WorkBuddy **5.6.2+** envelope-encrypts `accessToken`, `refreshToken`, and `nickname` in the local credential file (`workbuddy-desktop.info`). Many early community scripts broke because they read an empty token or the `$wbEncrypted` placeholder.

Reverse-engineering the client (`app.asar`) reveals:

| Item | Value |
|---|---|
| Algorithm | AES-256-GCM |
| AAD | `WB-AAD\0` |
| Key source | Derived from `keyblob` + `protectorKey` (system credential, DPAPI-protected); key never touches disk |
| Decrypt entry | Native binding `electron_browser_workbuddy_storage.loggerGet()` |

Therefore the correct approach is **not** to reverse DPAPI by hand, but to let the client decrypt at runtime:

```bash
ELECTRON_RUN_AS_NODE=1 "WorkBuddy.exe" -e <js>
```

Call `loggerGet()` inside the client's native runtime to obtain the at-rest key, derive the AES-256-GCM key with `sha256`, and decrypt the envelope with AAD `WB-AAD\0`. All in-memory, key zeroed after use.

> The local decryption implementation references the open-source project [88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin) (MIT), which has verified this approach.

### Check-in API

Reversed from the desktop client (domain `copilot.tencent.com`):

| Purpose | Endpoint |
|---|---|
| Query status | `POST /v2/billing/meter/checkin-activity-status` |
| Perform check-in | `POST /v2/billing/meter/daily-checkin` |
| Refresh accessToken | `POST /v2/plugin/auth/token/refresh` (with `X-Refresh-Token` header) |

Headers (`domain` is usually `www.workbuddy.cn`):

```
Authorization: Bearer <accessToken>
X-User-Id: <uid>
X-Domain: <domain>
Content-Type: application/json
```

---

## 🖥️ Option 1: Local (Windows Task Scheduler)

### How it works

Windows Task Scheduler runs the script on a schedule; the script calls the official API using local credentials. **No WorkBuddy process, no AI token cost, no window.**

### Steps

1. **Get the script**: `git clone https://github.com/88lin/workbuddy-auto-signin.git` (MIT, decryption built in).
2. **Offline self-check**: `python signin.py doctor` — verifies your decryption pipeline.
3. **Read-only verify**: `python signin.py status` — decrypts the token and queries status (does not claim).
4. **Register the task** (daily at 00:00):

   ```powershell
   $pythonw = "C:\path\to\pythonw.exe"   # windowless pythonw
   $signin = "D:\path\to\signin.py"

   $act  = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$signin`" silent"
   $tri  = New-ScheduledTaskTrigger -Daily -At "00:00"
   $set  = New-ScheduledTaskSettingsSet -StartWhenAvailable -Hidden
   Register-ScheduledTask -TaskName "WorkBuddyAutoSignin" `
     -Action $act -Trigger $tri -Settings $set
   ```

5. **Verify**: `Start-ScheduledTask -TaskName "WorkBuddyAutoSignin"`, then check `signin.log`.

> 💡 Add a catch-up task (e.g. `silent-poll` at 06:00 / 12:00 / 18:00) to avoid missing a day when the PC is off at 00:00.

---

## ☁️ Option 2: Cloud (GitHub Actions)

### How it works

Store `accessToken` in GitHub Secrets; GitHub Actions runs `cloud_checkin.py` on a schedule. **Fully independent of your local PC.**

> ⚠️ **Know the cost before you start**: `extract_token.py` yields a **full account accessToken** (equivalent to your password), not a read-only or scoped token, and this project offers no way to reduce its privilege. The cloud calls a reversed API daily from GitHub Actions' overseas IPs, unlike your usual login location, which carries account risk-control risk. **Do these steps yourself; do not delegate them to an AI** (see the safety red lines in `SKILL.md`).

### Steps

#### 1. Extract accessToken

On a machine where you are **logged into WorkBuddy**, run the bundled extractor (auto-locates the client, decrypts in memory, no network, no plaintext printed by default):

```bash
# 1. Clone this repo locally (only to run the extractor; no Fork needed)
git clone https://github.com/Alice9245426/workbuddy-auto-checkin.git
cd workbuddy-auto-checkin

# 2. Extract uid / domain / accessToken / refreshToken
python extract_token.py
```

It prints your `uid` and `domain`, and writes `accessToken` (plus optional `refreshToken`) to `wb_cloud_token.txt` / `wb_refresh_token.txt`.

> Requires Python 3. If WorkBuddy is installed in a non-default directory, the script auto-detects it from the registry; otherwise set `WORKBUDDY_EXE` to the full path of `WorkBuddy.exe`. Delete the two txt files after you are done.

#### 2. Create a repo and upload

> ⚠️ **Do not Fork this repo**: create a new private repo and upload **only the 2 files below**. Forking pulls in `extract_token.py`, `SKILL.md`, the installer and other files; if you later sync upstream updates, new code would run while holding your full account credential. The private repo only needs `cloud_checkin.py` and `checkin.yml`.

```bash
gh repo create workbuddy-cloud-checkin --private
gh api -X PUT repos/<you>/workbuddy-cloud-checkin/contents/cloud_checkin.py \
  -f message="add script" -f content="$(base64 -w0 cloud_checkin.py)"
gh api -X PUT "repos/<you>/workbuddy-cloud-checkin/contents/.github/workflows/checkin.yml" \
  -f message="add workflow" -f content="$(base64 -w0 .github/workflows/checkin.yml)"
```

#### 3. Configure Secrets

Add three repository secrets under **Settings → Secrets and variables → Actions**:

| Name | Value |
|---|---|
| `WB_TOKEN` | Your accessToken |
| `WB_UID` | Your uid |
| `WB_DOMAIN` | `www.workbuddy.cn` |

Or via CLI:

```bash
gh secret set WB_TOKEN  --repo <you>/workbuddy-cloud-checkin < token.txt
gh secret set WB_UID    --repo <you>/workbuddy-cloud-checkin --body "<uid>"
gh secret set WB_DOMAIN --repo <you>/workbuddy-cloud-checkin --body "www.workbuddy.cn"
```

#### 4. Trigger to verify

Repo **Actions** tab → select the workflow → **Run workflow**. Success if the log shows `{"ok": true, ...}`.

#### 5. Result notification (optional)

Configure extra secrets to push check-in results (success / already-done / failure):

| Secret | Channel | Notes |
|---|---|---|
| `TG_BOT_TOKEN` + `TG_CHAT_ID` | Telegram | Push via Bot API |
| `SERVERCHAN_KEY` | ServerChan (WeChat) | Get a SendKey at [sct.ftqq.com](https://sct.ftqq.com) |
| `NOTIFY_WEBHOOK` | Generic webhook | POSTs a JSON payload to the URL |

The three channels can be configured together; configure none to run silently.

#### 6. Token auto-renewal (optional)

By default the cloud only stores `accessToken` (~30 days). If you also set `WB_REFRESH_TOKEN` (the refreshToken), the script refreshes the accessToken before check-in, extending cloud validity to about **60 days**:

| Secret | Notes |
|---|---|
| `WB_REFRESH_TOKEN` | refreshToken (extracted alongside accessToken from local credentials) |

> ⚠️ The refresh endpoint is reversed from the client and may break; on failure the script falls back to the original `WB_TOKEN`, so the main flow is unaffected. Note the refreshToken itself also expires (~60 days) and must be re-extracted.
>
> ⚠️ **Token competition**: the server rotates the refreshToken on every refresh. After the cloud refreshes daily, the old refreshToken stored in your local WorkBuddy client may become invalid, forcing the client to re-login on its next renewal. If you still use the client on this machine, pick one: let the client renew (skip `WB_REFRESH_TOKEN` in the cloud), or accept re-extracting the token occasionally.

### Schedule and long-term maintenance

`checkin.yml` uses three **off-peak** crons as fallbacks for each other (the script checks status before claiming, so it is idempotent and never double-claims):

| cron (UTC) | Beijing time | Role |
|---|---|---|
| `13 16 * * *` | 00:13 | primary |
| `37 16 * * *` | 00:37 | fallback 1 |
| `7 17 * * *` | 01:22 | fallback 2 |

> ⚠️ Earlier versions used `0 16 * * *` (UTC top-of-hour). On 2026-11-08 that slot produced **zero `schedule` runs all day**, while manual `workflow_dispatch` kept working — peak load can skip the run entirely. Hence the off-peak multi-slot setup, plus 3 in-job retries (30s apart) on failure.

The cloud option uses a **one-time credential snapshot**. Each of the following can silently break your streak:

| Issue | When | What to do |
|---|---|---|
| `accessToken` expires | ~**30 days** after extraction (`expiresAt` in local credentials) | Re-run `extract_token.py` and update `WB_TOKEN` |
| Local re-login / account switch / client reinstall | Any time | The snapshot in Secrets may be revoked early; re-extract |
| GitHub disables the schedule | **60 days** with no commit or repo activity | Re-enable the workflow in the Actions tab; push a commit occasionally |
| A single request fails | Network blip / API 5xx | The workflow retries 3 times; only 3 consecutive failures lose the day. Configure step 5 notifications to avoid silent failure |
| Tencent changes the API or adds risk control | Unpredictable | See [FAQ](#-faq) |

> 💡 If your **PC is usually on**, ["Option 1 (Local)"](#-option-1-local-windows-task-scheduler) is clearly more robust: the client renews the token in the background, 7 trigger points, exact 00:00, no GitHub account, and no credential ever leaves your machine.

#### Local task reports `NETWORK` / SSL EOF (observed 2026-11-08)

A scheduled task is started by Windows and reads the **system proxy from the registry** (`ProxyServer`); it does **not** inherit `HTTPS_PROXY` from your terminal session. If that proxy returns `[SSL: UNEXPECTED_EOF_WHILE_READING]` for the Tencent domain, `signin.py` burns through its backoff retries and logs `"result": "NETWORK"` with `LastTaskResult=1`, while running `status` manually in a terminal succeeds (different proxy) — which makes it look like a broken script.

To diagnose, request `https://copilot.tencent.com/` once via the system proxy port, once via the terminal proxy port, and once with no proxy, then see which path throws SSL EOF. The fix is usually a **user-level `NO_PROXY`** for that domain (bypass only that host; direct connections work on most networks), then force-run the task and confirm `LastTaskResult=0` with `ALREADY` / `CLAIMED` in the log:

```powershell
[Environment]::SetEnvironmentVariable('NO_PROXY', 'copilot.tencent.com,*.tencent.com', 'User')
Start-ScheduledTask -TaskName "WorkBuddyAutoSignin"
Get-ScheduledTaskInfo -TaskName "WorkBuddyAutoSignin" | Select LastRunTime, LastTaskResult
```

If your network **requires** a proxy to reach the Tencent domain, do not set `NO_PROXY` — fix that proxy's routing rule instead.

---

## ⚖️ Local vs Cloud

| Dimension | Local | Cloud |
|---|---|---|
| Depends on local PC | ✅ PC must be on | ❌ No |
| Punctuality | ✅ Exact 00:00 (+6 catch-up slots) | ⚠️ Three off-peak slots from 00:13; still subject to delay or skipping |
| Maintenance | ✅ None (auto-renewal) | ⚠️ Re-extract accessToken every 30 days |
| Stability | ✅ High | ⚠️ Token re-extraction, 60-day inactivity auto-disable, depends on GitHub scheduling |
| Best for | PC usually on | PC may be off for long |

> 💡 You can run **both** together: whichever runs first checks in, the other idempotently skips. Credits are never doubled.

---

## 🔄 Token Renewal Mechanism

Credential expiry:

| Field | Validity | Notes |
|---|---|---|
| `accessToken` | 30 days | Used for API calls |
| `refreshToken` | 60 days | **Sliding renewal**: each refresh extends by 60 days |

Key findings:

- `refreshExpiresAt = lastRefreshTime + 60 days` — **each refresh pushes it forward**, not a fixed absolute expiry.
- Refresh is triggered **automatically by the WorkBuddy client in the background** (no manual login).
- Therefore: **PC usually on + client resident in background → local token auto-renews and never expires**, so the local option can run indefinitely.

The cloud `accessToken` in Secrets is a one-time snapshot (expires in 30 days). `cloud_checkin.py` now has built-in auto-renewal ("store `refreshToken` + refresh before check-in", see Option 2 step 6), extending cloud validity to ~60 days (note: may compete with the local client for the token).

---

## ❓ FAQ

<details>
<summary><b>Q: Will check-in duplicate credits?</b></summary>
No. The script queries status first and skips if already checked in (idempotent).
</details>

<details>
<summary><b>Q: Do local and cloud conflict?</b></summary>
No. Whichever runs first checks in, the other skips. Credits are never doubled.
</details>

<details>
<summary><b>Q: What if credentials expire?</b></summary>
Local: open the WorkBuddy client once to restore (background auto-refresh).<br>
Cloud: re-extract the accessToken and update Secrets.
</details>

<details>
<summary><b>Q: What if Tencent changes the API or adds risk control?</b></summary>
The API is reversed from the client and may break. If the script errors, re-reverse the API; if the account is forced to re-login by risk control, no approach can bypass it.
</details>

<details>
<summary><b>Q: Why does the workflow in the public repo error?</b></summary>
The public repo has no Secrets (and should not), so scheduled runs fail with a missing `WB_TOKEN`. This is expected. Create a new private repo and configure Secrets as described in ["Option 2"](#-option-2-cloud-github-actions).
</details>

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](./CONTRIBUTING.md)

---

## 🙏 Acknowledgements

- [88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin) (MIT) — main reference for local decryption and check-in.

## 📄 License

Released under the [MIT](./LICENSE) license.
