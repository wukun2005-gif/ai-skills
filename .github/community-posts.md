# Community Post Drafts

## Reddit r/ClaudeAI

Title: I built a skill sync engine — write once, run on Claude Code + Cursor + VS Code + 20 other tools

Body:

I was tired of rewriting the same instructions for every AI coding tool. Claude Code uses `~/.claude/skills/`, Cursor has its own rules format, Windsurf uses workflows, Cline merges into `.clinerules`...

So I built a set of reusable skills with a sync engine that auto-detects every AI tool on your machine and dispatches each skill in the right format.

**What's included:**
- `dev-iterate` — iterative dev workflow (PRD → dev → test → commit, per feature)
- `test` — smart test runner (analyzes changes, runs targeted tests)
- `commit` — infers commit style, commits and pushes
- `share-skills` — the sync engine: scans your system, auto-discovers tools, syncs everywhere

**How sync works:**
```
/share-skills          # detect all tools, sync everything
/share-skills --add test  # sync just one skill
```

It detects tools by scanning directory content patterns, not hardcoded paths — so new tools get picked up automatically.

Repo: https://github.com/wukun2005-gif/ai-skills

---

## Twitter/X

Thread draft:

1/ Tired of rewriting the same AI coding instructions for every tool? I built a skill sync engine.

Write your skill once in ~/.ai-skills/, run /share-skills, and it auto-detects + syncs to Claude Code, Cursor, VS Code, Windsurf, Cline, Kiro, and 15+ more tools.

2/ The key insight: instead of supporting specific tool formats, it scans your system for AI tools by detecting directory content patterns. New tools get auto-registered. No hardcoded paths.

3/ Includes 7 ready-to-use skills:
- dev-iterate: PRD → dev → test → commit loop
- test: smart targeted test execution
- commit: style-aware git commit
- doc-consistency: cross-doc consistency checks
And more.

4/ MIT licensed, ~5 min setup.

https://github.com/wukun2005-gif/ai-skills

#ClaudeCode #AICoding #DevTools

---

## Show HN

Title: Show HN: AI coding skills that sync across 20+ tools (Claude Code, Cursor, VS Code...)

Body:

I built a set of reusable skills (slash commands) for AI coding assistants with a sync engine that auto-detects every AI tool on your machine and dispatches each skill in the right format.

The problem: every AI coding tool has its own skills/rules system, and they're all incompatible. You end up rewriting the same instructions for each tool.

The solution: write skills once in `~/.ai-skills/`, run `/share-skills`, and it handles format conversion automatically — symlinks for Claude Code/Cursor/Kiro, file copies for VS Code/Windsurf, merge writes for Cline.

Tools are detected by scanning directory content patterns (not hardcoded paths), so newly installed tools are picked up automatically.

Includes 7 skills covering dev workflows (iterative dev, testing, commit, doc consistency, review) plus resume tools.

https://github.com/wukun2005-gif/ai-skills

---

## awesome-claude-skills submission (needs 10+ stars first)

Target section: `### Collections & Libraries` in `🌟 Community Skills`

Entry:
```markdown
*   **[ai-skills](https://github.com/wukun2005-gif/ai-skills)** - A collection of 9 reusable AI coding skills with auto-sync across 20+ tools (Claude Code, Cursor, VS Code Copilot, Cline, Windsurf, Kiro, and more) via a built-in share-skills command.

    *   Skills include: dev-iterate (iterative development), test (targeted test execution), commit (smart commit & push), backlog-update (feature suggestions), doc-consistency (cross-doc consistency checks), review-iterate (iterative doc review), resume-tailor, resume-html
    *   One-command distribution: auto-discovers installed AI tools and syncs skills to all of them via symlinks, copies, or merged writes
    *   MIT License
```

---

## awesome-claude-code submission (via issue form)

Submit at: https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml

Fields:
- Display Name: ai-skills
- Category: Agent Skills
- Sub-Category: General
- Primary Link: https://github.com/wukun2005-gif/ai-skills
- Author: wukun2005-gif / https://github.com/wukun2005-gif
- License: MIT
- Description: A collection of 9 reusable AI coding skills with a built-in sync engine that auto-detects and distributes skills across 20+ AI coding tools. Covers iterative development, testing, code review, documentation consistency, and resume tailoring.
- Validation prompt: "Run /dev-iterate on any project with a backlog.md — it will iterate through each feature, alternating dev and test phases, and commit after each one."
