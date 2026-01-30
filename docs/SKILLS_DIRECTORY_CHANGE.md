# Skills Directory Structure Change

## 📋 Summary

Changed skills directory from **hidden** `.agents/skills/` to **visible** `skills/`

## 🤔 Why the Change?

### Problem with `.agents/` (Hidden Directory)

1. **Violates Unix Convention**
   - Dot-prefixed directories (`.xxx`) are for temporary/system files
   - Examples: `.git/`, `.cache/`, `.config/`
   - NOT for user content that needs version control

2. **Poor Visibility**
   - Hidden in `ls` (need `ls -la`)
   - Hidden in many IDEs by default
   - Hard for new developers to discover

3. **Confusing Intent**
   - Hidden = "Don't touch this"
   - But skills ARE user content
   - Should be visible and obvious

### Benefits of `skills/`

✅ **Visible**: Shows up in `ls`, file browsers, IDEs
✅ **Clear Intent**: Obviously contains skills
✅ **Git-Friendly**: Clearly tracked content
✅ **Unix Convention**: Non-hidden = user content
✅ **Discoverable**: Easy for new developers to find

## 📂 Directory Structure

```
agents/
├── skills/              # ← New location (visible)
│   ├── README.md
│   ├── pdf/
│   ├── pptx/
│   ├── web-design-guidelines/
│   └── ... (50 skills)
├── alpha/
├── docs/
└── ...
```

## 🔄 What Changed

| File | Change |
|------|--------|
| **All skill files** | Renamed: `.agents/skills/` → `skills/` |
| `.gitignore` | Only ignore `skills/.cache/` and `skills/.temp/` |
| `alpha/skills/*.py` | Updated default path to `Path("skills")` |
| `config.yaml` | Updated skills_dir to `"skills"` |
| Documentation | Updated all references |
| Scripts | Updated all references |

## 🎯 Impact

**Before**:
```bash
$ ls
README.md  alpha/  docs/  tests/  ...
# Skills hidden!
```

**After**:
```bash
$ ls
README.md  alpha/  docs/  skills/  tests/  ...
# Skills visible! ✅
```

## ⚠️ Breaking Change Notice

**For Users Upgrading**:

If you have an existing project with `.agents/skills/`:

```bash
# Option 1: Let git handle it
git pull  # Git will rename automatically

# Option 2: Manual migration
mv .agents/skills skills/
rm -rf .agents/
```

**For Scripts/Tools**:

- Update any hardcoded `.agents/skills` paths to `skills`
- Alpha code automatically uses new path
- `npx skills` tool may still expect `.agents/` (external tool limitation)

## 📖 Related Changes

This change is part of a larger skill system optimization:

1. ✅ Query Classification (REQ-SKILL-1)
2. ✅ Local-Only Matching (REQ-SKILL-2)
3. ✅ Lazy Loading (REQ-SKILL-3)
4. ✅ **Visible Directory Structure** (REQ-SKILL-4) ← This change
5. ⏳ Background Skill Evolution (REQ-SKILL-5) - Planned
6. ⏳ Background Skill Optimization (REQ-SKILL-6) - Planned

## 🔗 References

- Commit: 9d73769
- Previous Commit: 3927554 (Added top 50 skills)
- Documentation: [INSTALL_POPULAR_SKILLS.md](../INSTALL_POPULAR_SKILLS.md)
