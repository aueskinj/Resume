## Repository Blog (Static)

This repo now builds a clean, static blog that lists every public GitHub repository in `public_repos.json`. Each repo becomes its own page; forks also include a short plan for how they'll be adapted or improved.

### How it works
- `pyfiles/build_blog.py` loads `public_repos.json`, normalizes the data, and renders static pages into `dist/` using Jinja templates from `templates/`.
- Assets (CSS, images, JS) are copied into `dist/assets/` so the output can be hosted anywhere (GitHub Pages, Netlify, Cloudflare Pages).
- The landing page `index.html` points you to `dist/index.html` once built.

### Build the site
```bash
pip install jinja2
python pyfiles/build_blog.py
# Outputs to dist/
```

Then open `dist/index.html` in your browser or serve the folder:
```bash
python -m http.server --directory dist 8080
```

### Content rules
- **Forked repos**: pages show a "Planned changes" paragraph describing how the fork will be documented, tested, and tailored.
- **Non-forks**: pages focus on the description and metadata only.
- Tags are generated from languages, topics, and fork status for easy browsing.

### Structure
- `pyfiles/build_blog.py` — static site generator
- `templates/` — Jinja templates (`base`, `index`, `post`, `tags`)
- `assets/css/style.css` — blog styling
- `public_repos.json` — source data from the GitHub API
- `dist/` — generated output (created by the build script)

### Notes
- If `public_repos.json` changes, rerun the build script to refresh `dist/`.
- The previous terminal-style UI has been retired in favor of the blog format.
