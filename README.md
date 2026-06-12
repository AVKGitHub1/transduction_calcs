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
d_opt = 2.98915
```

All dipoles are in atomic units, `e a0`.

## Single-Atom Cavity Coupling

Choose **Calculate from mode volume** under **Optical Single-Atom g**, then enter
the optical mode volume in `mm^3`. The calculator uses the hard-coded
`5S1/2, mj=1/2 -> 5P3/2, mj=3/2` dipole (`2.98915 e a0`) at `780.24 nm` and
reports `g / 2 pi` in kHz. The manual `gopt` input remains available.

The same calculation can be called directly from Python:

```python
from rabi_freq_HardCoded import single_atom_g_optical

g_khz = single_atom_g_optical(0.083e-9)["g_kHz"]
```

## GitHub Pages

This repo includes a GitHub Actions workflow that publishes only the static web
files: `index.html`, `styles.css`, and `app.js`.

To publish:

1. Push the repo to GitHub.
2. In the repo settings, open **Pages**.
3. Set **Build and deployment** to **GitHub Actions**.
4. Push to `main` or `master`, or run the workflow manually.

The published app entry point is `index.html`.
