#!/usr/bin/env python3
"""Builds the 'Tools I Build With' categories in index.html, skipping anything already listed in that section."""
import html, re, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CATS = [
 ('LLM Models', ['GPT (OpenAI)','Claude (Anthropic)','Gemini (Google)','Llama (Meta)','DeepSeek','Mistral','Grok (xAI)','Qwen (Alibaba)','Phi (Microsoft)','Command (Cohere)','Jamba (AI21 Labs)','Nemotron (NVIDIA)','GLM (Zhipu AI)','Kimi (Moonshot AI)']),
 ('AI Assistants & Research Tools', ['ChatGPT','Claude','Gemini','Perplexity','NotebookLM','Poe','You.com','Elicit','Consensus','Genspark']),
 ('AI Coding Tools & IDEs', ['Cursor','Windsurf','Visual Studio Code','GitHub Copilot','Replit','Lovable','Bolt.new','v0','Cline','Aider','Devin','Continue','OpenHands']),
 ('MCP Clients & Platforms', ['Claude Desktop','Cursor','ChatGPT','Visual Studio Code','Windsurf']),
 ('MCP Servers & Integrations', ['Figma MCP','Linear MCP','Jira MCP','Notion MCP','Slack MCP','GitHub MCP','Google Drive MCP','PostgreSQL MCP','Playwright MCP','Amplitude MCP','Mixpanel MCP']),
 ('Product Management Tools', ['Productboard','Jira Product Discovery','Linear','Notion AI','ClickUp']),
 ('Product Analytics & Data Tools', ['Mixpanel','Amplitude','PostHog','Google Analytics 4','Tableau','Power BI']),
 ('UI/UX Design & Prototyping Tools', ['Figma','FigJam','Framer','Relume']),
 ('Automation & AI Agent Platforms', ['n8n','Zapier']),
 ('Meeting Intelligence & Customer Research', ['Fireflies.ai']),
 ('AI & Developer Resources', ['Hugging Face','GitHub','Model Context Protocol Documentation','OpenAI API','Anthropic API']),
]
ICON = {
 'figma':'figma','lovable':'lovable','replit':'replit','cursor':'cursor','power bi':'powerbi','clickup':'clickup','jira':'jira','chatgpt':'openai','sora':'sora',
 'gpt':'openai','claude':'claude','gemini':'gemini','llama':'meta','deepseek':'deepseek','mistral':'mistral','grok':'grok','qwen':'qwen','phi':'microsoft','command':'cohere',
 'jamba':'ai21','nemotron':'nvidia','glm':'zhipu','kimi':'kimi','perplexity':'perplexity','notebooklm':'notebooklm','poe':'poe','windsurf':'windsurf',
 'visual studio code':'vscode','github copilot':'githubcopilot','v0':'v0','cline':'cline','devin':'devin','openhands':'openhands','claude desktop':'claude',
 'figma mcp':'figma','linear mcp':'linear','jira mcp':'jira','notion mcp':'notion','slack mcp':'slack','github mcp':'github','google drive mcp':'googledrive',
 'postgresql mcp':'postgresql','playwright mcp':'playwright','amplitude mcp':'amplitude','mixpanel mcp':'mixpanel','productboard':'productboard',
 'jira product discovery':'jira','linear':'linear','notion':'notion','mixpanel':'mixpanel','amplitude':'amplitude','posthog':'posthog',
 'google analytics 4':'googleanalytics','tableau':'tableau','figjam':'figma','framer':'framer','n8n':'n8n','zapier':'zapier','hugging face':'huggingface',
 'github':'github','model context protocol documentation':'mcp','openai api':'openai','anthropic api':'anthropic'}
def icon(name):
    f = ICON.get(key(name))
    if f and os.path.exists(f'{ROOT}/assets/icons/{f}.svg'):
        return f'<img src="assets/icons/{f}.svg" alt="" width="18" height="18" loading="lazy">'
    glyph = name[0].upper() if name[0].isalpha() else '&lt;/&gt;'
    return f'<b class="mono" aria-hidden="true">{glyph if not name[0].isalpha() else html.escape(glyph)}</b>'
def key(name):
    k = re.sub(r'\s*\(.*?\)', '', name).strip().lower()
    return re.sub(r'\s+ai$', '', k)
p = f'{ROOT}/index.html'
s = open(p).read()
m = re.search(r'(<div class="logos"[^>]*>)(.*?)(</div>)', s, re.S)
seen, spans = {}, []
for attrs, inner in re.findall(r'<span([^>]*)>(.*?)</span>', m.group(2), re.S):
    t = re.sub(r'<[^>]+>', '', re.sub(r'<b class="mono".*?</b>', '', inner)).strip()
    parts = [x.strip() for x in t.split('/')]
    for part in parts: seen[key(part)] = f'top row ({t})'
    spans.append(f'    <span{attrs}>' + ''.join(icon(x) for x in parts) + f'{html.escape(t)}</span>')
s = s[:m.start()] + m.group(1) + '\n' + '\n'.join(spans) + '\n  ' + m.group(3) + s[m.end():]
blocks, skipped = [], []
for cat, items in CATS:
    keep = []
    for it in items:
        k = key(it)
        if k in seen: skipped.append(f'{it}  ->  already in {seen[k]}'); continue
        seen[k] = cat; keep.append(it)
    if not keep: continue
    lis = ''.join(
        f'<li>{icon(it)}{html.escape(m.group(1))}<i>{html.escape(m.group(2))}</i></li>' if (m := re.match(r'(.+?)\s*\((.+)\)$', it)) else f'<li>{icon(it)}{html.escape(it)}</li>'
        for it in keep)
    blocks.append(f'    <div class="tcat"><h3>{html.escape(cat)}<small>{len(keep)}</small></h3><ul>{lis}</ul></div>')
grid = '  <div class="toolcats">\n' + '\n'.join(blocks) + '\n  </div>\n'
s = re.sub(r'  <div class="toolcats">.*?\n  </div>\n', '', s, flags=re.S)
s = re.sub(r'(<div class="logos"[^>]*>.*?</div>\n)', lambda m: m.group(1) + grid, s, count=1, flags=re.S)
open(p, 'w').write(s)
print('added', sum(b.count('<li>') for b in blocks), 'tools in', len(blocks), 'categories')
print('skipped as duplicates:'); print('\n'.join('  ' + x for x in skipped))
