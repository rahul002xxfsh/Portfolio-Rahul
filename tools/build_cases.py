#!/usr/bin/env python3
"""Renders tools/notion/*.json into work/<slug>.html and writes data for the home page cards."""
import html, json, os, re, urllib.request, urllib.parse
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'tools', 'notion')
API = 'https://grape-frog-a9c.notion.site/api/v3/getSignedFileUrls'
PROJECTS = [
 ('zeta-pluxee','zeta-pluxee','Zeta: Pluxee Split Payments Case Study','New Feature PRD','Split checkout for Pluxee meal cards, so food goes on Pluxee and the rest on UPI or a card: research, MoSCoW, wireframes, technical design and rollout.'),
 ('brandfolio-ai','brandfolio-full','Brandfolio AI','Product Building','Two-sided platform connecting early-stage brands with creators: product, wireframes, live site and go-to-market plan.'),
 ('temu-teardown','temu-teardown','Temu: Onboarding and Trust Teardown','Problem Solving',"First-time-user teardown of Temu's cluttered onboarding, prize wheel and coupon flow, with prioritised fixes."),
 ('upi-teardown','upi-teardown','UPI Payment System Teardown','Teardown','How UPI works end to end, who it changed things for, and where it goes next.'),
 ('udchalo-teardown','udchalo-teardown','UdChalo: Favourite Product Teardown','Favourite Product','Pain points, prioritised improvements, metrics and risks for a travel platform built for defence personnel.'),
 ('blinkit-research','blinkit-research','Blinkit Delivery Partner App: Product Research','Problem Solving','15 days of research with a delivery partner on rewards, notifications and 10-minute delivery pressure.'),
 ('pm-lifecycle','pm-lifecycle','From Ideas to Impact: The Product Management Lifecycle','Projects','A visual map of how a product moves from stakeholder insights to validated, adopted features.'),
 ('woco-goal-module','woco-goal-module','WoCo Goal Module: HR Tech PRD','New Feature PRD','PRD for a standalone goal-management module with leaderboard integration, targeting a 60% cut in manual HR tracking.'),
 ('student-tracker','student-tracker','Student Tracker (Frappe)','Problem Solving','Problem brief, user stories, backlog and Sprint 1 plan for an NGO student-count tracking tool.'),
 ('stick-dating','stick-dating','Stick Dating App: Path to $10M ARR','Problem Solving','Product, marketing and expansion plan to take a dating app to $10M ARR in 6 months.'),
 ('indus-app-store','indus-app-store','Elevating User Engagement on Indus App Store','Projects','Short videos, reviews and dark mode drove +30% session duration and +20% retention.'),
 ('smart-spending','smart-spending','Smart Spending Insights for UPI Apps','New Feature PRD','Voice tags, category icons and AI auto-tagging to help users see where their money goes.'),
]
COLORS = {'red':'#ff7b86','blue':'#74b4ff','green':'#6fdc9b','yellow':'#f3cf6b','orange':'#f7a35c','purple':'#c3a1ff','pink':'#ff9cc7','brown':'#d0a98c','gray':'#9a97a0'}
SLUG = {}
def val(b):
    v = b.get('value', {})
    return v.get('value', v) if isinstance(v, dict) and 'type' not in v and 'value' in v else v
def rich(prop):
    out = []
    for seg in prop or []:
        s = html.escape(seg[0] if isinstance(seg[0], str) else '')
        for m in (seg[1] if len(seg) > 1 else []):
            k = m[0]
            if k == 'b': s = f'<strong>{s}</strong>'
            elif k == 'i': s = f'<em>{s}</em>'
            elif k == 'c': s = f'<code>{s}</code>'
            elif k == 's': s = f'<s>{s}</s>'
            elif k == '_': s = f'<u>{s}</u>'
            elif k == 'a':
                href = m[1]
                if href.startswith('/'): href = 'https://grape-frog-a9c.notion.site' + href
                s = f'<a href="{html.escape(href, True)}" target="_blank" rel="noopener">{s}</a>'
            elif k == 'h':
                c = str(m[1]).replace('_background', '')
                if c in COLORS: s = f'<span style="color:{COLORS[c]}">{s}</span>'
        out.append(s)
    return ''.join(out).replace('\n', '<br>')
class Page:
    def __init__(self, slug, blocks):
        self.slug, self.b, self.toc, self.first_img, self.imgs = slug, blocks, [], None, 0
    def get(self, i):
        return val(self.b[i]) if i in self.b else {}
    def image(self, v, i):
        src = v.get('format', {}).get('display_source') or ''
        if not src:
            p = v.get('properties', {}).get('source'); src = p[0][0] if p else ''
        cap = rich(v.get('properties', {}).get('caption'))
        if src.startswith('attachment:'):
            ext = os.path.splitext(src)[1].lower() or '.png'
            os.makedirs(f'{ROOT}/assets/case/{self.slug}', exist_ok=True)
            self.imgs += 1
            name = f'{self.imgs:02d}{ext}'
            path = f'{ROOT}/assets/case/{self.slug}/{name}'
            if not os.path.exists(path):
                r = urllib.request.Request(API, json.dumps({'urls':[{'url':src,'permissionRecord':{'table':'block','id':i}}]}).encode(), {'content-type':'application/json','user-agent':'Mozilla/5.0'})
                url = json.load(urllib.request.urlopen(r, timeout=30))['signedUrls'][0]
                open(path, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers={'user-agent':'Mozilla/5.0'}), timeout=60).read())
            src = f'../assets/case/{self.slug}/{name}'
        self.first_img = self.first_img or src
        alt = html.escape(re.sub('<[^>]+>', '', cap)) or 'Case study image'
        return f'<figure><img src="{html.escape(src, True)}" alt="{alt}" loading="lazy">' + (f'<figcaption>{cap}</figcaption>' if cap else '') + '</figure>'
    def kids(self, v):
        return self.render(v.get('content', []))
    def render(self, ids):
        out, i = [], 0
        ids = [x for x in ids if x in self.b and self.get(x).get('alive', True)]
        while i < len(ids):
            v = self.get(ids[i]); t = v.get('type')
            if t in ('bulleted_list', 'numbered_list', 'to_do'):
                tag = 'ol' if t == 'numbered_list' else 'ul'; items = []
                while i < len(ids) and self.get(ids[i]).get('type') == t:
                    w = self.get(ids[i]); items.append(f"<li>{rich(w.get('properties', {}).get('title'))}{self.kids(w)}</li>"); i += 1
                out.append(f'<{tag}>' + ''.join(items) + f'</{tag}>'); continue
            out.append(self.block(ids[i], v, t)); i += 1
        return ''.join(out)
    def block(self, i, v, t):
        p = v.get('properties', {}); title = rich(p.get('title'))
        color = v.get('format', {}).get('block_color', '') or ''
        if t == 'text':
            if not title: return ''
            st = f' style="color:{COLORS[color]}"' if color in COLORS else ''
            return f'<p{st}>{title}</p>{self.kids(v)}'
        if t in ('header', 'sub_header', 'sub_sub_header'):
            n = {'header':2,'sub_header':2,'sub_sub_header':3}[t]
            plain = re.sub('<[^>]+>', '', title); hid = f"s{len(self.toc)+1}"
            if n == 2: self.toc.append((hid, plain))
            return f'<h{n} id="{hid}">{title}</h{n}>'
        if t == 'quote': return f'<blockquote>{title}{self.kids(v)}</blockquote>'
        if t == 'divider': return '<hr>'
        if t == 'callout':
            ic = v.get('format', {}).get('page_icon', '')
            ic = ic if ic and not ic.startswith(('http','/','attachment')) else ''
            return f'<aside class="callout"><span>{ic}</span><div>{title}{self.kids(v)}</div></aside>'
        if t == 'toggle': return f'<details><summary>{title}</summary>{self.kids(v)}</details>'
        if t == 'image': return self.image(v, i)
        if t == 'code':
            lang = (p.get('language') or [['']])[0][0].lower(); text = html.escape(''.join(s[0] for s in p.get('title', [])))
            return f'<pre class="mermaid">{text}</pre>' if lang == 'mermaid' else f'<pre><code>{text}</code></pre>'
        if t == 'column_list':
            return '<div class="cols">' + ''.join(f'<div>{self.kids(self.get(c))}</div>' for c in v.get('content', [])) + '</div>'
        if t == 'column': return self.kids(v)
        if t == 'table':
            fmt = v.get('format', {}); order = fmt.get('table_block_column_order', [])
            head = fmt.get('table_block_column_header'); rows = []
            for n, r in enumerate(v.get('content', [])):
                row = self.get(r).get('properties', {}); cell = 'th' if head and n == 0 else 'td'
                rows.append('<tr>' + ''.join(f'<{cell}>{rich(row.get(c))}</{cell}>' for c in order) + '</tr>')
            return '<div class="tw"><table>' + ''.join(rows) + '</table></div>'
        if t == 'page':
            if v.get('id') in SLUG: return ''
            return f'<p><a href="https://grape-frog-a9c.notion.site/{v.get("id","").replace("-","")}" target="_blank" rel="noopener">{title}</a></p>'
        if t in ('bookmark', 'embed', 'video', 'file', 'pdf', 'figma', 'drive'):
            src = v.get('format', {}).get('display_source') or (p.get('link') or p.get('source') or [['']])[0][0]
            return f'<p><a href="{html.escape(src, True)}" target="_blank" rel="noopener">{title or html.escape(src)}</a></p>' if src else ''
        return ''
TPL = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | Rahul De</title><meta name="description" content="{desc}"><meta name="theme-color" content="#08080c">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../case.css"></head>
<body>
<header class="ctop"><a class="clogo" href="../index.html">RAHUL DE<i>.</i></a><a class="cback" href="../index.html#work">← All work</a></header>
<main class="cwrap">
<div class="chead"><p class="ckick">{num} / {goal}</p><h1>{title}</h1><p class="cdesc">{desc}</p><a class="cnotion" href="{nurl}" target="_blank" rel="noopener">View in Notion ↗</a></div>
<div class="cbody"><nav class="ctoc" aria-label="On this page">{toc}</nav><article class="prose">{body}</article></div>
<nav class="cnext"><a href="{nslug}.html"><small>Next case study</small><span>{ntitle} →</span></a></nav>
</main>
{mermaid}
</body></html>
'''
MERMAID = '''<script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs';mermaid.initialize({startOnLoad:true,theme:'dark',securityLevel:'strict',themeVariables:{primaryColor:'#1a1a22',primaryBorderColor:'#e5404f',primaryTextColor:'#f4f2f1',lineColor:'#a3a0a8',fontFamily:'Manrope, sans-serif'}});</script>'''
def main():
    os.makedirs(f'{ROOT}/work', exist_ok=True)
    cards = []
    for n, (slug, src, title, goal, desc) in enumerate(PROJECTS):
        d = json.load(open(f'{SRC}/{src}.json')); pg = Page(slug, d['blocks'])
        body = pg.render(pg.get(d['id']).get('content', []))
        if src == 'brandfolio-full':
            top = json.load(open(f'{SRC}/brandfolio-ai.json')); p0 = Page(slug, top['blocks'])
            intro = ''.join(p0.block(i, p0.get(i), p0.get(i).get('type')) for i in p0.get(top['id']).get('content', []) if p0.get(i).get('type') == 'text')
            body = intro + body
        body = re.sub(r'<aside class="callout">\s*<span></span><div></div></aside>', '', body)
        toc = ''.join(f'<a href="#{h}">{html.escape(t)}</a>' for h, t in pg.toc if t)
        nx = PROJECTS[(n + 1) % len(PROJECTS)]
        page = TPL.format(title=html.escape(title), desc=html.escape(desc), num=f'{n+1:02d}', goal=html.escape(goal), toc=toc, body=body, nslug=nx[0], ntitle=html.escape(nx[2]), nurl='https://grape-frog-a9c.notion.site/'+d['id'].replace('-',''), mermaid=MERMAID if 'class="mermaid"' in body else '')
        open(f'{ROOT}/work/{slug}.html', 'w').write(page)
        cards.append({'slug':slug,'title':title,'goal':goal,'desc':desc,'img':(pg.first_img or '').replace('../','')})
        words = len(re.sub('<[^>]+>',' ',body).split())
        print(f'{slug:20} {words:6} words  sections {len(pg.toc):3}  images {pg.imgs}')
    json.dump(cards, open(f'{ROOT}/tools/cards.json', 'w'), indent=1)
main()
