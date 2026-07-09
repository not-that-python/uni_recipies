# To-Do

Source: Trello board (synced 2026-07-09). Prioritised into MVP / MMP / Future tiers.
Workflow: trunk-based, direct push to `main`, no PRs. See Versioning below for how we revert if something breaks.

## MVP — get it live and usable

- [ ] Push to production on Render first
- [ ] Clean up the page and improve UI

## MMP — make it worth telling people about

- [ ] Categorise recipes (salad, cooked) + build filters for them — **in progress (collaborator)**
- [ ] Add credit to the person who added the recipe
- [ ] If the guest name appears again, ask whether they've added a recipe before and would like to create an account
- [ ] If a recipe already exists, still take the new submission and show it as a variation
- [ ] How to section (checklist 0/3 in Trello — check board for sub-items)
- [ ] Tips
- [ ] Add recipe from user account — option to take the account holder's name as credit, or anonymise

## Future — big feature ideas (post-MMP)

- [ ] Meal planner
- [ ] Use AI agent to suggest recipes
- [ ] Use AI agent to find recipes from the web
- [ ] Personalised recipes
- [ ] "Surprise me" button — suggests a recipe outside the user's usual personal choices
- [ ] Netflix-style personalised suggestions, but for recipes

### Nice to Have

- [ ] Categorise whether a recipe is from a parent or a student
- [ ] Categorise whether a recipe is international or UK home-student style

## Versioning

We tag `main` with semantic version tags (`v0.1.0`, `v0.2.0`, ...) at stable points so we can revert without needing PRs or branches:

- Tag before/after each meaningful chunk of work lands on `main` (e.g. after an MVP item ships).
- To undo a bad push: `git revert <commit>` (keeps history honest) rather than `git reset --hard` + force-push, since we're both pushing directly to the same `main`.
- To go back to a known-good state: `git checkout v0.1.0` (or whichever tag) to inspect/run it; ask before actually moving `main` backwards.
- Baseline tag `v0.1.0` marks current `main` (product brief + help page + search/add recipe flow, pre-Render-deploy).
