#!/usr/bin/env python3
"""Downloads the public Notion portfolio pages into tools/notion/*.json so build_cases.py can render them."""
import json, os, sys, time, urllib.request
BASE = 'https://grape-frog-a9c.notion.site/api/v3/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notion')
PROJECTS = {
 'zeta-pluxee':'3f963e415d3880ac80eac021d57a8644','brandfolio-ai':'26363e415d3881a2bcede440e0eb9382',
 'temu-teardown':'26563e415d388034a5fee351ce803ff9','upi-teardown':'26a63e415d388076ae60e073ef814fc1',
 'udchalo-teardown':'27b63e415d3880e48e2fe31ec1f62c14','blinkit-research':'28663e415d388004bd39c5e700aae894',
 'pm-lifecycle':'28663e415d388044b477f831a67b86c8','woco-goal-module':'27b63e415d38809baeaccdde3d14fd64',
 'student-tracker':'28563e415d3880288506c9e4046b289f','stick-dating':'2a363e415d3880e6922ae3c3745fb7f0',
 'indus-app-store':'2b563e415d388018a23bc4ec0fbf0bf8','smart-spending':'2b563e415d38802eb591e26b3a2d9fd6',
 'gatepass':'40f63e415d388138a542c7f09df6d285',
 'brandfolio-full':'26363e415d38813c949dd433eda01d69','exp-brandfolio':'26363e415d38810e8b81d4cc54a1a61b','exp-sapmen':'26363e415d3881e9bfa1e15d0c31958e',
 'exp-pawzz':'26363e415d3881e6ba3ee45665c4a723','home':'26363e415d3880919846df2ca2bbb7ba',
}
def dash(i): return f'{i[:8]}-{i[8:12]}-{i[12:16]}-{i[16:20]}-{i[20:]}'
def post(path, body):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(req, timeout=40))
def pull(pid):
    blocks, cursor, chunk = {}, {'stack': []}, 0
    while True:
        d = post('loadCachedPageChunk', {'page': {'id': pid}, 'limit': 100, 'cursor': cursor, 'chunkNumber': chunk, 'verticalColumns': False})
        blocks.update(d['recordMap'].get('block', {}))
        cursor = d.get('cursor') or {'stack': []}
        chunk += 1
        if not cursor.get('stack'): return blocks
        time.sleep(.25)
os.makedirs(OUT, exist_ok=True)
for slug, raw in PROJECTS.items():
    pid = dash(raw)
    blocks = pull(pid)
    json.dump({'id': pid, 'blocks': blocks}, open(f'{OUT}/{slug}.json', 'w'))
    print(slug, len(blocks))
    time.sleep(.3)
