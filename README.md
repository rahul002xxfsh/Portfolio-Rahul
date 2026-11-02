# Portfolio Rahul

Rahul De's product management portfolio, where 24 AI-agent cursors build the page in front of you as you scroll.

No framework: `index.html`, `styles.css`, `app.js` and `config.js`, plus 12 full case-study pages in `work/`.

## Run locally

```bash
python3 -m http.server 4173
```

Then open http://127.0.0.1:4173.

## Content

- **Contact details and links:** `config.js`.
- **Homepage copy:** `index.html`.
- **Case studies:** `work/*.html`, generated from the public Notion portfolio. To refresh them after editing Notion:

```bash
python3 tools/notion_pull.py
python3 tools/build_cases.py
```

- **Portrait:** `assets/art/portrait.png`. `tools/cutout.swift` removes a photo's background with Apple Vision.

## How the build animation works

`app.js` treats every element marked `data-l` as one of 134 layers. An agent claims a layer as it scrolls into view and takes it from blueprint box to finished element. When every layer is done, the agents circle the showreel card and the status pill offers Replay.

Visitors with Reduce Motion enabled get the finished page straight away, plus a Play build button.

Fonts are Anton, Kaushan Script, Inter Tight and Manrope, self-hosted under the SIL Open Font License (see `assets/fonts/`).
