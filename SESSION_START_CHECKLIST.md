# Session Start Checklist (VS Code + Codex + GitHub)

Run this at the start of every coding session to avoid path/branch sync issues.

## 1) Open the right folder in VS Code
- Open: `C:\Users\ryanb\budget`
- In VS Code terminal:

```powershell
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
```

## 2) Run identity check script
From repo root:

```powershell
.\scripts\where-am-i.ps1 -ExpectedRepoName budget -ExpectedBranch main
```

This verifies:
- current directory
- git root
- branch
- remotes
- ahead/behind with `origin/<branch>`
- uncommitted changes

## 3) Before coding in Codex
- Confirm Codex workdir is the same repo root
- Confirm branch matches VS Code
- Confirm `git status --short` looks expected

## 4) During work
- Commit regularly in small chunks
- Keep one branch per task
- Push often

## 5) Before ending session

```powershell
git status
git log --oneline -n 5
git push origin main
```

If branch is not `main`, push the active branch explicitly.
