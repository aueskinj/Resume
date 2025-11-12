## Terminal Portfolio

This repository now powers an interactive, terminal-themed portfolio for **Austin Kimuhu Njuguna (aueskinj)**. Instead of a static resume, visitors explore projects, forks, experiments, and language distribution through a command-line inspired interface with animations and keyboard shortcuts.

### Features
- ASCII banner boot sequence with subtle CRT/flicker effects
- REPL style command input with history (Up/Down) & tab autocomplete
- Dynamic loading of `repos.json` (fetched client-side, no build step)
- Filtering by language, fork status, and year
- Rich repo detail view with badges, metadata, and direct GitHub link
- ASCII bar charts for language distribution (`graph`)
- Activity timeline (`timeline`)
- Guided animated exploration (`explore`) with abort via Ctrl+C
- Random repo spotlight (`random`)
- Backend focus sections: `about`, `skills`

### Commands
```
help                Show help
ls [-l]             List repositories (optionally long form)
repo <name>         Show details of a repository (fuzzy prefix match)
open <name>         Open a repository on GitHub in a new tab
filter k=v [...]    Set filters (language=Python fork=true year=2025)
filter clear        Clear all filters
graph [lang]        ASCII language distribution
timeline            Recent repository activity
random              Show a random repository
explore             Animated guided tour of highlighted repos
about               Short personal / focus summary
skills              Backend / tooling stack
clear               Clear the screen
```

### Keyboard Shortcuts
- `Tab` autocomplete repo names
- `↑` / `↓` previous / next command history
- `Ctrl+C` abort long-running exploration (prints ^C)

### Data Source
The file `repos.json` is expected at the project root. It should be an array of GitHub repository objects (subset of the REST API shape). Only selected fields are used: `name`, `full_name`, `html_url`, `description`, `fork`, `language`, `pushed_at`, `updated_at`, `stargazers_count`, `default_branch`, and optionally `license`.

### Local Development
No build step required; it's all static.

#### Serve Locally (optional but recommended for fetch CORS behavior)
```bash
python3 -m http.server 8080
# Then open http://localhost:8080
```

Or use any static server (e.g. `npx serve .`). Opening the file directly works in most browsers, though some block `fetch` of local JSON depending on settings.

### Customization Ideas
- Add a worker-based search index for full-text search across README snippets
- Integrate pinned highlights with a `featured.json`
- Add ASCII sparkline commit histories per repo
- Persist filters & history in `localStorage`
- Add dark/light themes toggled by a command (`theme dark` / `theme light`)

### Accessibility
- Terminal output region uses `role=log` and `aria-live=polite`
- Input labeled; color contrast tuned for dark backgrounds

### Deployment
Host on any static hosting (GitHub Pages, Netlify, Cloudflare Pages). Ensure `repos.json` is refreshed periodically (GitHub Action or manual export).

### License
All code in this repository authored for the terminal interface is released under the MIT License unless otherwise noted. Original resume content superseded by this redesign.

---
Feel free to fork and adapt for your own terminal-style portfolio.
