# Cursor Agent Conversations: What Syncs and What Doesn't

## Quick Answer

**Agent conversations are NOT synced between computers.** Each machine has its own conversation history stored locally.

---

## What Syncs Through Git

✅ **Code files** - All `.py`, `.md`, `.txt`, `.sh` files  
✅ **Documentation** - README, guides, etc.  
✅ **Configuration** - `.gitignore`, `requirements.txt`, etc.  
✅ **Project structure** - Folders, file organization

---

## What Does NOT Sync

❌ **Cursor Agent Conversations** - Stored locally per machine  
❌ **Cursor Settings** - Editor preferences, themes, etc.  
❌ **Python Virtual Environments** - `.venv/` folder (recreate on each machine)  
❌ **Large Data Files** - TIFF files, model checkpoints (use GCS)

---

## Where Agent Conversations Are Stored

**Windows Location:**
```
C:\Users\YOUR_USERNAME\.cursor\projects\PROJECT_ID\agent-transcripts\
```

Each conversation is stored as a JSON file with a unique ID.

**Important**: These files are:
- Stored locally on each computer
- Not included in Git (not part of your repository)
- Not synced between machines

---

## Why This Design?

1. **Privacy**: Conversations may contain sensitive information
2. **Size**: Conversation history can be large
3. **Machine-specific**: Each computer has its own context
4. **Focus**: Git is for code, not chat history

---

## How to Share Important Information

If you need to share important decisions or information from agent conversations:

### 1. Document in README.md
```markdown
## Key Decisions
- Using U-Net architecture for semantic segmentation
- Training on 3-10 manually labeled scenes
- Using GCS for data storage
```

### 2. Add to GETTING_STARTED.md
```markdown
## Important Notes
- Always pull before starting work
- Data files stay in GCS, not Git
```

### 3. Code Comments
```python
# Note: This function uses NDVI threshold of 0.4 based on testing
# See conversation from 2026-02-19 for details
def compute_wooded_area(image):
    ...
```

### 4. Create Documentation Files
- `ARCHITECTURE.md` - System design decisions
- `DECISIONS.md` - Important choices and rationale
- `TROUBLESHOOTING.md` - Common issues and solutions

---

## Workflow Recommendations

### On Each Computer

1. **Clone repository** (first time):
   ```bash
   git clone https://github.com/YOUR_USERNAME/wooded-area-mapping.git
   ```

2. **Start new agent conversation** - Each machine has fresh context

3. **Reference documentation** - Use README.md, guides, code comments

4. **Document important decisions** - Update README or create docs

### If You Need Past Conversation Context

1. **Check documentation** - Most important info should be documented
2. **Check code comments** - Implementation details are in code
3. **Ask agent again** - Agent can read your code/docs and provide context
4. **Manual copy** - If absolutely necessary, copy relevant parts from transcript files

---

## Best Practices

### ✅ Do:
- Document important decisions in README.md
- Add code comments explaining "why"
- Keep guides updated (GETTING_STARTED.md, etc.)
- Commit documentation changes to Git

### ❌ Don't:
- Rely on agent conversation history being available
- Expect conversations to sync between machines
- Put sensitive information in conversations (if you need it documented)

---

## Summary

- **Agent conversations**: Local to each machine, not synced
- **Code & documentation**: Synced through Git ✅
- **Solution**: Document important info in README/docs
- **Each computer**: Has its own agent conversation history

**Remember**: The agent can always read your code and documentation to understand context, even without past conversations!
