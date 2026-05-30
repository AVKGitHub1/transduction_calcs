# Transduction Calculator

The physics can be seen at [Notion Derivation Page](https://www.notion.so/Efficiency-Function-Derivation-36eee2c01b6180728fb7e5bccfe16d82)

Browser-deployable version of the transduction GUI. The web app runs as static
HTML/CSS/JavaScript, so it can be published directly with GitHub Pages and does
not need a Python server.

The website mirrors the main GUI controls, plots conversion efficiency, supports
CSV parameter import/export, and can download the plot as PNG.

## Files

- `index.html`: web app entry point
- `styles.css`: web app layout and styling
- `app.js`: browser-side calculations, plotting, CSV, and PNG export
- `gui.py`: desktop PyQt GUI
- `rabi_freq.py`: ARC-backed Rabi calculation
- `rabi_freq_HardCoded.py`: Python hard-coded dipole calculation
- `.github/workflows/deploy-pages.yml`: GitHub Pages deployment workflow

## Local Use

Open `index.html` directly in a browser. No build step is required.

The static web app always uses the hard-coded dipole calculation. ARC is a
Python dependency and is only available in the desktop GUI path.

## Updating Dipoles

For the deployed website, update the web dipoles in `app.js`:

```js
const DIPOLES_EA0 = {
  blue: -6.93809e-3,
  uv: 1.70762e-3,
};
```

For the Python hard-coded path, update the matching values in
`rabi_freq_HardCoded.py`:

```python
d_b = -6.93809e-03
d_UV = 1.70762e-03
```

Both sets are in atomic units, `e a0`.

## GitHub Pages

This repo includes a GitHub Actions workflow that publishes only the static web
files: `index.html`, `styles.css`, and `app.js`.

To publish:

1. Push the repo to GitHub.
2. In the repo settings, open **Pages**.
3. Set **Build and deployment** to **GitHub Actions**.
4. Push to `main` or `master`, or run the workflow manually.

The published app entry point is `index.html`.
