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
def key(name):
    k = re.sub(r'\s*\(.*?\)', '', name).strip().lower()
    return re.sub(r'\s+ai$', '', k)
p = f'{ROOT}/index.html'
s = open(p).read()
row = re.search(r'<div class="logos"[^>]*>(.*?)</div>', s, re.S).group(1)
seen = {}
for t in re.findall(r'<span[^>]*>([^<]+)</span>', row):
    for part in t.split('/'):
        seen[key(part)] = f'top row ({t.strip()})'
blocks, skipped = [], []
for cat, items in CATS:
    keep = []
    for it in items:
        k = key(it)
        if k in seen: skipped.append(f'{it}  ->  already in {seen[k]}'); continue
        seen[k] = cat; keep.append(it)
    if not keep: continue
    lis = ''.join(
        f'<li>{html.escape(m.group(1))}<i>{html.escape(m.group(2))}</i></li>' if (m := re.match(r'(.+?)\s*\((.+)\)$', it)) else f'<li>{html.escape(it)}</li>'
        for it in keep)
    blocks.append(f'    <div class="tcat"><h3>{html.escape(cat)}<small>{len(keep)}</small></h3><ul>{lis}</ul></div>')
grid = '  <div class="toolcats">\n' + '\n'.join(blocks) + '\n  </div>\n'
s = re.sub(r'  <div class="toolcats">.*?\n  </div>\n', '', s, flags=re.S)
s = re.sub(r'(<div class="logos"[^>]*>.*?</div>\n)', lambda m: m.group(1) + grid, s, count=1, flags=re.S)
open(p, 'w').write(s)
print('added', sum(b.count('<li>') for b in blocks), 'tools in', len(blocks), 'categories')
print('skipped as duplicates:'); print('\n'.join('  ' + x for x in skipped))
