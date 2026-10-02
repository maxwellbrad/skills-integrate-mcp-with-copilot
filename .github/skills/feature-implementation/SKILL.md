---
name: feature-implementation
description: "Use when implementing a feature, bug fix, or repository change that should be developed on a new branch and published through a user-reviewed pull request."
---

# Feature Implementation Workflow

Use this workflow for repository changes that need a local branch, user review, and a pull request.

1. Identify the requested behavior, owning code, applicable repository instructions, and focused validation. Check the current branch and worktree before changing anything. Preserve existing user changes; if they conflict with creating a clean feature branch, ask before proceeding.
2. Create a descriptive local branch from the appropriate base branch. Do not switch away from or overwrite uncommitted work.
3. Make the smallest complete implementation, including focused tests and relevant documentation. Run the narrowest useful checks, then any required repository gates. Review the diff for unrelated changes and disclose any checks that could not run.
4. Summarize the implementation, tests, and notable tradeoffs. Ask the user to confirm the changes look correct. Stop here and do not commit, push, or open a pull request until the user explicitly approves publication.
5. After approval, commit the feature changes, push the branch, and create a pull request. Check for a repository pull request template and follow it. Report the branch, commit, pull request link, and any remaining checks.

If the user declines publication, leave the reviewed work on the local branch and make no remote changes.