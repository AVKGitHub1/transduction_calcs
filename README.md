# Transduction Calculator

Static web version of the transduction GUI. The website runs fully in the
browser and uses the hard-coded Rabi dipole calculation from
`rabi_freq_HardCoded.py`.

For the deployed website, update the web dipoles in `app.js`:

```js
const DIPOLES_EA0 = {
  blue: -6.93809e-3,
  uv: 1.70762e-3,
};
```

## GitHub Pages

This repo includes a GitHub Actions workflow at
`.github/workflows/deploy-pages.yml`.

To publish:

1. Push the repo to GitHub.
2. In the repo settings, open **Pages**.
3. Set **Build and deployment** to **GitHub Actions**.
4. Push to `main` or `master`, or run the workflow manually.

The published app entry point is `index.html`.
