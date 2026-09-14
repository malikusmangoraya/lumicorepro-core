# Design Vault

The Design Vault turns **legally-obtained design assets** (e.g. a HorizonX UI
kit downloaded under your subscription, or an in-house Figma/HTML export) into
design systems the LumicorePro agent can apply to generated projects.

## How it works

Each subfolder under `registry/design-vault/` is one design source. The agent
scans them and registers each as a usable `ui_style`.

```
registry/design-vault/
  horizonx/          <- your HorizonX / paid kit exports live here
    style-tokens.json   <optional> hand-curated tokens (most accurate)
    any-page.html       <optional> auto-extracted design language
  my-brand/           <- your own design system
    style-tokens.json
```

The agent reads the design language (colors → palette, fonts, radii/shadows →
CSS) and applies it via `restyle_project(project, name, '<source>')`. Only the
**extracted tokens** are registered — no copyrighted source file is stored,
redistributed, or shipped.

## Using it

1. After downloading a HorizonX asset (HTML / Figma export), drop the HTML
   file into `registry/design-vault/horizonx/`.
2. For Figma-only files: copy your Figma colors/fonts/radii into a
   `style-tokens.json` using the sample in this folder.
3. Trigger a rescan:
   ```bash
   cd ai-agent && python -c "from agent.design_vault import refresh; print(refresh())"
   ```
4. Now `ui_style='horizonx'` (or any source name) is live. Prompt the agent
   with `use the horizonx design kit` and it will apply it automatically.

## License note

HorizonX source files come with a commercial license that lets you use them in
personal/client work but **not resell or redistribute the files**. This vault
respects that: it only ever extracts *design tokens* (colors/fonts/primitives)
locally for the agent — it never copies or embeds the kit's code into this
repository or into shipped projects.