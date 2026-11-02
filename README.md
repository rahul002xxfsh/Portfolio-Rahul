# Portfolio Rahul

A dark, cinematic editor and VFX portfolio where 24 AI-agent cursors build the page in front of you as you scroll.

No framework and no build step: `index.html`, `styles.css`, `app.js` and `config.js`.

## Run locally

```bash
python3 -m http.server 4173
```

Then open http://127.0.0.1:4173.

## Make it yours

- **Name and contact details:** edit `config.js`. The email, Instagram handle and phone are placeholders.
- **Portrait:** replace `assets/art/portrait.png` with your own transparent cut-out (1200×1400).
- **Project frames:** replace `office.jpg`, `trailer.jpg`, `city.jpg` and `clay.jpg` in `assets/art/`. `city.jpg` and `clay.jpg` are the after and before sides of the comparison slider.
- **Copy:** awards, client logos, education and timeline text live in `index.html` and are sample content.

`tools/art.html` and `tools/render-art.sh` regenerate the stand-in artwork.

## How the build animation works

`app.js` treats every element marked `data-l` as one of 134 layers. An agent claims a layer as it scrolls into view and takes it from blueprint box to finished element. When every layer is done, the agents circle the showreel card and the status pill offers Replay.

Visitors with Reduce Motion enabled get the finished page straight away, plus a Play build button.

Fonts are Anton, Kaushan Script, Inter Tight and Manrope, self-hosted under the SIL Open Font License (see `assets/fonts/`).
