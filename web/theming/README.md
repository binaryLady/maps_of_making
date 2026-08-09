# Optional theming & whitelabel layer

Off by default. Shipping this directory changes nothing: with no
`data-mom-theme` attribute and no `/site.config.json`, every page renders the
zine look exactly as before.

## Opting in (deployers)

1. Copy `site.config.example.json` to `web/site.config.json` (keep it out of
   version control if it identifies your deployment).
2. Set what you want:
   - `name` / `tagline` / `page_title` — brand text replacing the defaults
   - `theme_default` — `""` (zine) or `"dark"` (neutral graphite)
   - `tokens` — any `--mom-*` custom-property overrides; this is where a
     deployment's whole visual identity lives (colors, radius, shadow)
3. Visitors can override the theme per browser via
   `MOMTheme.apply('dark')` / `MOMTheme.apply('')` — wire it to any control.

## Design contract

- Tokens are the only place a themed value may be defined
  (`web/theming/tokens.css`); the layer skins the map through its existing
  chrome variables and never touches the semantic pin colors (green = alive,
  red = broken, cobalt = claimed).
- Everything is fail-soft: a missing or invalid config file simply yields the
  upstream defaults.
