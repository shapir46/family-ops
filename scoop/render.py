from playwright.sync_api import sync_playwright
import json, os, sys

# Column fill rule (Jacob, 2026-10-10): every column ends close to its bottom, filled with real content.
# A column is OK when nothing spills past it (scrollHeight <= clientHeight) and its content ends
# no more than MAX_GAP pixels above the column bottom.
MAX_GAP = 40      # more empty space than this at the bottom of a column = UNDERFILLED

out = sys.argv[1]
with sync_playwright() as p:
    exe = os.environ.get("CHROMIUM_PATH") or ("/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None)
    b = p.chromium.launch(executable_path=exe); pg = b.new_page(); pg.goto("file://" + os.path.abspath("gazette.html"))
    pg.pdf(path=out, format="Letter", margin=dict(top="0.3in", bottom="0.3in", left="0.3in", right="0.3in"), print_background=True)
    cols = pg.evaluate("[...document.querySelectorAll('.col')].map(c=>{let k=[...c.children].reduce((a,e)=>Math.max(a,e.getBoundingClientRect().bottom),0);"
                       "let r=c.getBoundingClientRect();return [Math.round(k), Math.round(r.bottom - parseFloat(getComputedStyle(c).paddingBottom)), c.scrollHeight - c.clientHeight]})")
    b.close()

print([f"{k} / {bot}" for k, bot, _ in cols])          # content bottom / column bottom, one pair per column
verdicts = []
for i, (k, bot, spill) in enumerate(cols, 1):
    gap = bot - k
    v = "OVERFLOW" if spill > 0 or gap < 0 else "UNDERFILLED" if gap > MAX_GAP else "OK"
    verdicts.append({"column": i, "content": k, "bottom": bot, "gap_px": gap, "verdict": v})
ok = all(v["verdict"] == "OK" for v in verdicts)
print("LAYOUT:", "OK" if ok else "FIX " + ", ".join(f"col {v['column']} {v['verdict']} (gap {v['gap_px']}px)" for v in verdicts if v["verdict"] != "OK"))
print(json.dumps(verdicts))
