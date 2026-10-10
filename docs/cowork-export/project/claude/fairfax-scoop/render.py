from playwright.sync_api import sync_playwright
import sys
out=sys.argv[1]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto("file://"+__import__("os").path.abspath("gazette.html")+"")
    pg.pdf(path=out,format="Letter",margin=dict(top="0.3in",bottom="0.3in",left="0.3in",right="0.3in"),print_background=True)
    # overflow check: column content height vs available
    print(pg.evaluate("[...document.querySelectorAll('.col')].map(c=>{let k=[...c.children].reduce((a,e)=>Math.max(a,e.getBoundingClientRect().bottom),0);return Math.round(k)+' / '+Math.round(c.getBoundingClientRect().bottom)})"))
    b.close()
