"""Guard against an instruction file being emptied or losing a step (this happened once, 2026-10-10)."""
from familyops import ROOT

REQUIRED = {
    ".claude/skills/family-digest/SKILL.md": ["## Step 1a", "## Step 1b", "## Step 2 ", "## Step 2b", "## Step 2c ",
                                              "## Step 2c-ii", "## Step 2d", "## Step 3", "## Step 4", "## Step 5",
                                              "## Step 6", "## Run report"],
    ".claude/skills/daily-scoop/SKILL.md": ["## Step 7", "7a", "7b", "7c", "7d", "7e"],
    "CLAUDE.md": ["## Hard rules", "## Shadow mode"],
    "data/family.md": ["Established child facts", "bus", "Child attribution"],
    "scoop/README.md": ["NEW STANDING RULES", "NEVER REPEAT", "edition.json fields"],
    ".claude/skills/family-update/SKILL.md": ["## Steps", "data/"],
    ".claude/skills/newspaper-design/SKILL.md": ["## Steps", "scoop/"],
    ".claude/skills/digest-format/SKILL.md": ["## Steps", "check-email"],
    ".claude/skills/dashboard-design/SKILL.md": ["## Steps", "state/"],
    "data/CLAUDE.md": ["single source of truth"],
    "docs/HOW-TO-UPDATE.md": ["/family-update", "/newspaper-design", "/digest-format", "/dashboard-design"],
}


def test_instruction_files_complete():
    for path, needles in REQUIRED.items():
        text = (ROOT / path).read_text()
        assert len(text) > 300, f"{path} looks truncated ({len(text)} chars)"
        for n in needles:
            assert n in text, f"{path} is missing '{n}'"


def test_sunday_school_kids():
    import yaml
    fam = yaml.safe_load((ROOT / "data/family.yaml").read_text())
    assert fam["sunday_school"]["kids"] == ["Ari", "Elle"]
