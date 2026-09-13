# Allshield Copilot work rules

## Purpose

This repository uses one `main` history with separate working directories. The directories are an ownership boundary between Copilot sessions; they are not Git branches.

Before changing a file, Copilot must know both the exact active work directory and the allowed read directories. If Johan has not supplied that information, Copilot must not edit, move, delete, stage, commit, or run a command that can write files. It may ask Johan for the missing directory assignment.

## Fixed directory assignments

All paths below are relative to the repository root.

| Machine | Active work directory | Copilot may write there |
|---|---|---|
| MSI | `allshield_diagrams/` | Yes, only for the MSI assignment |
| Razor | `allshield_AHU/` | Yes, only for the Razor assignment |
| Slk | `allshield_building/` | Yes, only for the Slk assignment |

The active Copilot must verify its assignment before working. It may only create, edit, rename, or delete files inside its own active work directory.

## Read-only shared material

Every machine may read all content in `shared/`. Copilot must treat `shared/` as read-only:

- Do not create, edit, rename, move, delete, format, regenerate, or stage files in `shared/`.
- Do not overwrite an existing source file, PDF, image, video, archive, baseline, or user document.
- A new shared source is added only by Johan, who decides when it is manually made available to the other machines.
- When a task needs a shared file to change, Copilot must stop and ask Johan. It may not create a replacement copy under a different name to bypass this rule.

Copilot may also read root-level project instructions and `.github/copilot-instructions.md`, but may not change them unless Johan explicitly assigns that file as an exception for the current task.

## What Copilot must not touch outside its assignment

Unless Johan explicitly grants a one-time exception, the active Copilot must not modify anything outside its own work directory, including:

- another machine's work directory;
- `shared/`;
- `.git/`, `.github/`, repository-root files, and VS Code workspace settings;
- common output folders, source archives, baselines, or user documents.

Generated FreeCAD documents, screenshots, logs, test results, temporary files, and exports must be written below the active work directory in a unique output folder. Do not use a shared root-level `outputs/` folder while another Copilot may be active.

## Git rules

The repository has one shared Git index per local checkout. Parallel file edits in different directories are normally fine, but staging and committing are repository-wide operations. Therefore, Git writes must be short and coordinated: only one Copilot or user may stage, commit, merge, reset, clean, switch branches, or alter worktrees at a time.

Before staging, Copilot must check the active work directory and the staged index:

```powershell
git status --short -- allshield_diagrams/
git diff --cached --name-only
```

For Razor or Slk, replace `allshield_diagrams/` with the assigned directory. If the staged index contains a path outside the active work directory, Copilot must not stage or commit and must ask Johan.

Stage only the assigned directory or explicitly named files. Never use broad Git commands such as `git add .`, `git add -A`, `git commit -a`, `git reset --hard`, `git clean`, or a branch/worktree command unless Johan explicitly requests it.

```powershell
git add -- allshield_AHU/
git diff --cached -- allshield_AHU/
git commit -m "AHU: concise description of the verified change"
```

Replace the path and message with the active assignment. A local commit preserves the work in that machine's local repository; it does **not** automatically copy the commit or files to the other two machines.

Do not push, publish, fetch, pull, merge, rebase, or synchronize with another machine or remote unless Johan explicitly requests that exact action. When Johan manually transfers changes, record the source machine, commit ID, and transferred paths in the relevant work handoff.

## Required workflow for every task

1. Confirm the current machine and its assigned active work directory.
2. Read the relevant material in `shared/` and the repository instructions without modifying them.
3. Work only in the assigned directory.
4. Run focused checks that do not write outside the assigned directory. Report static, native, GUI, and source checks separately when applicable.
5. Before committing, confirm that the index is clear of another machine's files and stage only the assigned paths.
6. Keep a concise handoff in the assigned work directory: changed files, source evidence, test results, output locations, unresolved items, and local commit ID if created.

## Stop conditions

Copilot must stop and ask Johan rather than guessing when:

- the exact machine or work directory is unknown;
- required input is absent from `shared/` or cannot be read;
- a task requires modifying `shared/`, another work directory, a root file, or a common generator;
- another machine has staged changes or is performing a Git operation;
- a result needs to be transferred, merged, pushed, or synchronized;
- a source value, coordinate, dimension, or model interpretation is unresolved.

These rules supplement, and never override, `.github/copilot-instructions.md` and the project handoff/test-plan requirements.