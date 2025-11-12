"use strict";

(function () {
  const sel = (q, r = document) => r.querySelector(q);
  const out = sel('#output');
  const form = sel('#cmd');
  const input = sel('#cli');

  const state = {
    repos: [],
    byName: new Map(),
    filters: {},
    history: [],
    histIndex: -1,
    exploring: false,
    exploreAbort: null,
  };

  const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
  const scrollBottom = () => { out.scrollTop = out.scrollHeight; };
  const esc = (s) => s.replace(/[&<>]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  const fmtDate = (iso) => {
    try { return new Date(iso).toLocaleDateString(undefined, { year:'numeric', month:'short', day:'2-digit' }); } catch { return iso || ''; }
  };
  const pad = (s, n) => (s + ' '.repeat(n)).slice(0, n);

  function div(cls, text) {
    const d = document.createElement('div');
    if (cls) d.className = cls;
    if (text != null) d.textContent = text;
    return d;
  }

  function print(text = '', cls = 'line mono') {
    const line = div(cls);
    line.innerHTML = text;
    out.appendChild(line);
    scrollBottom();
    return line;
  }

  async function typeLine(text = '', cls = 'line mono') {
    const line = div(cls);
    out.appendChild(line);
    let buf = '';
    for (const ch of text) {
      buf += ch;
      line.textContent = buf;
      await sleep(6 + Math.random() * 14);
    }
    scrollBottom();
    return line;
  }

  function rule() {
    const r = div('rule');
    out.appendChild(r);
  }

  function badges(items) {
    return `<span class="badges">${items.map((t) => `<span class="badge">${esc(t)}</span>`).join(' ')}</span>`;
  }

  const banner = [
    '      ___           __           _           _           ',
    '     / _ | ___  __/ /__  __ _  (_)__  ___  (_)__  ___ _ ',
    '    / __ |/ _ \/ _  / _ \/  "_/ / / _ \/ _ \/ / _ \/ _ `/ ',
    '   /_/ |_|\___/\_,_/\___/_/\_\_/_/_//_/\___/_/_//_/\_,_/  ',
    '                                                         ',
  ].join('\n');

  async function boot() {
    await typeLine(banner, 'line banner');
    print(`<span class="dim">interactive portfolio</span> <span class="accent">//</span> backend-focused, repo-driven`);
    rule();
    print(`Type <span class="accent">help</span> to get started. Try <span class="accent">ls</span> or <span class="accent">explore</span>.`);
    print(`Quick keys: <span class="kbd">Tab</span> autocomplete, <span class="kbd">↑/↓</span> history, <span class="kbd">Ctrl+C</span> abort.`);
    rule();
  }

  async function loadData() {
    try {
      const res = await fetch('repos.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.repos = Array.isArray(data) ? data : [];
      state.byName.clear();
      for (const r of state.repos) {
        const key = (r.name || r.full_name || '').toLowerCase();
        if (key) state.byName.set(key, r);
      }
      const langs = new Set(state.repos.map(r => r.language).filter(Boolean));
      print(`${state.repos.length} repositories loaded ${langs.size ? badges([`${langs.size} languages`]) : ''}`);
    } catch (e) {
      print(`<span class="danger">Error:</span> Failed to load repos.json (${esc(String(e))}).`, 'line');
    }
  }

  // Filtering utilities
  function applyFilters(list) {
    const f = state.filters || {};
    return list.filter((r) => {
      if (f.language && (r.language || '').toLowerCase() !== String(f.language).toLowerCase()) return false;
      if (f.fork != null) {
        const want = String(f.fork).toLowerCase();
        if ((r.fork ? 'true' : 'false') !== want) return false;
      }
      if (f.year) {
        const y = (r.pushed_at || r.updated_at || '').slice(0,4);
        if (y !== String(f.year)) return false;
      }
      return true;
    });
  }

  function sortByRecent(list) {
    return [...list].sort((a, b) => new Date(b.pushed_at || b.updated_at || 0) - new Date(a.pushed_at || a.updated_at || 0));
  }

  function findRepo(name) {
    if (!name) return null;
    const key = name.toLowerCase();
    if (state.byName.has(key)) return state.byName.get(key);
    // fuzzy startsWith
    const matches = state.repos.filter(r => (r.name || '').toLowerCase().startsWith(key));
    if (matches.length === 1) return matches[0];
    if (matches.length > 1) return { __multiple: matches };
    return null;
  }

  function repoLine(r, long = false) {
    const name = r.name || r.full_name || 'unknown';
    const lang = r.language || 'misc';
    const star = r.stargazers_count || 0;
    const fork = r.fork ? 'fork' : 'orig';
    const dt = fmtDate(r.pushed_at || r.updated_at);
    if (!long) return `${name} <span class="dim">[${esc(lang)}]</span> <span class="accent">★</span>${star} <span class="muted">${fork}</span>`;
    return `${name}\n  <span class="dim">${esc(r.description || '—')}</span>\n  <span class="badge">${esc(lang)}</span> <span class="badge">${fork}</span> <span class="badge">★ ${star}</span> <span class="badge">${esc(r.default_branch || 'main')}</span>  <span class="dim">updated ${dt}</span>`;
  }

  function bar(n, max, width = 24, fill = '█') {
    const len = max ? Math.round((n / max) * width) : 0;
    return fill.repeat(len || (n ? 1 : 0));
  }

  // Commands
  const commands = {
    help() {
      print(`Available commands:`);
      print(`  <span class="accent">help</span>            Show this help`);
      print(`  <span class="accent">ls</span> [ -l ]       List repositories (respects filters)`);
      print(`  <span class="accent">repo</span> &lt;name&gt;     Show details for a repository`);
      print(`  <span class="accent">open</span> &lt;name&gt;     Open repo on GitHub`);
      print(`  <span class="accent">filter</span> k=v ...  Set filters (language=Python, fork=true, year=2025)`);
      print(`  <span class="accent">filter</span> clear     Clear filters`);
      print(`  <span class="accent">graph</span> [lang]    ASCII bar chart of languages`);
      print(`  <span class="accent">timeline</span>        Recent activity`);
      print(`  <span class="accent">random</span>           Jump to a random repo`);
      print(`  <span class="accent">explore</span>          Animated tour of highlighted repos`);
      print(`  <span class="accent">about</span>            Who I am (backend focus)`);
      print(`  <span class="accent">skills</span>           Backend stack + tooling`);
      print(`  <span class="accent">clear</span>            Clear screen`);
    },

    ls(flag) {
      const long = (Array.isArray(flag) ? flag : [flag]).includes('-l');
      const list = sortByRecent(applyFilters(state.repos));
      if (!list.length) { print(`<span class="muted">(no repositories match current filters)</span>`); return; }
      for (const r of list) { print(repoLine(r, long)); }
      if (state.filters && Object.keys(state.filters).length) {
        const f = Object.entries(state.filters).map(([k,v]) => `${k}=${v}`);
        print(`<span class="dim">filters:</span> ${badges(f)}`);
      }
    },

    repo(name) {
      const r = findRepo(name);
      if (!r) return print(`<span class="warn">Not found:</span> ${esc(name || '')}`);
      if (r.__multiple) {
        print(`<span class="warn">Ambiguous:</span> ${esc(name)} — did you mean:`);
        for (const x of r.__multiple.slice(0, 8)) print(`  ${repoLine(x)}`);
        return;
      }
      rule();
      print(`<span class="bold">${esc(r.name || r.full_name || 'repository')}</span>`);
      if (r.description) print(`<span class="dim">${esc(r.description)}</span>`);
      const chips = [
        r.language || 'misc',
        r.fork ? 'fork' : 'orig',
        `★ ${r.stargazers_count || 0}`,
        r.default_branch || 'main',
      ];
      print(badges(chips));
      const updated = fmtDate(r.pushed_at || r.updated_at);
      const lic = r.license && (r.license.name || r.license.spdx_id);
      print(`<span class="dim">updated ${updated}${lic ? ` • license ${esc(lic)}` : ''}</span>`);
      if (r.html_url) print(`<a class="link" href="${esc(r.html_url)}" target="_blank" rel="noreferrer noopener">${esc(r.html_url)}</a>`);
      rule();
    },

    open(name) {
      const r = findRepo(name);
      if (!r || r.__multiple) return commands.repo(name);
      if (r.html_url) {
        print(`opening <span class="link">${esc(r.html_url)}</span> ...`);
        window.open(r.html_url, '_blank', 'noopener,noreferrer');
      } else {
        print(`<span class="warn">No URL</span> for ${esc(r.name || '')}`);
      }
    },

    filter(...pairs) {
      if (!pairs || !pairs.length) {
        if (!Object.keys(state.filters).length) return print(`<span class="muted">(no filters set)</span>`);
        const f = Object.entries(state.filters).map(([k,v]) => `${k}=${v}`);
        return print(`<span class="dim">filters:</span> ${badges(f)}`);
      }
      if (pairs.length === 1 && String(pairs[0]).toLowerCase() === 'clear') {
        state.filters = {};
        print(`<span class="success">filters cleared</span>`);
        return;
      }
      for (const p of pairs) {
        const [k, v] = String(p).split('=');
        if (!k || v == null) continue;
        const key = k.toLowerCase();
        if (key === 'language' || key === 'lang') state.filters.language = v;
        else if (key === 'fork') state.filters.fork = (/^(1|y|yes|true)$/i).test(v);
        else if (key === 'year') state.filters.year = v;
      }
      const chips = Object.entries(state.filters).map(([k,v]) => `${k}=${v}`);
      print(`<span class="success">filters set</span> ${chips.length ? badges(chips) : ''}`);
    },

    graph(kind = 'lang') {
      if (!state.repos.length) return print(`<span class="warn">No data</span>`);
      if (String(kind).toLowerCase() === 'lang' || String(kind).toLowerCase() === 'language') {
        const counts = new Map();
        for (const r of state.repos) {
          const k = (r.language || 'misc');
          counts.set(k, (counts.get(k) || 0) + 1);
        }
        const items = [...counts.entries()].sort((a,b)=>b[1]-a[1]);
        const max = items[0]?.[1] || 0;
        print(`<span class="dim">language distribution</span>`);
        for (const [k, n] of items) {
          print(`${pad(k + ' ', 12)} ${bar(n, max, 28)} <span class="dim">${n}</span>`);
        }
      } else {
        print(`<span class="warn">Unknown graph:</span> ${esc(String(kind))}`);
      }
    },

    timeline() {
      const list = sortByRecent(state.repos).slice(0, 12);
      if (!list.length) return print(`<span class="muted">(no activity)</span>`);
      for (const r of list) {
        print(`${pad((r.name || ''), 28)} <span class="dim">${fmtDate(r.pushed_at || r.updated_at)}</span>  <span class="dim">${esc(r.language || 'misc')}</span>`);
      }
    },

    random() {
      if (!state.repos.length) return print(`<span class="warn">No repos</span>`);
      const r = state.repos[Math.floor(Math.random() * state.repos.length)];
      commands.repo(r.name || r.full_name);
    },

    about() {
      print(`<span class="bold">Austin Kimuhu Njuguna</span> — backend & data systems engineer`);
      print(`<span class="dim">I build automation, APIs, pipelines, and ML-backed services. This terminal showcases things I've built, tinkered with, and forked.</span>`);
      print(`Focus areas: <span class="badge">Python</span> <span class="badge">APIs</span> <span class="badge">SQL</span> <span class="badge">Data Engineering</span> <span class="badge">Automation</span>`);
      print(`Org: <a class="link" href="https://github.com/aueskinj" target="_blank" rel="noreferrer noopener">github.com/aueskinj</a>`);
    },

    skills() {
      const langs = [...new Set(state.repos.map(r=>r.language).filter(Boolean))].sort();
      print(`<span class="bold">Stack</span>`);
      print(badges(['Python','Flask/FastAPI','SQL','Pandas','scikit-learn','TensorFlow','Docker','GitHub Actions','AWS']));
      if (langs.length) print(`<span class="dim">Repo languages:</span> ${badges(langs)}`);
    },

    clear() { out.innerHTML = ''; },

    async explore() {
      if (!state.repos.length) return print(`<span class="warn">No repos</span>`);
      if (state.exploring) return print(`<span class="muted">(exploration already running — press Ctrl+C to stop)</span>`);
      state.exploring = true;
      let abort = false;
      state.exploreAbort = () => { abort = true; };
      print(`<span class="accent">Starting guided tour</span> — press <span class="kbd">Ctrl+C</span> to stop.`);
      const list = sortByRecent(state.repos)
        .sort((a,b)=> (b.stargazers_count||0) - (a.stargazers_count||0))
        .slice(0, 8);
      for (const r of list) {
        if (abort) break;
        await sleep(200);
        await typeLine(`$ repo ${r.name}`);
        commands.repo(r.name);
        await sleep(320);
      }
      if (abort) print(`<span class="muted">^C</span> tour aborted`);
      else print(`<span class="success">tour complete</span>`);
      state.exploring = false;
      state.exploreAbort = null;
    },
  };

  function parse(line) {
    const parts = line.trim().split(/\s+/);
    const cmd = (parts.shift() || '').toLowerCase();
    return { cmd, args: parts };
  }

  function autocomplete(current) {
    if (!current) return null;
    const token = current.trim().toLowerCase();
    const names = state.repos.map(r => (r.name || '').toLowerCase());
    const hits = names.filter(n => n.startsWith(token));
    if (hits.length === 1) return hits[0];
    if (hits.length > 1) {
      print(hits.slice(0, 12).join('  '));
    }
    return null;
  }

  // history navigation
  function handleHistoryNav(e) {
    if (!state.history.length) return;
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (state.histIndex < 0) state.histIndex = state.history.length - 1;
      else state.histIndex = Math.max(0, state.histIndex - 1);
      input.value = state.history[state.histIndex] || '';
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (state.histIndex >= 0) state.histIndex = Math.min(state.history.length, state.histIndex + 1);
      input.value = state.history[state.histIndex] || '';
      if (state.histIndex === state.history.length) { state.histIndex = -1; }
    }
  }

  // ctrl+c support
  function handleCtrlC(e) {
    if (e.ctrlKey && (e.key === 'c' || e.key === 'C')) {
      e.preventDefault();
      print('<span class="muted">^C</span>');
      if (state.exploring && state.exploreAbort) state.exploreAbort();
      input.value = '';
      return true;
    }
    return false;
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const line = input.value.trim();
    if (!line) return;
    // echo the command
    print(`<span class="prompt"><span class="user">ak</span>@<span class="host">portfolio</span>:<span class="path">~</span>$</span> ${esc(line)}`);
    state.history.push(line);
    state.histIndex = -1;
    input.value = '';

    const { cmd, args } = parse(line);
    if (!cmd) return;
    const fn = commands[cmd];
    if (typeof fn === 'function') {
      try { fn(...args); }
      catch (err) { print(`<span class="danger">Command error:</span> ${esc(String(err))}`); }
    } else {
      print(`<span class="warn">Unknown command:</span> ${esc(cmd)} — try <span class="accent">help</span>`);
    }
  });

  input.addEventListener('keydown', (e) => {
    if (handleCtrlC(e)) return;
    if (e.key === 'Tab') {
      e.preventDefault();
      const a = autocomplete(input.value);
      if (a) input.value = a;
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      handleHistoryNav(e);
    }
  });

  // Init
  (async function init() {
    await boot();
    await loadData();
    // initial suggestions
    print(`<span class="dim">try:</span> <span class="accent">ls -l</span>  •  <span class="accent">graph</span>  •  <span class="accent">timeline</span>`);
  })();
})();
