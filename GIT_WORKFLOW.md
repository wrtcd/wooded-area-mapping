# Git Workflow Guide: Working Across Multiple Computers

## Overview

You'll work on the **same branch** (`main`) from both your laptop and desktop. Git keeps everything synchronized through pull/push operations.

**Key Concept**: Git doesn't create separate branches for each computer. Instead, you:
1. **Pull** latest changes before starting work
2. **Make changes** locally
3. **Commit** your changes
4. **Push** to GitHub
5. **Pull** on the other computer to get updates

---

## Daily Workflow

### Starting Work (On Either Computer)

**Always start by pulling the latest changes:**

```bash
cd "path/to/wooded-area-mapping"  # Navigate to your project folder
git pull origin main               # Get latest changes from GitHub
```

**Why?** This ensures you have the latest code from your other computer or any collaborators.

### Making Changes

1. **Edit files** as normal (code, scripts, documentation)
2. **Test your changes** locally
3. **Stage your changes**:
   ```bash
   git add .                    # Stage all changes
   # OR
   git add specific_file.py     # Stage specific files
   ```

4. **Commit your changes**:
   ```bash
   git commit -m "Description of what you changed"
   ```
   Examples:
   - `git commit -m "Add temporal features computation"`
   - `git commit -m "Update README with new workflow"`
   - `git commit -m "Fix bug in predict_wooded_dl.py"`

5. **Push to GitHub**:
   ```bash
   git push origin main
   ```

### Switching Computers

**When you switch from laptop to desktop (or vice versa):**

```bash
# On the NEW computer (where you want to continue work)
cd "path/to/wooded-area-mapping"
git pull origin main    # Get latest changes from GitHub
```

Now you have all the latest changes and can continue working!

---

## Common Scenarios

### Scenario 1: You Made Changes on Laptop, Now Working on Desktop

```bash
# On desktop
cd "path/to/wooded-area-mapping"
git pull origin main    # Gets your laptop changes
# Continue working...
git add .
git commit -m "Made changes on desktop"
git push origin main
```

### Scenario 2: You Forgot to Pull Before Making Changes

**Important**: Your changes ARE saved! They're saved locally in your Git repository on your local `main` branch. Nothing is lost.

**What happens:**

1. **You make changes** → Saved locally ✅
2. **You commit** → Saved to your local `main` branch ✅
3. **You try to push** → Git checks if GitHub has newer commits
4. **If GitHub has newer commits** → Git rejects the push to prevent overwriting

**Example:**
```bash
# You forgot to pull, made changes, committed
git add .
git commit -m "My changes"
git push origin main
# Error: "Updates were rejected because the remote contains work..."
```

**Your work is NOT lost!** It's all saved locally. You just need to sync:

**Solution:**
```bash
git pull origin main    # Pull latest changes from GitHub
# Git will merge automatically if no conflicts
# If there are conflicts, Git will tell you (see Scenario 3)
git push origin main    # Now push your changes
```

**What `git pull` does:**
- Downloads changes from GitHub
- Merges them with your local changes
- Creates a merge commit (or auto-merges if no conflicts)
- Your changes + GitHub changes = combined result

**After pull + push, everything is synced!**

### Scenario 3: Merge Conflicts (Both Computers Have Changes)

**If you and someone else (or you on different computers) edited the same file:**

```bash
git pull origin main
# Git shows: "CONFLICT (content): Merge conflict in filename.py"
```

**How to resolve:**

1. **Open the conflicted file** - Git marks conflicts like this:
   ```python
   <<<<<<< HEAD
   # Your changes (from current computer)
   code_you_wrote()
   =======
   # Changes from GitHub (other computer)
   code_from_other_computer()
   >>>>>>> origin/main
   ```

2. **Edit the file** to keep what you want:
   ```python
   # Keep both, or choose one, or combine
   code_you_wrote()
   code_from_other_computer()
   ```

3. **Mark as resolved**:
   ```bash
   git add filename.py    # Mark conflict as resolved
   git commit -m "Resolve merge conflict in filename.py"
   git push origin main
   ```

**Tip**: To avoid conflicts, always `git pull` before starting work!

---

## Important: Your Work is Always Saved Locally!

**Key Point**: Even if you forget to pull, your changes are **always saved locally** in your Git repository. Nothing is lost!

- ✅ **Local commits** = Saved to your computer's Git repository
- ✅ **Local `main` branch** = Your changes are here
- ⚠️ **Remote `main` branch** (GitHub) = May have different/newer changes

**What happens if you forget to pull:**
1. Your changes are saved locally ✅
2. GitHub might have newer changes from your other computer
3. When you push, Git will ask you to pull first (to merge changes)
4. After pulling, your local changes + GitHub changes = combined
5. Then you can push everything together

**Bottom line**: Your work is safe! Git just wants you to sync before pushing.

---

## Best Practices

### 1. **Pull Before You Start**
Always pull latest changes before making new changes:
```bash
git pull origin main
```

**Why?** Prevents merge conflicts and keeps everything in sync.

### 2. **Commit Frequently**
Don't wait until the end of the day. Commit logical units of work:
- ✅ Good: `git commit -m "Add compute_features function"`
- ❌ Bad: `git commit -m "Lots of changes"` (after 2 days of work)

### 3. **Write Clear Commit Messages**
Describe **what** you changed and **why**:
- ✅ Good: `"Fix sliding window bug in predict_wooded_dl.py"`
- ✅ Good: `"Update README with GCS workflow instructions"`
- ❌ Bad: `"fix"` or `"update"`

### 4. **Push Regularly**
Push your commits to GitHub regularly (at least once per work session):
```bash
git push origin main
```

### 5. **Check Status Before Committing**
See what you've changed:
```bash
git status              # See which files changed
git diff               # See actual changes (detailed)
git diff --staged      # See staged changes
```

---

## Useful Git Commands

### Check Current Status
```bash
git status              # What files changed?
git log --oneline       # Recent commits
git log --oneline -5    # Last 5 commits
```

### See What Changed
```bash
git diff                # Unstaged changes
git diff --staged       # Staged changes
git diff HEAD           # All changes since last commit
```

### Undo Changes (Before Committing)
```bash
git restore filename.py           # Discard changes to file
git restore .                     # Discard ALL changes (careful!)
git restore --staged filename.py  # Unstage file (keep changes)
```

### Undo Last Commit (Keep Changes)
```bash
git reset --soft HEAD~1   # Undo commit, keep changes staged
git reset HEAD~1          # Undo commit, keep changes unstaged
```

### View History
```bash
git log                    # Full commit history
git log --oneline          # One line per commit
git log --graph --oneline  # Visual branch history
```

### Compare with Remote
```bash
git fetch origin           # Get remote info (doesn't merge)
git status                 # See if you're ahead/behind
git log HEAD..origin/main  # See commits on remote you don't have
```

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub (Remote)                        │
│              Single source of truth                      │
└─────────────────────────────────────────────────────────┘
                    ↕ Pull / Push
    ┌──────────────────┴──────────────────┐
    │                                      │
┌───▼────────┐                      ┌─────▼──────┐
│  Laptop    │                      │  Desktop   │
│            │                      │            │
│ 1. git pull│                      │ 1. git pull│
│ 2. Edit    │                      │ 2. Edit    │
│ 3. Commit  │                      │ 3. Commit  │
│ 4. Push    │                      │ 4. Push    │
└────────────┘                      └────────────┘
```

**Key Point**: Both computers work on the same `main` branch. Git syncs changes through pull/push.

---

## Example: Complete Work Session

### Morning on Laptop
```bash
cd "C:\Users\aeaturu\Desktop\WORK 2026 February\wooded area mapping"
git pull origin main                    # Get latest
# Edit files...
git add compute_features.py
git commit -m "Add EVI computation to compute_features"
git push origin main                    # Share changes
```

### Afternoon on Desktop
```bash
cd "C:\Users\aeaturu\Desktop\wooded-area-mapping"  # Different path OK
git pull origin main                    # Get laptop changes
# Continue working...
git add train_wooded_multi_scene.py
git commit -m "Fix patch extraction bug"
git push origin main                    # Share changes
```

### Next Day on Laptop
```bash
git pull origin main                    # Get desktop changes from yesterday
# Now you have everything!
```

---

## Troubleshooting

### "Your branch is ahead of 'origin/main'"
**Meaning**: You have local commits not pushed yet.
**Solution**: `git push origin main`

### "Your branch is behind 'origin/main'"
**Meaning**: GitHub has commits you don't have locally.
**Solution**: `git pull origin main`

### "Diverged branches"
**Meaning**: Both local and remote have different commits.
**Solution**: 
```bash
git pull origin main    # This will merge or show conflicts
# Resolve conflicts if any, then:
git push origin main
```

### Accidentally committed large file
```bash
# Remove from Git (keep file locally)
git rm --cached large_file.tif
git commit -m "Remove large file from Git"
git push origin main
```

---

## Quick Reference Card

**Start of work session:**
```bash
git pull origin main
```

**After making changes:**
```bash
git add .
git commit -m "Clear description"
git push origin main
```

**End of work session:**
```bash
git push origin main    # Make sure everything is pushed!
```

**Switch computers:**
```bash
git pull origin main    # Get latest changes
```

---

## Summary

- ✅ **One branch** (`main`) - not separate branches per computer
- ✅ **Pull before work** - always get latest changes
- ✅ **Commit frequently** - logical units of work
- ✅ **Push regularly** - share your changes
- ✅ **Clear messages** - describe what/why you changed

**Remember**: Git is a synchronization tool. Pull to get updates, push to share your work!
