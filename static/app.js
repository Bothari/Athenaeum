'use strict';

// ── Icons (Lucide, 18×18, stroke currentColor, stroke-width 1.5) ──────────────

const ICON_AUDIOBOOK = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`;

const ICON_EBOOK = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`;

const ICON_SEARCH = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;

const ICON_DOWNLOAD = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;

const ICON_SETTINGS = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>`;

const ICON_AUTHOR = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

const ICON_SERIES = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="4" height="16" rx="1"/><rect x="8" y="6" width="4" height="14" rx="1"/><rect x="14" y="3" width="4" height="17" rx="1"/><line x1="1" y1="21" x2="22" y2="21"/></svg>`;

const ICON_LIBRARY = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`;

const ICON_REQUESTS = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;

const ICON_EDIT = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`;

const ICON_LINK = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`;

const ICON_CHECK = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;

const ICON_CROSS = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;

const ICON_ARROW_UP = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>`;

const ICON_ARROW_DOWN = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>`;

const ICON_SPINNER = `<svg class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;

const ICON_REFRESH = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-.67-6.05L23 10"/></svg>`;

const ICON_PLAY = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21"/></svg>`;

const ICON_TRASH = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>`;

const ICON_SUN = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;

const ICON_MOON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;

const ICON_DASHBOARD = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;

const ICON_HOME = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`;

const ICON_CHEVRON_DOWN = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;

const ICON_CHEVRON_UP = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>`;

const ICON_STAR = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;

const ICON_HC = () =>
  `<img src="https://wp.hardcover.app/wp-content/uploads/2023/11/Symbol-Dark.png" alt="Hardcover" width="18" class="hc-icon">`;

function typeIcon(type) {
  return type === 'audiobook' ? ICON_AUDIOBOOK : ICON_EBOOK;
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function formatAge(days) {
  if (days == null) return null;
  if (days === 0) return 'today';
  if (days < 365) return `${days}d`;
  return `${Math.floor(days / 365)}y`;
}

function formatBytes(bytes) {
  if (!bytes) return '—';
  const gb = bytes / 1e9;
  if (gb >= 1) return gb.toFixed(1) + ' GB';
  return (bytes / 1e6).toFixed(0) + ' MB';
}

function formatEta(eta) {
  let secs;
  if (typeof eta === 'string') {
    // SABnzbd returns "H:MM:SS"
    const parts = eta.split(':').map(Number);
    if (parts.length === 3 && !parts.some(isNaN)) {
      secs = parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else {
      return null;
    }
  } else {
    secs = eta;
  }
  // qBittorrent uses -1 (unavailable) and 8640000 (infinite); treat anything over 24h as unknown
  if (secs == null || secs < 0 || secs > 86400) return null;
  if (secs < 60) return `${secs}s`;
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s > 0 ? ' ' + s + 's' : ''}`.trim();
}

// Parse hash params from location.hash  e.g. #/path?foo=bar
function getHashParams() {
  const hash = location.hash.slice(1); // remove leading #
  const qIdx = hash.indexOf('?');
  if (qIdx === -1) return {};
  const params = new URLSearchParams(hash.slice(qIdx + 1));
  const result = {};
  for (const [k, v] of params) result[k] = v;
  return result;
}

function getHashPath() {
  const hash = location.hash.slice(1);
  const qIdx = hash.indexOf('?');
  return qIdx === -1 ? hash : hash.slice(0, qIdx);
}

function buildHash(path, params = {}) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') q.set(k, v);
  }
  const qs = q.toString();
  return '#' + path + (qs ? '?' + qs : '');
}

function navigate(path, params = {}) {
  location.hash = buildHash(path, params).slice(1); // hash includes #
}

// ── Auth state ─────────────────────────────────────────────────────────────────

let _authUser = null; // { user_id, username, role, force_password_change } or null when unchecked

function authUser() { return _authUser; }
function isAdmin() { return !_authUser || _authUser.role === 'admin'; }

// ── API helper ─────────────────────────────────────────────────────────────────

async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 401) {
    // Session expired mid-use — redirect to login preserving current route
    const dest = location.hash.slice(1) || '/';
    const forceLocal = sessionStorage.getItem('force_local') === '1';
    const loginParams = dest !== '/login' ? { next: dest } : {};
    if (forceLocal) loginParams.force_local = '1';
    location.hash = buildHash('/login', loginParams).slice(1);
    throw new Error('401: Not authenticated');
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status}: ${err}`);
  }
  return res.json();
}

// ── Toast ──────────────────────────────────────────────────────────────────────

function toast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

// ── Loading / Error state helpers ──────────────────────────────────────────────

function renderLoading(container) {
  container.innerHTML = `<div class="state-loading">${ICON_SPINNER}</div>`;
}

function renderError(container, retryFn) {
  container.innerHTML = `<div class="state-error">Failed to load. <a href="#" class="retry" style="color:var(--accent)">Retry</a></div>`;
  container.querySelector('.retry').onclick = (e) => { e.preventDefault(); retryFn(); };
}

// ── Shared: confirmAction ──────────────────────────────────────────────────────
// State stored on btn.dataset.confirming — not in a JS variable.

function confirmAction(btn, confirmText, action) {
  if (btn.dataset.confirming) {
    btn.dataset.confirming = '';
    btn.classList.remove('btn-warning');
    action();
  } else {
    const origText = btn.innerHTML;
    btn.dataset.confirming = '1';
    btn.classList.add('btn-warning');
    btn.textContent = confirmText;
    // Auto-reset after 4s if not clicked again
    setTimeout(() => {
      if (btn.dataset.confirming) {
        btn.dataset.confirming = '';
        btn.classList.remove('btn-warning');
        btn.innerHTML = origText;
      }
    }, 4000);
  }
}

// ── Shared: renderTable ────────────────────────────────────────────────────────
// config: { container, headers, fetchFn, renderRow, stateKey, emptyMessage? }
// headers: [{ label, key, sortable?, style? }]
// fetchFn: (params) => Promise<{ items, total }>
// Sort/filter/pagination state lives in URL hash params.

function renderTable(config) {
  const { container, headers, fetchFn, renderRow, stateKey } = config;
  const emptyMessage = config.emptyMessage || 'No items found.';
  const LIMIT = 50;

  let params = getHashParams();
  let sort = params[`${stateKey}_sort`] || (headers.find(h => h.sortable) || headers[0]).key;
  let dir = params[`${stateKey}_dir`] || 'asc';
  let q = params[`${stateKey}_q`] || '';
  let offset = 0;
  let total = 0;
  let loading = false;
  let allLoaded = false;
  let observer = null;
  let loadedCount = 0;
  let restoring = false;

  function updateUrlParams() {
    const allParams = getHashParams();
    allParams[`${stateKey}_sort`] = sort;
    allParams[`${stateKey}_dir`] = dir;
    if (q) allParams[`${stateKey}_q`] = q;
    else delete allParams[`${stateKey}_q`];
    delete allParams[`${stateKey}_offset`];
    const path = getHashPath();
    history.replaceState(null, '', buildHash(path, allParams));
  }

  function sortIcon(key) {
    if (key !== sort) return '';
    return dir === 'asc' ? ICON_ARROW_UP : ICON_ARROW_DOWN;
  }

  function renderHeaders() {
    return headers.map(h => {
      const active = h.key === sort ? ' sort-active' : '';
      const sortable = h.sortable !== false ? ' sortable' : '';
      const style = h.style ? ` style="${h.style}"` : '';
      const klass = [sortable, active, h.klass || ''].join(' ').trim();
      return `<th class="${klass}" data-key="${h.key}"${style}>${escapeHtml(h.label)} ${h.sortable !== false ? sortIcon(h.key) : ''}</th>`;
    }).join('');
  }

  async function fetchAndAppend(reset = false) {
    if (loading) return;
    loading = true;
    try {
      const extra = config.extraFetchParams ? config.extraFetchParams() : {};
      const data = await fetchFn({ q, sort, dir, limit: LIMIT, offset, ...extra });
      total = data.total;
      const tbody = container.querySelector('tbody');
      if (reset) { tbody.innerHTML = ''; loadedCount = 0; }
      if (data.items.length === 0 && reset) {
        tbody.innerHTML = `<tr><td colspan="${headers.length}" class="state-empty">${emptyMessage}</td></tr>`;
        allLoaded = true;
        return;
      }
      data.items.forEach(item => {
        const tr = document.createElement('tr');
        const html = renderRow(item, tr);
        if (typeof html === 'string') tr.innerHTML = html;
        tbody.appendChild(tr);
      });
      loadedCount += data.items.length;
      allLoaded = data.items.length < LIMIT;
      if (!allLoaded && !restoring) attachObserver();
    } finally {
      loading = false;
    }
  }

  function attachObserver() {
    if (observer) observer.disconnect();
    const tbody = container.querySelector('tbody');
    const lastRow = tbody.lastElementChild;
    if (!lastRow || allLoaded) return;
    observer = new IntersectionObserver(async (entries) => {
      if (entries[0].isIntersecting && !loading && !allLoaded) {
        observer.disconnect();
        offset += LIMIT;
        updateUrlParams();
        await fetchAndAppend(false);
      }
    }, { rootMargin: '200px' });
    observer.observe(lastRow);
  }

  // Initial render
  container.innerHTML = `
    <div class="table-toolbar">
      <input type="text" placeholder="Filter..." value="${escapeHtml(q)}" id="${stateKey}-filter-input">
      ${config.extraControls || ''}
    </div>
    <div class="table-wrap">
      <table class="table-${stateKey}">
        <thead><tr>${renderHeaders()}</tr></thead>
        <tbody></tbody>
      </table>
    </div>
  `;

  // Sort click
  container.querySelector('thead').addEventListener('click', e => {
    const th = e.target.closest('th[data-key]');
    if (!th || !th.classList.contains('sortable')) return;
    const key = th.dataset.key;
    if (key === sort) {
      dir = dir === 'asc' ? 'desc' : 'asc';
    } else {
      sort = key;
      dir = 'asc';
    }
    offset = 0;
    allLoaded = false;
    updateUrlParams();
    container.querySelector('thead tr').innerHTML = renderHeaders();
    // Reattach click on new header
    fetchAndAppend(true);
  });

  // Filter input (debounced)
  let filterTimer;
  container.querySelector(`#${stateKey}-filter-input`).addEventListener('input', e => {
    clearTimeout(filterTimer);
    filterTimer = setTimeout(() => {
      q = e.target.value;
      offset = 0;
      allLoaded = false;
      updateUrlParams();
      fetchAndAppend(true);
    }, 200);
  });

  async function initAndRestore() {
    await fetchAndAppend(true);
    if (config.restoreScroll) {
      restoring = true;
      const { scrollY, count } = config.restoreScroll;
      while (!allLoaded && loadedCount < count) {
        offset += LIMIT;
        await fetchAndAppend(false);
      }
      restoring = false;
      attachObserver();
      requestAnimationFrame(() => window.scrollTo({ top: scrollY, behavior: 'instant' }));
    }
  }
  initAndRestore();
  return {
    reload() { offset = 0; allLoaded = false; loadedCount = 0; fetchAndAppend(true); },
    getCount() { return loadedCount; },
  };
}

// ── Shared: renderTryLinkLog ───────────────────────────────────────────────────

function renderTryLinkLog(log, type, showScores = false) {
  const hcBaseUrl = { book: 'https://hardcover.app/books', author: 'https://hardcover.app/authors', series: 'https://hardcover.app/series' }[type] || 'https://hardcover.app';
  const resultColors = { match: 'var(--color-success)', linked: 'var(--color-success)', no_match: 'var(--color-error)', no_results: 'var(--color-error)', conflict: 'var(--color-warning)', error: 'var(--color-error)', no_api_key: 'var(--color-error)', not_found: 'var(--color-error)' };
  const color = resultColors[log.result] || 'var(--color-text-dim)';
  let html = '';
  if (log.result === 'no_match' || log.result === 'no_results') {
    html += `<p style="margin:0.5rem 0 0;color:var(--color-text-dim);font-size:0.875rem">No confident match found.</p>`;
  } else if (log.result === 'error') {
    html += `<p style="margin:0.5rem 0 0;color:var(--color-error);font-size:0.875rem">${escapeHtml(log.error || 'Error')}</p>`;
  } else if (log.result === 'no_api_key') {
    html += `<p style="margin:0.5rem 0 0;color:var(--color-error);font-size:0.875rem">No Hardcover API key configured.</p>`;
  } else if (log.result === 'conflict') {
    html += `<p style="margin:0.5rem 0 0;color:var(--color-warning);font-size:0.875rem">Conflict: this HC item is already linked to another entry.</p>`;
  }

  if (log.candidates && log.candidates.length) {
    const isBook = type === 'book';
    const hcLogo = ICON_HC();
    html += `<div class="table-wrap" style="margin-top:0.5rem"><table><tbody>`;
    for (const c of log.candidates) {
      const rowBg = c.is_best ? 'background:var(--color-surface-raised)' : '';
      const openUrl = c.slug ? `${hcBaseUrl}/${encodeURIComponent(c.slug)}` : '';
      const label = isBook ? escapeHtml(c.title) : escapeHtml(c.name);
      const scoreText = c.score != null ? c.score : (c.t_score != null ? `t:${c.t_score} a:${c.a_score}` : '');
      const scoreBadge = showScores && scoreText !== '' ? `<span style="font-size:0.75rem;color:var(--color-text-dim);margin-left:0.375rem">${scoreText}</span>` : '';
      const sub = isBook && c.author ? `<div style="font-size:0.8rem;color:var(--color-text-dim);margin-top:1px">${escapeHtml(c.author)}</div>` : '';
      html += `<tr style="${rowBg}">
        <td>${label}${scoreBadge}${sub}</td>
        <td style="width:1%;white-space:nowrap">
          <div style="display:flex;gap:0.5rem;align-items:center;justify-content:flex-end">
            <button class="btn btn-primary btn-sm try-link-use-btn" data-hc-id="${escapeHtml(c.hc_id)}" data-hc-slug="${escapeHtml(c.slug || '')}">Link</button>
            ${openUrl ? `<a href="${escapeHtml(openUrl)}" target="_blank" style="display:flex;align-items:center" title="Open on Hardcover">${hcLogo}</a>` : ''}
          </div>
        </td>
      </tr>`;
    }
    html += `</tbody></table></div>`;
  }

  return html;
}

// ── Shared: setupHcCard ────────────────────────────────────────────────────────

function setupHcCard(containerEl, type, entityId, initialHcId, initialSlug) {
  const hcBase = { book: 'https://hardcover.app/books', author: 'https://hardcover.app/authors', series: 'https://hardcover.app/series' }[type];
  const linkEndpoint = `/sync/link/${type}/${entityId}`;
  const tryLinkEndpoint = `/sync/try-link/${type}/${entityId}`;

  const render = (hcId, slug) => {
    const hcUrl = (hcId && slug) ? `${hcBase}/${encodeURIComponent(slug)}` : null;
    const label = slug || (hcId ? `#${hcId}` : '');

    const linkedLabel = `Linked to Hardcover ${type} #${escapeHtml(String(hcId))}`;
    const cardInner = hcId ? `
      <div style="display:flex;align-items:center;gap:0.625rem;flex-wrap:wrap">
        <span style="font-size:0.875rem">${linkedLabel}</span>
        ${hcUrl
          ? `<a href="${escapeHtml(hcUrl)}" target="_blank" style="display:flex;align-items:center" title="Open on Hardcover">${ICON_HC()}</a>`
          : `<span style="display:flex;align-items:center;opacity:0.6">${ICON_HC()}</span>`
        }
        <button class="btn btn-secondary btn-sm hc-unlink-btn" style="padding:2px 8px;font-size:0.8rem">Unlink</button>
        ${type === 'book' ? `<button class="btn btn-secondary btn-sm hc-refresh-btn" style="padding:2px 8px;font-size:0.8rem">Refresh HC data</button>` : ''}
      </div>
    ` : `
      <button class="btn btn-secondary btn-sm hc-find-btn">Find Hardcover match</button>
      <div class="hc-result"></div>
      <div style="display:flex;gap:0.5rem;align-items:center;margin-top:0.75rem">
        <input type="text" class="form-input hc-id-input" placeholder="Paste HC URL or ID" style="flex:1;min-width:0">
        <button class="btn btn-secondary btn-sm hc-set-btn">Set</button>
      </div>
    `;

    containerEl.innerHTML = `
      <div class="section-heading">Hardcover</div>
      <div class="card">${cardInner}</div>
    `;

    if (hcId) {
      containerEl.querySelector('.hc-unlink-btn').onclick = async function() {
        this.disabled = true;
        try {
          await api(linkEndpoint, { method: 'PUT', body: { hardcover_id: '', hardcover_slug: '' } });
          render(null, null);
          toast('Unlinked', 'success');
        } catch (e) {
          toast('Unlink failed: ' + e, 'error');
          this.disabled = false;
        }
      };
      const refreshBtn = containerEl.querySelector('.hc-refresh-btn');
      if (refreshBtn) {
        refreshBtn.onclick = async function() {
          this.disabled = true;
          this.textContent = 'Refreshing…';
          try {
            const result = await api(`/books/${entityId}/refresh-hc`, { method: 'POST' });
            render(result.canonical_id || hcId, result.slug || slug);
            toast('HC data refreshed', 'success');
          } catch (e) {
            toast('Refresh failed: ' + e, 'error');
            this.disabled = false;
            this.textContent = 'Refresh HC data';
          }
        };
      }
      return;
    }

    const findBtn = containerEl.querySelector('.hc-find-btn');
    const resultEl = containerEl.querySelector('.hc-result');
    const idInput = containerEl.querySelector('.hc-id-input');
    const setBtn = containerEl.querySelector('.hc-set-btn');

    findBtn.onclick = async function() {
      this.disabled = true;
      this.textContent = 'Searching...';
      try {
        const [log, settings] = await Promise.all([
          api(tryLinkEndpoint, { method: 'POST' }),
          api('/settings').catch(() => ({})),
        ]);
        const showScores = !!((settings.general || {}).debug_view);
        resultEl.innerHTML = renderTryLinkLog(log, type, showScores);
      } catch (e) {
        resultEl.innerHTML = `<p style="color:var(--color-error);font-size:0.875rem">${escapeHtml(String(e))}</p>`;
      }
      this.disabled = false;
      this.textContent = 'Find Hardcover match';
    };

    resultEl.addEventListener('click', async e => {
      const btn = e.target.closest('.try-link-use-btn');
      if (!btn) return;
      btn.disabled = true;
      try {
        const newHcId = btn.dataset.hcId;
        const newSlug = btn.dataset.hcSlug || '';
        await api(linkEndpoint, { method: 'PUT', body: { hardcover_id: newHcId, hardcover_slug: newSlug } });
        render(newHcId, newSlug);
        toast('Linked', 'success');
      } catch (e) {
        toast('Failed: ' + e, 'error');
        btn.disabled = false;
      }
    });

    idInput.addEventListener('input', async function() {
      const val = this.value.trim();
      if (!val.includes('hardcover.app/')) return;
      try {
        const resolved = await api('/sync/resolve-hc-url', { method: 'POST', body: { url: val, type } });
        if (resolved.hardcover_id) {
          this.value = resolved.hardcover_id;
          this.dataset.resolvedSlug = resolved.hardcover_slug || '';
          toast('URL resolved to HC ID ' + resolved.hardcover_id, 'success');
        } else if (resolved.error) {
          toast(resolved.error, 'error');
        }
      } catch (e) { /* ignore */ }
    });

    setBtn.onclick = async function() {
      let val = idInput.value.trim();
      if (!val) return;
      this.disabled = true;
      let resolvedSlug = idInput.dataset.resolvedSlug || '';
      if (val.includes('hardcover.app/')) {
        try {
          const r = await api('/sync/resolve-hc-url', { method: 'POST', body: { url: val, type } });
          if (r.hardcover_id) {
            val = r.hardcover_id;
            resolvedSlug = r.hardcover_slug || '';
          } else {
            toast(r.error || 'Could not resolve URL', 'error');
            this.disabled = false;
            return;
          }
        } catch (e) {
          toast('Failed to resolve URL: ' + e, 'error');
          this.disabled = false;
          return;
        }
      }
      try {
        await api(linkEndpoint, { method: 'PUT', body: { hardcover_id: val, hardcover_slug: resolvedSlug } });
        render(val, resolvedSlug);
        toast('Link updated', 'success');
      } catch (e) {
        toast('Failed: ' + e, 'error');
      }
      this.disabled = false;
    };
  };

  render(initialHcId, initialSlug);
}

// ── Shared: renderBookCard ─────────────────────────────────────────────────────

function renderBookCard(book) {
  const author = Array.isArray(book.authors)
    ? book.authors.map(a => a.name).join(', ')
    : (book.author || '');
  const coverImg = book.cover_url
    ? `<img class="book-card-cover" src="${escapeHtml(book.cover_url)}" alt="" loading="lazy">`
    : `<div class="book-card-cover-placeholder">${ICON_EBOOK}</div>`;
  const formats = Array.isArray(book.formats) ? book.formats : [];
  const requests = Array.isArray(book.requests) ? book.requests : [];
  const fmtBadges = formats.map(f =>
    `<span class="badge badge-in_library" title="${f.type}${f.narrator ? ' — ' + f.narrator : ''}">${typeIcon(f.type)}</span>`
  ).join('');
  const reqBadges = requests
    .filter(r => !formats.some(f => f.type === r.type))
    .map(r => `<span class="badge badge-${r.status}">${typeIcon(r.type)}</span>`)
    .join('');
  const badges = fmtBadges + reqBadges;

  const el = document.createElement('div');
  el.className = 'book-card';
  el.innerHTML = `
    ${coverImg}
    <div class="book-card-body">
      <div class="book-card-title">${escapeHtml(book.title)}</div>
      <div class="book-card-author">${escapeHtml(author)}</div>
      <div class="book-card-meta">${badges}</div>
    </div>
  `;
  el.onclick = () => navigate('/library/book', { book_id: book.id });
  return el;
}

// ── Shared: renderAuthorCard ───────────────────────────────────────────────────

function renderAuthorCard(author) {
  const el = document.createElement('div');
  el.className = 'entity-card';
  el.innerHTML = `
    <div class="entity-card-name">${escapeHtml(author.name)}</div>
    <div class="entity-card-meta">${author.book_count || 0} book${author.book_count !== 1 ? 's' : ''}</div>
  `;
  el.onclick = () => navigate('/library/authors/' + author.id);
  return el;
}

// ── Shared: release date helpers ──────────────────────────────────────────────

function _isUnreleased(result) {
  const rd = (result.release_date || '').slice(0, 10);
  if (!rd) return true;
  const today = new Date().toISOString().slice(0, 10);
  if (rd.endsWith('-01-01') && rd.slice(0, 4) >= String(new Date().getFullYear())) return true;
  return rd > today;
}

// ── Shared: series status badge ────────────────────────────────────────────────

function seriesStatusBadge(s) {
  const useAll = s.show_secondary_works;
  const missing  = useAll ? s.missing_all  : s.missing_primary;
  const upcoming = useAll ? s.upcoming_all : s.upcoming_primary;
  if (missing == null && upcoming == null) return '';
  if (missing > 0)  return `<span class="badge badge-missing" style="font-size:0.75rem">${missing} missing</span>`;
  if (upcoming > 0) return `<span class="badge badge-upcoming" style="font-size:0.75rem">${upcoming} upcoming</span>`;
  return `<span class="badge badge-completed" style="font-size:0.75rem">Complete</span>`;
}

// ── Shared: renderSeriesCard ───────────────────────────────────────────────────

function renderSeriesCard(series) {
  const el = document.createElement('div');
  el.className = 'entity-card';
  const badge = seriesStatusBadge(series);
  el.innerHTML = `
    <div class="entity-card-name">${escapeHtml(series.name)}</div>
    <div class="entity-card-meta" style="display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap">
      <span class="badge badge-in_library">${series.library_count || 0}</span>${series.requested_count > 0 ? `<span class="badge badge-requested">+${series.requested_count}</span>` : ''}
      ${badge}
    </div>
  `;
  el.onclick = () => navigate('/library/series/' + series.id);
  return el;
}

// ── Shared: renderDetailStats ──────────────────────────────────────────────────
// stats: { inLibrary, requested, missing, upcoming, total }
// missing/upcoming/total may be null while loading.

function renderDetailStats(name, stats) {
  const loading = stats.missing == null;
  const total = stats.total != null ? stats.total : null;
  const pct = (total && stats.inLibrary != null) ? Math.round((stats.inLibrary / total) * 100) : null;

  const barHtml = total != null ? `
    <div class="series-progress-bar" title="${stats.inLibrary} of ${total} in library">
      <div class="series-progress-fill" style="width:${pct}%"></div>
    </div>` : `<div class="series-progress-bar series-progress-loading"></div>`;

  const summaryParts = [`<span>${stats.inLibrary || 0} in library</span>`];
  if (stats.requested) summaryParts.push(`<span>${stats.requested} requested</span>`);
  if (loading) {
    summaryParts.push(`<span class="td-dim" id="series-stat-missing">checking…</span>`);
  } else {
    if (stats.missing)  summaryParts.push(`<a class="series-stat-missing" href="#series-section-missing" onclick="document.getElementById('series-section-missing')?.scrollIntoView({behavior:'smooth',block:'start'});return false;">${stats.missing} missing</a>`);
    if (stats.upcoming) summaryParts.push(`<a class="series-stat-upcoming" href="#series-section-upcoming" onclick="document.getElementById('series-section-upcoming')?.scrollIntoView({behavior:'smooth',block:'start'});return false;">${stats.upcoming} upcoming</a>`);
    if (!stats.missing && !stats.upcoming) summaryParts.push(`<span class="series-stat-complete">complete</span>`);
  }

  return `
    <div class="series-stats-block mb-2" id="series-stats-block">
      ${barHtml}
      <div class="series-stats-summary">${summaryParts.join('<span class="series-stat-sep">·</span>')}</div>
    </div>
  `;
}

// ── Shared: buildFormatRows ────────────────────────────────────────────────────
// Renders always-visible format status rows at the bottom of a search card.
// Each row shows a status dot (gray=unmonitored, blue=requested, green=in-library),
// type label, optional narrator input (audiobook unmonitored), and narrator name.
// Clicking the dot toggles between unmonitored and requested.

function buildFormatRows(card, result, onRequestSuccess) {
  const container = card.querySelector('.search-card-fmt-rows');

  const state = {};
  for (const type of ['audiobook', 'ebook']) {
    const lib = (result.library_formats || []).find(f => f.type === type);
    const req = (result.existing_requests || []).find(r => r.type === type && r.status !== 'failed');
    state[type] = {
      mode: lib ? 'in-library' : req ? 'requested' : 'unmonitored',
      reqStatus: req ? (req.status || 'requested') : null,
      narrator: req ? (req.narrator || '') : '',
      reqId: req ? (req.id || null) : null,
      reqOwnerId: req ? (req.requested_by_user_id || null) : null,
      libNarrator: lib ? (lib.narrator || '') : '',
    };
  }

  function render() {
    const ab = state['audiobook'];
    const eb = state['ebook'];

    function pill(type) {
      const s = state[type];
      const typeName = type === 'audiobook' ? 'Audiobook' : 'Ebook';
      const canCancel = s.mode !== 'requested' || isAdmin() || !_authUser || !s.reqOwnerId || s.reqOwnerId === _authUser.user_id;
      const tips = { 'in-library': `${typeName} — in library`, 'requested': canCancel ? `${typeName} — click to cancel` : `${typeName} — requested by another user`, 'unmonitored': `${typeName} — click to request` };
      const badgeClass = s.mode === 'in-library' ? 'badge-in_library' : s.mode === 'requested' ? (s.reqStatus === 'pending' ? 'badge-pending' : s.reqStatus === 'completed' ? 'badge-completed' : 'badge-requested') : 'badge-neutral';
      const isDisabled = s.mode === 'in-library' || (s.mode === 'requested' && !canCancel);
      return `<button class="badge ${badgeClass} fmt-pill" data-type="${type}" title="${tips[s.mode]}"${isDisabled ? ' disabled' : ''}>${typeIcon(type)}</button>`;
    }

    // Narrator: show input if audiobook is unmonitored, text if requested/in-library
    let narratorHtml = '';
    if (ab.mode === 'unmonitored') {
      narratorHtml = `<input class="fmt-narrator-input" data-type="audiobook" type="text" placeholder="Narrator" value="${escapeHtml(ab.narrator)}">`;
    } else if (ab.mode === 'requested' && ab.narrator) {
      narratorHtml = `<span class="fmt-narrator-text">${escapeHtml(ab.narrator)}</span>`;
    } else if (ab.mode === 'in-library' && ab.libNarrator) {
      narratorHtml = `<span class="fmt-narrator-text">${escapeHtml(ab.libNarrator)}</span>`;
    }

    container.innerHTML = `<div class="fmt-row">
      <span class="fmt-label">Request</span>
      ${pill('ebook')}
      <span class="fmt-sep">|</span>
      ${pill('audiobook')}
      ${narratorHtml}
    </div>`;

    const inp = container.querySelector('.fmt-narrator-input');
    if (inp) {
      inp.addEventListener('input', e => { state['audiobook'].narrator = e.target.value; });
      inp.addEventListener('click', e => e.stopPropagation());
    }

    container.querySelectorAll('.fmt-pill:not(:disabled)').forEach(btn => {
      btn.addEventListener('click', e => { e.stopPropagation(); handleDot(btn.dataset.type); });
    });
  }

  async function handleDot(type) {
    const s = state[type];
    const dot = container.querySelector(`.fmt-pill[data-type="${type}"]`);
    dot.disabled = true;

    if (s.mode === 'unmonitored') {
      try {
        const narratorVal = type === 'audiobook' ? (s.narrator.trim() || null) : null;
        let bookId = result.book_id;

        // Always POST /books to ensure series association is created even for existing books
        const book = await api('/books', { method: 'POST', body: {
          title: result.title,
          authors: (result.authors || []).map(a => ({ name: a.name, hc_id: a.id || null })),
          cover_url: result.cover_url || null,
          series_list: (result.series || []).map(s => ({
            name: s.name,
            position: s.position || null,
            hardcover_id: s.hardcover_series_id || null,
          })),
          metadata_source: result.metadata_source || null,
          metadata_id: result.metadata_id || null,
          metadata_url: result.metadata_url || null,
          hardcover_slug: result.slug || null,
        }});
        result.book_id = book.id;
        bookId = book.id;
        const bookUrl = buildHash('/library/book', { book_id: bookId });
        card.querySelectorAll('.search-card-cover-link, .search-card-title-link').forEach(a => { a.href = bookUrl; });

        const req = await api('/requests', { method: 'POST', body: { book_id: bookId, type, narrator: narratorVal } });
        if (req.skipped) toast('Already requested', 'info');
        s.reqId = req.id || null;
        s.reqStatus = req.status || 'requested';
        s.mode = 'requested';
        render();
        if (onRequestSuccess) onRequestSuccess({ id: bookId }, result, [type]);
      } catch (err) {
        toast('Request failed: ' + err.message, 'error');
        dot.disabled = false;
      }

    } else if (s.mode === 'requested') {
      if (!s.reqId) { toast('Cannot cancel — unknown request ID', 'warning'); dot.disabled = false; return; }
      if (!isAdmin() && _authUser && s.reqOwnerId && s.reqOwnerId !== _authUser.user_id) { toast('Cannot cancel another user\'s request', 'warning'); dot.disabled = false; return; }
      try {
        await api(`/requests/${s.reqId}`, { method: 'DELETE' });
        s.mode = 'unmonitored';
        s.reqId = null;
        s.narrator = '';
        render();
        if (state.audiobook.mode === 'unmonitored' && state.ebook.mode === 'unmonitored') {
          card.querySelectorAll('.search-card-cover-link, .search-card-title-link').forEach(a => a.removeAttribute('href'));
        }
      } catch (err) {
        toast('Cancel failed: ' + err.message, 'error');
        dot.disabled = false;
      }
    }
  }

  render();
}

// ── Shared: populateBookCard ───────────────────────────────────────────────────
// Fills `el` with the standard book card layout (cover + body + format rows).
// `el` should already have the appropriate class (search-card or book-detail-header).
// result shape: { title, author, authors, series, rating, rating_count,
//                 hardcover_url, cover_url, book_id, library_formats, existing_requests }

function populateBookCard(el, result, onRequestSuccess, { showFmtRows = true } = {}) {
  const pos = result.series && result.series[0] && result.series[0].position;
  const posFmt = pos ? (() => { const n = parseFloat(pos); return isNaN(n) ? pos : (n % 1 === 0 ? String(Math.floor(n)) : String(n)); })() : '';
  const seriesStr = (result.series && result.series[0])
    ? `${escapeHtml(result.series[0].name)}${posFmt ? ' #' + posFmt : ''}`
    : '';

  const ratingStr = result.rating
    ? `${ICON_STAR} ${result.rating.toFixed(1)} <span style="opacity:0.6">(${result.rating_count || 0})</span>`
    : '';

  const today = new Date().toISOString().slice(0, 10);
  const rd = result.release_date || '';
  const rdYearOnly = rd && rd.endsWith('-01-01') && rd.substring(0, 4) >= String(new Date().getFullYear());
  const releaseBadge = (rd && (rd >= today || rdYearOnly))
    ? `<span class="badge badge-neutral" title="${rdYearOnly && rd < today ? 'Expected ' + rd.substring(0, 4) : 'Releases ' + rd}">Unreleased</span>`
    : (!rd && result.release_date_fetched)
      ? `<span class="badge badge-neutral" title="No release date known">No date</span>`
      : (!rd && result.published_year && String(result.published_year) > String(new Date().getFullYear()))
        ? `<span class="badge badge-neutral" title="Expected ${result.published_year}">Unreleased</span>`
        : '';

  const hcLink = result.hardcover_url
    ? `<a href="${escapeHtml(result.hardcover_url)}" target="_blank" class="search-card-hc-link" title="Open on Hardcover">${ICON_HC()}</a>`
    : '';

  const authorEntries = (result.authors && result.authors.length > 0
    ? result.authors
    : (result.author ? [{ name: result.author, id: result.author_id || '' }] : [])
  ).filter(a => a.name);
  const authorHtml = authorEntries.map(a =>
    a.id
      ? `<a href="${buildHash('/', { hc_author_id: a.id, advanced: '1' })}" class="search-card-link">${escapeHtml(a.name)}</a>`
      : `<span class="search-card-link">${escapeHtml(a.name)}</span>`
  ).join(', ');

  const seriesItem = result.series && result.series[0];
  const seriesHtml = seriesItem
    ? seriesItem.hardcover_series_id
      ? `<a href="${buildHash('/', { hc_series_id: seriesItem.hardcover_series_id, advanced: '1' })}" class="search-card-link">${escapeHtml(seriesItem.name)}${posFmt ? ' #' + posFmt : ''}</a>`
      : `<a href="${buildHash('/', { series: seriesItem.name, advanced: '1' })}" class="search-card-link">${escapeHtml(seriesItem.name)}${posFmt ? ' #' + posFmt : ''}</a>`
    : '';

  const hasActiveLink = result.book_id && (
    (result.library_formats && result.library_formats.length > 0) ||
    (result.existing_requests && result.existing_requests.some(r => r.status !== 'failed'))
  );
  const bookHash = hasActiveLink ? buildHash('/library/book', { book_id: result.book_id }) : '';

  el.innerHTML = `
    <a class="search-card-cover-link"${bookHash ? ` href="${bookHash}"` : ''}>
      ${result.cover_url
        ? `<img class="search-card-cover" src="${escapeHtml(result.cover_url)}" alt="" loading="lazy">`
        : `<div class="search-card-cover-placeholder">${ICON_EBOOK}</div>`
      }
    </a>
    <div class="search-card-body">
      <div class="search-card-title-row">
        <a class="search-card-title search-card-title-link"${bookHash ? ` href="${bookHash}"` : ''}>${escapeHtml(result.title)}</a>
        ${hcLink}
      </div>
      <div class="search-card-author">${authorHtml}</div>
      ${seriesHtml ? `<div class="search-card-series">${seriesHtml}</div>` : ''}
      <div class="search-card-meta">
        ${ratingStr ? `<span class="search-card-rating">${ratingStr}</span>` : ''}
        ${releaseBadge}
      </div>
    </div>
    ${showFmtRows ? '<div class="search-card-fmt-rows"></div>' : ''}
  `;

  if (showFmtRows) buildFormatRows(el, result, onRequestSuccess);
}

// ── Shared: renderSearchResults ────────────────────────────────────────────────

function renderSearchResults(container, results, onRequestSuccess = null) {
  if (!results || results.length === 0) {
    container.innerHTML = `<div class="state-empty">No results found.</div>`;
    return;
  }

  container.innerHTML = `<div class="search-results-header">${results.length} result${results.length !== 1 ? 's' : ''}</div>`;

  results.forEach(result => {
    const card = document.createElement('div');
    card.className = 'search-card';
    populateBookCard(card, result, onRequestSuccess);
    container.appendChild(card);
  });
}

// ── Tab scroll hints ──────────────────────────────────────────────────────────

function setupTabScrollHints(wrap) {
  const tabs = wrap.querySelector('.tabs');
  if (!tabs) return;
  function update() {
    wrap.classList.toggle('tabs-fade-left',  tabs.scrollLeft > 0);
    wrap.classList.toggle('tabs-fade-right', tabs.scrollLeft + tabs.clientWidth < tabs.scrollWidth - 1);
  }
  tabs.addEventListener('scroll', update, { passive: true });
  update();
}

// ── First-run banner ───────────────────────────────────────────────────────────

async function checkAbsBanner() {
  try {
    const settings = await api('/settings');
    const banner = document.getElementById('banner');
    if (!settings.audiobookshelf || !settings.audiobookshelf.url) {
      banner.innerHTML = `⚠ AudiobookShelf is not configured. <a href="#/settings">Go to Settings</a> to get started.`;
      banner.classList.remove('hidden');
    } else {
      banner.classList.add('hidden');
    }
  } catch { /* ignore */ }
}

// ── Router ────────────────────────────────────────────────────────────────────

const _routes = [];

function route(pattern, handler) {
  // Convert pattern like /library/series/:id to regex
  const keys = [];
  const regexStr = pattern
    .replace(/[.*+?^${}()|[\]\\]/g, c => c === ':' ? c : `\\${c}`)
    .replace(/:([a-zA-Z_][a-zA-Z0-9_]*)/g, (_, key) => { keys.push(key); return '([^/]+)'; });
  _routes.push({ regex: new RegExp('^' + regexStr + '$'), keys, handler });
}

function matchRoute(path) {
  for (const r of _routes) {
    const m = path.match(r.regex);
    if (m) {
      const params = {};
      r.keys.forEach((k, i) => { params[k] = decodeURIComponent(m[i + 1]); });
      return { handler: r.handler, params };
    }
  }
  return null;
}

const app = document.getElementById('app');
let _prevPath = null;

async function render() {
  // Remove home-page class before every render; home route re-adds it
  document.body.classList.remove('home-page');
  const path = getHashPath() || '/';

  // Clear saved series scroll when navigating to the list fresh (not back from a detail page)
  if (path === '/library/series' && !(_prevPath || '').startsWith('/library/series/')) {
    sessionStorage.removeItem('series_list_scroll');
  }
  _prevPath = path;
  const match = matchRoute(path);
  if (!match) {
    app.innerHTML = `<div class="state-empty" style="margin-top:4rem">Page not found.</div>`;
    return;
  }
  try {
    await match.handler(match.params, getHashParams());
  } catch (err) {
    console.error('Route error:', err);
    app.innerHTML = `<div class="state-empty" style="margin-top:4rem">Page not found.</div>`;
  }
}

// Highlight active nav link (top + bottom)
function updateNavForRole() {
  const admin = isAdmin();
  const authed = !!_authUser;
  // Top nav
  document.querySelectorAll('a.nav-btn[href="#/dashboard"], a.nav-btn[href="#/settings"]').forEach(el => {
    el.style.display = admin ? '' : 'none';
  });
  const profileLink = document.getElementById('nav-profile');
  if (profileLink) profileLink.style.display = (!admin && authed) ? '' : 'none';
  // Rename Queue -> Requests for non-admins
  const queueLink = document.querySelector('a.nav-btn[href="#/requests"]');
  if (queueLink) queueLink.textContent = admin ? 'Queue' : 'Requests';
  // Bottom nav
  ['nb-dashboard', 'nb-settings'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = admin ? '' : 'none';
  });
  const nbProfile = document.getElementById('nb-profile');
  if (nbProfile) nbProfile.style.display = (!admin && authed) ? '' : 'none';
}

function updateActiveNav() {
  const path = getHashPath() || '/';

  // Top nav
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn[href]').forEach(el => {
    const href = el.getAttribute('href').replace('#', '');
    if (href === '/' ? path === '/' : path.startsWith(href)) {
      el.classList.add('active');
    }
  });
  if (path.startsWith('/library')) {
    document.getElementById('library-menu-btn')?.classList.add('active');
  }

  // Bottom nav
  document.querySelectorAll('.nav-bottom-btn').forEach(el => el.classList.remove('active'));
  const nbMap = {
    'nb-search':   () => path === '/',
    'nb-library':  () => path.startsWith('/library'),
    'nb-queue':    () => path.startsWith('/requests') || path.startsWith('/downloads'),
    'nb-dashboard':() => path === '/dashboard',
    'nb-settings': () => path === '/settings',
    'nb-profile':  () => path === '/profile',
  };
  for (const [id, test] of Object.entries(nbMap)) {
    if (test()) document.getElementById(id)?.classList.add('active');
  }
}

// ── Routes ────────────────────────────────────────────────────────────────────

// Login
route('/login', async (params, qp) => {
  const forceLocal = 'force_local' in qp || sessionStorage.getItem('force_local') === '1';
  if ('force_local' in qp) sessionStorage.setItem('force_local', '1');
  const next = qp.next || '/';

  // Check if OIDC is active and we should redirect
  if (!forceLocal) {
    try {
      const meData = await fetch('/api/auth/me');
      if (meData.status === 401) {
        const body = await meData.json().catch(() => ({}));
        const modes = (body.detail || {}).modes || [];
        if (modes.includes('oidc') && !modes.includes('form')) {
          // OIDC only — redirect immediately
          window.location.href = '/api/auth/oidc/start';
          return;
        }
        if (modes.includes('oidc') && !forceLocal) {
          // OIDC + form available — redirect to OIDC by default
          window.location.href = '/api/auth/oidc/start';
          return;
        }
      } else if (meData.ok) {
        // Already logged in
        navigate(next);
        return;
      }
    } catch {}
  }

  app.innerHTML = `<div class="narrow-page" style="max-width:400px;margin-top:4rem">
    <div class="page-header"><span class="page-title">Sign in</span></div>
    <div class="card">
      <div class="form-group">
        <label class="form-label">Username</label>
        <input class="form-input" id="login-username" type="text" autocomplete="username">
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input class="form-input" id="login-password" type="password" autocomplete="current-password">
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" id="login-btn">Sign in</button>
        <span class="form-feedback" id="login-feedback"></span>
      </div>
    </div>
    ${!forceLocal ? `<div style="margin-top:1rem;text-align:center"><a href="/api/auth/oidc/start" style="font-size:0.85rem">Sign in with SSO</a></div>` : ''}
  </div>`;

  const doLogin = async () => {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const fb = document.getElementById('login-feedback');
    const btn = document.getElementById('login-btn');
    if (!username || !password) { fb.textContent = 'Enter username and password.'; return; }
    btn.disabled = true;
    try {
      const data = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!data.ok) { fb.textContent = 'Invalid credentials.'; btn.disabled = false; return; }
      const result = await data.json();
      _authUser = result;
      sessionStorage.removeItem('force_local');
      updateNavForRole();
      if (result.force_password_change) { navigate('/change-password'); return; }
      navigate(next);
    } catch { fb.textContent = 'Login failed.'; btn.disabled = false; }
  };

  document.getElementById('login-btn').addEventListener('click', doLogin);
  document.getElementById('login-password').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
  document.getElementById('login-username').focus();
});

// Change password (forced after admin reset)
route('/change-password', async () => {
  app.innerHTML = `<div class="narrow-page" style="max-width:400px;margin-top:4rem">
    <div class="page-header"><span class="page-title">Set new password</span></div>
    <div class="card">
      <p class="text-dim" style="margin-bottom:1rem">Your password must be changed before continuing.</p>
      <div class="form-group">
        <label class="form-label">Current password</label>
        <input class="form-input" id="cp-current" type="password">
      </div>
      <div class="form-group">
        <label class="form-label">New password</label>
        <input class="form-input" id="cp-new" type="password">
      </div>
      <div class="form-group">
        <label class="form-label">Confirm new password</label>
        <input class="form-input" id="cp-confirm" type="password">
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" id="cp-btn">Save password</button>
        <span class="form-feedback" id="cp-feedback"></span>
      </div>
    </div>
  </div>`;

  document.getElementById('cp-btn').addEventListener('click', async () => {
    const current = document.getElementById('cp-current').value;
    const nw = document.getElementById('cp-new').value;
    const confirm = document.getElementById('cp-confirm').value;
    const fb = document.getElementById('cp-feedback');
    const btn = document.getElementById('cp-btn');
    if (!current || !nw) { fb.textContent = 'All fields required.'; return; }
    if (nw !== confirm) { fb.textContent = 'Passwords do not match.'; return; }
    btn.disabled = true;
    try {
      await api('/auth/change-password', { method: 'POST', body: { current_password: current, new_password: nw } });
      if (_authUser) _authUser.force_password_change = false;
      toast('Password updated.');
      navigate('/');
    } catch { fb.textContent = 'Failed to change password.'; btn.disabled = false; }
  });
});

// Home / Search
route('/', async (params, qp) => {
  const q = qp.q || '';
  const author = qp.author || '';
  const series = qp.series || '';
  const hcAuthorId = qp.hc_author_id || '';
  const hcSeriesId = qp.hc_series_id || '';
  const advanced = qp.advanced === '1';
  const hasValue = !!(q || author || series || hcAuthorId || hcSeriesId);

  if (!hasValue) document.body.classList.add('home-page');

  app.innerHTML = `<div class="narrow-page">
    <div class="search-page ${hasValue ? '' : 'empty'}" id="search-page">
      <div class="home-title">Athenaeum</div>
      <div class="search-container" id="search-container">
        <div class="search-input-row">
          <input
            type="text"
            class="search-input-main"
            id="search-q"
            placeholder="Search for a book…"
            value="${escapeHtml(q)}"
            autocomplete="off"
          >
          <div class="search-input-icons">
            <button class="search-clear-btn${hasValue ? '' : ' hidden'}" id="search-clear" title="Clear" style="${hasValue ? '' : 'display:none'}">
              ${ICON_CROSS}
            </button>
            <button class="search-advanced-btn${advanced ? ' active' : ''}" id="search-adv-btn" title="Advanced search">
              ${ICON_SETTINGS}
            </button>
          </div>
        </div>
        <div class="search-advanced-fields${advanced ? ' open' : ''}" id="search-adv-fields">
          <div class="search-advanced-inner">
            <input type="text" id="search-author" placeholder="Author…" value="${escapeHtml(author)}">
            <input type="text" id="search-series" placeholder="Series…" value="${escapeHtml(series)}">
          </div>
        </div>
      </div>
      <div class="search-results" id="search-results"></div>
    </div>
  </div>`;

  const qInput = document.getElementById('search-q');
  const advBtn = document.getElementById('search-adv-btn');
  const advFields = document.getElementById('search-adv-fields');
  const clearBtn = document.getElementById('search-clear');
  const resultsDiv = document.getElementById('search-results');
  const searchPage = document.getElementById('search-page');

  function updateClearBtn() {
    const authorVal = document.getElementById('search-author')?.value || '';
    const seriesVal = document.getElementById('search-series')?.value || '';
    const anyVal = !!(qInput.value || authorVal || seriesVal);
    if (clearBtn) clearBtn.style.display = anyVal ? '' : 'none';
  }

  async function runSearch() {
    const currentQp = getHashParams();
    const hcAuthorIdVal = currentQp.hc_author_id || '';
    const hcSeriesIdVal = currentQp.hc_series_id || '';
    const qVal = qInput.value.trim();
    const authorVal = document.getElementById('search-author')?.value.trim() || '';
    const seriesVal = document.getElementById('search-series')?.value.trim() || '';
    const isAdv = advFields.classList.contains('open');

    if (!qVal && !authorVal && !seriesVal && !hcAuthorIdVal && !hcSeriesIdVal) return;

    // Update URL
    const newParams = {};
    if (hcAuthorIdVal && !qVal && !authorVal && !seriesVal) {
      newParams.hc_author_id = hcAuthorIdVal;
      newParams.advanced = '1';
    } else if (hcSeriesIdVal && !qVal && !authorVal && !seriesVal) {
      newParams.hc_series_id = hcSeriesIdVal;
      newParams.advanced = '1';
    } else {
      if (qVal) newParams.q = qVal;
      if (authorVal) newParams.author = authorVal;
      if (seriesVal) newParams.series = seriesVal;
      if (isAdv) newParams.advanced = '1';
    }
    history.replaceState(null, '', buildHash('/', newParams));

    // Move input to top, switch to normal nav layout
    searchPage.classList.remove('empty');
    document.body.classList.remove('home-page');

    renderLoading(resultsDiv);

    try {
      let data;
      if (hcAuthorIdVal && !qVal && !authorVal && !seriesVal) {
        data = await api('/search/advanced?author_id=' + encodeURIComponent(hcAuthorIdVal));
      } else if (hcSeriesIdVal && !qVal && !authorVal && !seriesVal) {
        data = await api('/search/advanced?hc_series_id=' + encodeURIComponent(hcSeriesIdVal));
      } else if (isAdv || authorVal || seriesVal) {
        const qStr = new URLSearchParams();
        if (qVal) qStr.set('title', qVal);
        if (authorVal) qStr.set('author', authorVal);
        if (seriesVal) qStr.set('series', seriesVal);
        data = await api('/search/advanced?' + qStr.toString());
      } else {
        data = await api('/search/metadata?q=' + encodeURIComponent(qVal));
      }
      renderSearchResults(resultsDiv, data.results);
    } catch (err) {
      renderError(resultsDiv, runSearch);
    }
  }

  // Advanced toggle
  advBtn.onclick = () => {
    const isOpen = advFields.classList.toggle('open');
    advBtn.classList.toggle('active', isOpen);
    // Update URL
    const params = getHashParams();
    if (isOpen) params.advanced = '1';
    else delete params.advanced;
    history.replaceState(null, '', buildHash('/', params));
  };

  // Clear button
  if (clearBtn) {
    clearBtn.onclick = () => {
      qInput.value = '';
      const authorEl = document.getElementById('search-author');
      const seriesEl = document.getElementById('search-series');
      if (authorEl) authorEl.value = '';
      if (seriesEl) seriesEl.value = '';
      resultsDiv.innerHTML = '';
      searchPage.classList.add('empty');
      history.replaceState(null, '', '#/');
      updateClearBtn();
    };
  }

  // Input event
  qInput.addEventListener('input', updateClearBtn);
  document.getElementById('search-author')?.addEventListener('input', updateClearBtn);
  document.getElementById('search-series')?.addEventListener('input', updateClearBtn);

  // Submit on Enter
  function onKeydown(e) {
    if (e.key === 'Enter') runSearch();
  }
  qInput.addEventListener('keydown', onKeydown);
  document.getElementById('search-author')?.addEventListener('keydown', onKeydown);
  document.getElementById('search-series')?.addEventListener('keydown', onKeydown);

  // Auto-run if query in URL
  if (hasValue) {
    await runSearch();
  } else {
    qInput.focus();
  }
});

// Library: Books list
route('/library/books', async (params, qp) => {
  renderLoading(app);
  try {
    app.innerHTML = `<div class="narrow-page">
      <div class="page-header"><span class="page-title">${ICON_LIBRARY} Books</span></div>
      <div id="books-content"></div>
    </div>`;

    const content = document.getElementById('books-content');

    let booksUnlinked = qp.unlinked === '1';
    const booksTable = renderTable({
      container: content,
      stateKey: 'books',
      headers: [
        { label: 'Title', key: 'title', sortable: true },
        { label: 'Author', key: 'author', sortable: true },
        { label: 'Formats', key: 'formats', sortable: false, style: 'width:90px' },
      ],
      fetchFn: (p) => api('/books?' + new URLSearchParams(p).toString()),
      extraFetchParams: () => booksUnlinked ? { unlinked: '1' } : {},
      extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="books-unlinked-cb"${booksUnlinked ? ' checked' : ''}> Unlinked only</label>`,
      renderRow: (b) => {
        const author = Array.isArray(b.authors) ? b.authors.map(a => a.name).join(', ') : '—';
        const formats = b.formats || [];
        const requests = b.requests || [];
        const formatBadges = formats.map(f =>
          `<span class="badge badge-in_library" title="${f.type}${f.narrator ? ' — ' + f.narrator : ''}">${typeIcon(f.type)}</span>`
        ).join(' ');
        const pendingBadges = requests.map(r =>
          `<span class="badge badge-${r.status}" title="${r.type} — ${r.status}">${typeIcon(r.type)}</span>`
        ).join(' ');
        return `
          <td><a href="${buildHash('/library/book', { book_id: b.id })}">${escapeHtml(b.title)}</a></td>
          <td class="td-dim">${escapeHtml(author)}</td>
          <td style="white-space:nowrap">${formatBadges}${pendingBadges}</td>
        `;
      },
      emptyMessage: `Your library is empty. <a href="#/">Search for a book</a>`,
    });
    content.querySelector('#books-unlinked-cb').addEventListener('change', e => {
      booksUnlinked = e.target.checked;
      booksTable.reload();
    });
  } catch (err) {
    renderError(app, render);
  }
});

// Library: Authors list
route('/library/authors', async (params, qp) => {
  app.innerHTML = `<div class="narrow-page">
    <div class="page-header"><span class="page-title">${ICON_AUTHOR} Authors</span></div>
    <div id="authors-content"></div>
  </div>`;
  const content = document.getElementById('authors-content');
  let authorsUnlinked = qp.unlinked === '1';
  const authorsTable = renderTable({
    container: content,
    stateKey: 'authors',
    headers: [
      { label: 'Name', key: 'name', sortable: true },
      { label: 'Books', key: 'book_count', sortable: true, style: 'width:80px' },
    ],
    fetchFn: (p) => api('/authors?' + new URLSearchParams(p).toString()),
    extraFetchParams: () => authorsUnlinked ? { unlinked: '1' } : {},
    extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="authors-unlinked-cb"${authorsUnlinked ? ' checked' : ''}> Unlinked only</label>`,
    renderRow: (a) => `
      <td><a href="#/library/authors/${a.id}">${escapeHtml(a.name)}</a></td>
      <td class="td-dim">${a.book_count || 0}</td>
    `,
    emptyMessage: 'No authors yet. Authors are added automatically when books are synced.',
  });
  content.querySelector('#authors-unlinked-cb').addEventListener('change', e => {
    authorsUnlinked = e.target.checked;
    authorsTable.reload();
  });
});

// Library: Author detail
route('/library/authors/:id', async ({ id }) => {
  const ICON_LIST_V = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;
  const ICON_GRID_V = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`;
  renderLoading(app);
  try {
    const books = await api(`/authors/${id}/books`);
    let authorName = 'Author';
    for (const book of books) {
      const match = (book.authors || []).find(a => a.id === id);
      if (match) { authorName = match.name; break; }
    }

    function renderAuthorBooksView() {
      const view = localStorage.getItem('detail_view') || 'list';
      app.innerHTML = `<div class="narrow-page">
        <div class="page-header">
          <span class="page-title">${ICON_AUTHOR} ${escapeHtml(authorName)}</span>
          <div class="view-toggle">
            <button class="view-toggle-btn${view === 'poster' ? ' active' : ''}" id="vt-poster" title="Poster">${ICON_GRID_V}</button>
            <button class="view-toggle-btn${view === 'list' ? ' active' : ''}" id="vt-list" title="List">${ICON_LIST_V}</button>
          </div>
        </div>
        <div id="author-books"></div>
        <div id="author-also-by-section"></div>
        <div id="author-hc-section" class="mt-2"></div>
        <div id="author-debug-section"></div>
      </div>`;
      document.getElementById('vt-poster').onclick = () => { localStorage.setItem('detail_view', 'poster'); renderAuthorBooksView(); loadAlsoBy(); };
      document.getElementById('vt-list').onclick   = () => { localStorage.setItem('detail_view', 'list');   renderAuthorBooksView(); loadAlsoBy(); };

      // HC match section
      const authorEntry = books.flatMap(b => b.authors || []).find(a => a.id === id) || {};
      const hcAuthorId = authorEntry.hardcover_author_id;
      const hcAuthorSlug = authorEntry.hardcover_author_slug;
      const authorHcSection = document.getElementById('author-hc-section');
      if (authorHcSection) {
        setupHcCard(authorHcSection, 'author', id, hcAuthorId, hcAuthorSlug);
      }

      // Debug card — pull link IDs from the books we already have
      api('/settings').then(s => {
        if (!(s.general || {}).debug_view) return;
        const authorEntry = books.flatMap(b => b.authors || []).find(a => a.id === id) || {};
        const rows = [
          ['abs_author_id', authorEntry.abs_author_id],
          ['hardcover_author_id', authorEntry.hardcover_author_id],
        ].map(([k, v]) =>
          `<tr><td class="td-dim" style="white-space:nowrap;padding-right:1rem">${escapeHtml(k)}</td><td class="td-mono">${escapeHtml(String(v ?? '—'))}</td></tr>`
        ).join('');
        const dbg = document.getElementById('author-debug-section');
        if (dbg) dbg.innerHTML = `
          <div class="section-heading mt-2">Debug: Links</div>
          <div class="card" style="overflow-x:auto">
            <table class="data-table"><tbody>${rows}</tbody></table>
          </div>
        `;
      }).catch(() => {});

      const container = document.getElementById('author-books');
      if (!books.length) {
        container.innerHTML = `<div class="state-empty">No books found.</div>`;
      } else if (view === 'list') {
        let sortKey = 'title', sortDir = 'asc';
        function renderAuthorTable() {
          const sorted = [...books].sort((a, b) => {
            const av = sortKey === 'title'
              ? (a.title || '').toLowerCase()
              : (a.series || []).map(s => s.name).join('').toLowerCase();
            const bv = sortKey === 'title'
              ? (b.title || '').toLowerCase()
              : (b.series || []).map(s => s.name).join('').toLowerCase();
            return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
          });
          const titleIcon = sortKey === 'title' ? (sortDir === 'asc' ? ICON_ARROW_UP : ICON_ARROW_DOWN) : '';
          const seriesIcon = sortKey === 'series' ? (sortDir === 'asc' ? ICON_ARROW_UP : ICON_ARROW_DOWN) : '';
          const table = document.createElement('table');
          table.className = 'data-table';
          table.innerHTML = `<thead><tr>
            <th class="sortable${sortKey==='title'?' sort-active':''}" data-sort="title">Title ${titleIcon}</th>
            <th class="sortable${sortKey==='series'?' sort-active':''}" data-sort="series">Series ${seriesIcon}</th>
          </tr></thead>`;
          const tbody = document.createElement('tbody');
          sorted.forEach(b => {
            const seriesInfo = (b.series || []).map(s => `${s.name}${s.position ? ' #' + s.position : ''}`).join(', ');
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><a href="#/library/book?book_id=${b.id}">${escapeHtml(b.title)}</a></td>
              <td class="td-dim">${escapeHtml(seriesInfo) || '—'}</td>
            `;
            tbody.appendChild(tr);
          });
          table.appendChild(tbody);
          table.querySelector('thead').addEventListener('click', e => {
            const th = e.target.closest('th[data-sort]');
            if (!th) return;
            const key = th.dataset.sort;
            if (key === sortKey) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
            else { sortKey = key; sortDir = 'asc'; }
            container.innerHTML = '';
            renderAuthorTable();
          });
          container.innerHTML = '';
          container.appendChild(table);
        }
        renderAuthorTable();
      } else {
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        books.forEach(b => grid.appendChild(renderBookCard(b)));
        container.appendChild(grid);
      }
    }
    async function loadAlsoBy() {
      const sec = document.getElementById('author-also-by-section');
      if (!sec) return;
      sec.innerHTML = `<div class="section-heading mt-2">Also by this Author</div><div class="state-loading">Checking Hardcover…</div>`;
      try {
        const data = await api(`/authors/${id}/also-by`);
        if (data.error || !data.items || !data.items.length) {
          sec.innerHTML = '';
          return;
        }
        sec.innerHTML = `<div class="section-heading mt-2">Also by this Author (${data.items.length})</div>`;
        data.items.forEach(result => {
          const card = document.createElement('div');
          card.className = 'search-card';
          populateBookCard(card, result, null);
          sec.appendChild(card);
        });
      } catch {
        sec.innerHTML = '';
      }
    }

    renderAuthorBooksView();
    loadAlsoBy();
  } catch (err) {
    renderError(app, render);
  }
});

// Library: Series list
route('/library/series', async (params, qp) => {
  const savedScroll = JSON.parse(sessionStorage.getItem('series_list_scroll') || 'null');
  sessionStorage.removeItem('series_list_scroll');

  app.innerHTML = `<div class="narrow-page">
    <div class="page-header"><span class="page-title">${ICON_SERIES} Series</span></div>
    <div id="series-content"></div>
  </div>`;
  const content = document.getElementById('series-content');
  let seriesUnlinked = qp.unlinked === '1';
  const seriesTable = renderTable({
    container: content,
    stateKey: 'series',
    headers: [
      { label: 'Name', key: 'name', sortable: true },
      { label: 'Books', key: 'library_count', sortable: true, style: 'width:80px' },
      { label: 'Missing', style: 'width:90px' },
    ],
    fetchFn: (p) => api('/series?' + new URLSearchParams(p).toString()),
    extraFetchParams: () => seriesUnlinked ? { unlinked: '1' } : {},
    extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="series-unlinked-cb"${seriesUnlinked ? ' checked' : ''}> Unlinked only</label>`,
    renderRow: (s) => {
      const badge = seriesStatusBadge(s) || `<span class="td-dim" style="font-size:0.75rem">—</span>`;
      return `
        <td><a href="#/library/series/${s.id}">${escapeHtml(s.name)}</a></td>
        <td><span class="badge badge-in_library">${s.library_count || 0}</span>${s.requested_count > 0 ? ` <span class="badge badge-requested">${s.requested_count}</span>` : ''}</td>
        <td>${badge}</td>
      `;
    },
    emptyMessage: 'No series yet. Series are added automatically when books with series data are synced.',
    restoreScroll: savedScroll || undefined,
  });
  content.addEventListener('click', e => {
    if (e.target.closest('a[href^="#/library/series/"]')) {
      sessionStorage.setItem('series_list_scroll', JSON.stringify({ scrollY: window.scrollY, count: seriesTable.getCount() }));
    }
  });
  content.querySelector('#series-unlinked-cb').addEventListener('change', e => {
    seriesUnlinked = e.target.checked;
    seriesTable.reload();
  });
});

// Library: Series detail
route('/library/series/:id', async ({ id }) => {
  const ICON_LIST_V = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;
  const ICON_GRID_V = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`;
  renderLoading(app);
  try {
    const [booksData, seriesData] = await Promise.all([
      api(`/series/${id}/books`),
      api(`/series/${id}`),
    ]);

    const seriesName = seriesData.name
      || (booksData.length && booksData[0].series
        ? (booksData[0].series.find(s => s.id === id) || booksData[0].series[0] || {}).name
        : '') || 'Series';

    const inLibrary = seriesData.library_count || 0;
    const requested = seriesData.requested_count || 0;

    function renderSeriesBooksView() {
      const view = localStorage.getItem('detail_view') || 'list';
      app.innerHTML = `<div class="narrow-page">
        <div class="page-header">
          <span class="page-title">${ICON_SERIES} ${escapeHtml(seriesName)}</span>
          <div class="view-toggle">
            <button class="view-toggle-btn${view === 'poster' ? ' active' : ''}" id="vt-poster" title="Poster">${ICON_GRID_V}</button>
            <button class="view-toggle-btn${view === 'list' ? ' active' : ''}" id="vt-list" title="List">${ICON_LIST_V}</button>
          </div>
        </div>
        <div id="series-stats">${renderDetailStats(seriesName, { inLibrary, requested, missing: null, upcoming: null, total: null })}</div>
        <div class="section-heading">Books in Library</div>
        <div id="series-books"></div>
        <div id="series-missing-section"></div>
        ${isAdmin() ? `<div id="series-pack-section" class="mt-2"></div>` : ''}
        <div id="series-hc-section" class="mt-2"></div>
      </div>`;
      document.getElementById('vt-poster').onclick = () => { localStorage.setItem('detail_view', 'poster'); stopPackPoll(); renderSeriesBooksView(); loadSeriesExtras(); loadMissing(); if (isAdmin()) loadSeriesPackSection(); };
      document.getElementById('vt-list').onclick   = () => { localStorage.setItem('detail_view', 'list');   stopPackPoll(); renderSeriesBooksView(); loadSeriesExtras(); loadMissing(); if (isAdmin()) loadSeriesPackSection(); };

      const booksContainer = document.getElementById('series-books');
      if (!booksData.length) {
        booksContainer.innerHTML = `<p class="td-dim" style="padding:0.5rem 0">The shelves are bare.</p>`;
        return;
      }
      if (view === 'list') {
        const table = document.createElement('table');
        table.className = 'data-table';
        table.innerHTML = `<thead><tr><th style="width:3rem">#</th><th>Title</th><th style="width:100px">Formats</th></tr></thead>`;
        const tbody = document.createElement('tbody');
        booksData.forEach(b => {
          const fmtBadges = (b.formats || []).map(f => `<span class="badge badge-in_library" title="${f.type}${f.narrator ? ' — ' + f.narrator : ''}">${typeIcon(f.type)}</span>`).join(' ');
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td class="td-dim">${b.series_position != null ? b.series_position : '—'}</td>
            <td><a href="#/library/book?book_id=${b.id}">${escapeHtml(b.title)}</a></td>
            <td>${fmtBadges || '<span class="td-dim">—</span>'}</td>
          `;
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        booksContainer.appendChild(table);
      } else {
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        booksData.forEach(b => {
          const card = renderBookCard(b);
          if (b.series_position != null) {
            const cover = card.querySelector('.book-card-cover, .book-card-cover-placeholder');
            if (cover) {
              const wrap = document.createElement('div');
              wrap.style.cssText = 'position:relative';
              cover.replaceWith(wrap);
              wrap.appendChild(cover);
              const badge = document.createElement('span');
              badge.className = 'series-pos-badge';
              badge.textContent = `#${b.series_position}`;
              wrap.appendChild(badge);
            }
          }
          grid.appendChild(card);
        });
        booksContainer.appendChild(grid);
      }
    }
    renderSeriesBooksView();

    async function loadSeriesExtras() {
      try {
        const [s, seriesData] = await Promise.all([
          api('/settings'),
          api(`/series/${id}`),
        ]);
        const hcSeriesId = (seriesData.link || {}).hardcover_series_id;
        const hcSeriesSlug = (seriesData.link || {}).hardcover_series_slug;

        const seriesHcSection = document.getElementById('series-hc-section');
        if (seriesHcSection) {
          setupHcCard(seriesHcSection, 'series', id, hcSeriesId, hcSeriesSlug);
        }

        if (!(s.general || {}).debug_view) return;
        const link = seriesData.link || {};
        const rows = Object.entries(link).map(([k, v]) =>
          `<tr><td class="td-dim" style="white-space:nowrap;padding-right:1rem">${escapeHtml(k)}</td><td>${escapeHtml(String(v ?? '—'))}</td></tr>`
        ).join('');
        const dbg = document.getElementById('series-debug-section');
        if (dbg) dbg.innerHTML = `
          <div class="section-heading mt-2">Debug: Links</div>
          <div class="card" style="overflow-x:auto">
            <table class="data-table"><tbody>${rows}</tbody></table>
          </div>
        `;
      } catch {}
    }

    async function loadMissing() {
      const sec = document.getElementById('series-missing-section');
      if (!sec) return;
      sec.innerHTML = `<div class="section-heading mt-2">Missing from Series</div><div class="state-loading">Checking Hardcover…</div>`;
      try {
        const data = await api(`/series/${id}/missing`);
        if (data.items && !data.error) {
          const nMissing  = data.items.filter(b => !_isUnreleased(b)).length;
          const nUpcoming = data.items.filter(b =>  _isUnreleased(b)).length;
          const total = inLibrary + nMissing + nUpcoming;
          const statsEl = document.getElementById('series-stats');
          if (statsEl) {
            statsEl.innerHTML = renderDetailStats(seriesName, {
              inLibrary, requested, missing: nMissing, upcoming: nUpcoming, total,
            });
          }
        }

        const showSecondary = !!data.show_secondary_works;
        const toggleChk = `<label class="missing-secondary-label"><input type="checkbox" id="missing-secondary-toggle"${showSecondary ? ' checked' : ''}> Non-primary works</label>`;

        if (data.error || !data.items || !data.items.length) {
          sec.innerHTML = data.items && !data.items.length
            ? `<div class="section-heading-row mt-2"><span class="section-heading">Missing from Series</span>${toggleChk}</div><p class="td-dim" style="padding:0.5rem 0">All books accounted for.</p>`
            : '';
        } else {
          const missing  = data.items.filter(b => !_isUnreleased(b));
          const upcoming = data.items.filter(b =>  _isUnreleased(b));

          sec.innerHTML = '';

          function renderSubsection(items, heading, headingClass, anchorId) {
            if (!items.length) return;
            const headRow = document.createElement('div');
            headRow.className = 'section-heading-row mt-2';
            if (anchorId) headRow.id = anchorId;
            headRow.innerHTML = `<span class="section-heading ${headingClass}">${heading} (${items.length}${data.truncated ? '+' : ''})</span>`;
            if (heading.startsWith('Missing')) headRow.appendChild((() => { const d = document.createElement('div'); d.innerHTML = toggleChk; return d.firstChild; })());
            sec.appendChild(headRow);

            items.forEach(result => {
              const card = document.createElement('div');
              card.className = 'search-card';
              populateBookCard(card, result, null);
              if (result.series_position) {
                const titleRow = card.querySelector('.search-card-title-row');
                const titleEl = titleRow && titleRow.querySelector('.search-card-title');
                if (titleRow && titleEl) {
                  const badge = document.createElement('span');
                  badge.className = 'badge';
                  badge.style.cssText = 'background:var(--surface2);color:var(--text-dim);margin-right:0.4rem;font-size:0.75rem;vertical-align:middle;flex-shrink:0';
                  badge.textContent = `#${result.series_position}`;
                  titleRow.insertBefore(badge, titleEl);
                }
              }
              if (result.in_library && result.book_id) {
                const fmtRows = card.querySelector('.search-card-fmt-rows');
                if (fmtRows) {
                  const row = document.createElement('div');
                  row.className = 'fmt-row fmt-add-series-row';
                  const lbl = document.createElement('span');
                  lbl.className = 'fmt-label';
                  lbl.textContent = 'Series';
                  const btn = document.createElement('button');
                  btn.className = 'btn btn-primary btn-sm';
                  btn.textContent = 'Add to this series';
                  btn.addEventListener('click', async () => {
                    btn.disabled = true;
                    btn.textContent = 'Adding…';
                    try {
                      await api(`/series/${id}/link-library-book`, {
                        method: 'POST',
                        body: { book_id: result.book_id, position: result.series_position || null },
                      });
                      btn.textContent = 'Added';
                      setTimeout(() => loadMissing(), 800);
                    } catch {
                      btn.disabled = false;
                      btn.textContent = 'Add to this series';
                      showToast('Failed to add book to series', 'error');
                    }
                  });
                  row.appendChild(lbl);
                  row.appendChild(btn);
                  fmtRows.appendChild(row);
                }
              }
              sec.appendChild(card);
            });
          }

          renderSubsection(missing,  'Missing from Series', '', 'series-section-missing');
          renderSubsection(upcoming, 'Upcoming',            '', 'series-section-upcoming');

          // toggle only wired to Missing heading — re-attach after render
        }

        const toggleEl = document.getElementById('missing-secondary-toggle');
        if (toggleEl) {
          toggleEl.addEventListener('change', async () => {
            toggleEl.disabled = true;
            await api(`/series/${id}`, { method: 'PATCH', body: { show_secondary_works: toggleEl.checked } });
            loadMissing();
          });
        }
      } catch (err) {
        sec.innerHTML = '';
        const missingCard = document.getElementById('series-stat-missing');
        if (missingCard) missingCard.querySelector('.stat-value').textContent = '—';
      }
    }

    // Series pack section: shows download status, review UI, or search button
    let packPollTimer = null;

    function stopPackPoll() {
      if (packPollTimer) { clearTimeout(packPollTimer); packPollTimer = null; }
    }

    async function loadSeriesPackSection() {
      const sec = document.getElementById('series-pack-section');
      if (!sec) return;
      stopPackPoll();

      let dl = null;
      try {
        const downloads = await api(`/series/${id}/series-downloads`);
        dl = downloads && downloads[0];
      } catch { /* ignore, treat as no active download */ }

      if (!dl) {
        renderPackSearchUI(sec);
        return;
      }

      const { status } = dl;

      if (status === 'snatched' || status === 'downloading') {
        sec.innerHTML = `
          <div class="section-heading-row">
            <span class="section-heading">Series Pack</span>
          </div>
          <div class="card" style="padding:0.75rem 1rem">
            <div style="display:flex;align-items:center;gap:0.6rem;color:var(--text-dim)">
              ${ICON_SPINNER} Downloading pack…
            </div>
          </div>`;
        packPollTimer = setTimeout(loadSeriesPackSection, 10000);

      } else if (status === 'rescanning') {
        sec.innerHTML = `
          <div class="section-heading-row">
            <span class="section-heading">Series Pack</span>
          </div>
          <div class="card" style="padding:0.75rem 1rem">
            <div style="display:flex;align-items:center;gap:0.6rem;color:var(--text-dim)">
              ${ICON_SPINNER} Re-scanning mappings…
            </div>
          </div>`;
        packPollTimer = setTimeout(loadSeriesPackSection, 3000);

      } else if (status === 'awaiting_review') {
        renderPackReviewUI(sec, dl);

      } else if (status === 'organizing') {
        sec.innerHTML = `
          <div class="section-heading-row">
            <span class="section-heading">Series Pack</span>
          </div>
          <div class="card" style="padding:0.75rem 1rem">
            <div style="display:flex;align-items:center;gap:0.6rem;color:var(--text-dim)">
              ${ICON_SPINNER} Organising…
            </div>
          </div>`;
        packPollTimer = setTimeout(loadSeriesPackSection, 5000);

      } else {
        renderPackSearchUI(sec);
      }
    }

    function renderPackSearchUI(sec) {
      sec.innerHTML = `
        <div class="section-heading">Series Pack</div>
        <div style="margin-bottom:0.75rem">
          <button class="btn btn-primary btn-sm" id="series-pack-search-btn">${ICON_SEARCH} Search Prowlarr</button>
        </div>
        <div id="series-pack-results"></div>`;

      document.getElementById('series-pack-search-btn').onclick = async (e) => {
        const btn = e.currentTarget;
        const resultsEl = document.getElementById('series-pack-results');
        btn.disabled = true;
        btn.innerHTML = ICON_SPINNER + ' Searching…';
        resultsEl.innerHTML = '';
        try {
          const data = await api(`/series/${id}/search-pack`, { method: 'POST' });
          if (data.error) {
            resultsEl.innerHTML = `<div class="text-dim">${escapeHtml(data.error)}</div>`;
          } else {
            renderSeriesPackResults(resultsEl, data.results || []);
          }
        } catch {
          resultsEl.innerHTML = `<div class="text-dim">Search failed.</div>`;
        } finally {
          btn.disabled = false;
          btn.innerHTML = ICON_SEARCH + ' Search Prowlarr';
        }
      };
    }

    function renderPackReviewUI(sec, dl) {
      // Handle both old flat-array format and new object format
      const raw = dl.proposed_mappings || {};
      const fileMappings = Array.isArray(raw) ? raw : (raw.file_mappings || []);
      const seriesBooks = Array.isArray(raw) ? [] : (raw.series_books || []);

      // State: per-file selected book_id (null = skip)
      // Seed from the best-match: place/skip_in_library use book_id, no_match uses null
      const selections = fileMappings.map(m => m.book_id || null);

      function getConfirmed() {
        return fileMappings
          .map((m, i) => selections[i] ? {
            filepath: m.filepath,
            filename: m.filename,
            book_id: selections[i],
            book_title: (seriesBooks.find(b => b.id === selections[i]) || {}).title || m.book_title || '',
            score: m.score,
            action: 'place',
          } : null)
          .filter(Boolean);
      }

      function renderGapsSummary(container) {
        const usedIds = new Set(selections.filter(Boolean));
        const gaps = seriesBooks.filter(b => !usedIds.has(b.id) && !b.in_library);
        container.innerHTML = '';
        if (!gaps.length) return;
        const div = document.createElement('div');
        div.style.cssText = 'padding:0.5rem 1rem;font-size:0.8rem;color:var(--text-dim);border-top:1px solid var(--border)';
        div.textContent = `${gaps.length} book${gaps.length !== 1 ? 's' : ''} without a file: ${gaps.map(g => g.title).join(', ')}`;
        container.appendChild(div);
      }

      function updateFooter(footerEl) {
        const confirmed = getConfirmed();
        const btn = footerEl.querySelector('.pack-confirm-btn');
        if (!btn) return;
        btn.disabled = confirmed.length === 0;
        btn.innerHTML = confirmed.length === 0
          ? 'Nothing to organise'
          : `${ICON_CHECK} Confirm & organise (${confirmed.length} file${confirmed.length !== 1 ? 's' : ''})`;
      }

      sec.innerHTML = '';

      const headingRow = document.createElement('div');
      headingRow.className = 'section-heading-row';
      headingRow.innerHTML = `
        <span class="section-heading">Series Pack — Review Mappings</span>
        <button class="btn btn-secondary btn-sm" id="pack-rescan-btn" style="margin-left:auto">↺ Re-scan</button>`;
      sec.appendChild(headingRow);

      headingRow.querySelector('#pack-rescan-btn').onclick = async (e) => {
        e.target.disabled = true;
        e.target.innerHTML = ICON_SPINNER;
        try {
          await api(`/series/${id}/series-downloads/${dl.id}/rescan`, { method: 'POST' });
          loadSeriesPackSection();
        } catch (err) {
          toast('Re-scan failed: ' + err.message, 'error');
          e.target.disabled = false;
          e.target.innerHTML = '↺ Re-scan';
        }
      };

      const card = document.createElement('div');
      card.className = 'card';
      card.style.padding = '0';
      sec.appendChild(card);

      const list = document.createElement('div');
      card.appendChild(list);

      fileMappings.forEach((m, i) => {
        const row = document.createElement('div');
        row.style.cssText = 'padding:0.5rem 1rem;border-bottom:1px solid var(--border)';

        const fnDiv = document.createElement('div');
        fnDiv.className = 'td-mono td-dim';
        fnDiv.style.cssText = 'font-size:0.75rem;overflow-wrap:anywhere;margin-bottom:0.3rem';
        fnDiv.textContent = m.filename;
        row.appendChild(fnDiv);

        const controlRow = document.createElement('div');
        controlRow.style.cssText = 'display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap';

        const sel = document.createElement('select');
        sel.style.cssText = 'flex:1;min-width:120px;max-width:340px;font-size:0.85rem;padding:0.2rem 0.4rem';

        const skipOpt = document.createElement('option');
        skipOpt.value = '';
        skipOpt.textContent = '— Skip —';
        sel.appendChild(skipOpt);

        seriesBooks.forEach(book => {
          const opt = document.createElement('option');
          opt.value = book.id;
          opt.textContent = book.title + (book.in_library ? ' (in library)' : '');
          sel.appendChild(opt);
        });

        sel.value = selections[i] || '';
        sel.onchange = () => {
          selections[i] = sel.value || null;
          renderGapsSummary(gapsDiv);
          updateFooter(footer);
        };
        controlRow.appendChild(sel);

        if (m.score != null && m.score > 0) {
          const badge = document.createElement('span');
          badge.className = 'badge';
          badge.style.cssText = 'background:var(--surface2);color:var(--text-dim);font-size:0.7rem;flex-shrink:0';
          badge.textContent = m.score;
          controlRow.appendChild(badge);
        }

        row.appendChild(controlRow);
        list.appendChild(row);
      });

      const gapsDiv = document.createElement('div');
      card.appendChild(gapsDiv);
      renderGapsSummary(gapsDiv);

      const footer = document.createElement('div');
      footer.style.cssText = 'padding:0.75rem 1rem;display:flex;gap:0.5rem;justify-content:flex-end;border-top:1px solid var(--border)';
      const confirmBtn = document.createElement('button');
      confirmBtn.className = 'btn btn-primary btn-sm pack-confirm-btn';
      footer.appendChild(confirmBtn);
      card.appendChild(footer);

      updateFooter(footer);

      confirmBtn.onclick = async () => {
        const confirmed = getConfirmed();
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = ICON_SPINNER + ' Starting…';
        try {
          await api(`/series/${id}/series-downloads/${dl.id}/confirm`, {
            method: 'POST',
            body: { mappings: confirmed },
          });
          toast('Organising series pack…');
          loadSeriesPackSection();
        } catch (err) {
          toast('Failed: ' + err.message, 'error');
          updateFooter(footer);
        }
      };
    }

    function renderSeriesPackResults(container, results) {
      if (!results.length) {
        container.innerHTML = `<div class="text-dim" style="padding:0.5rem 0">No results found.</div>`;
        return;
      }
      container.innerHTML = '';
      const sorted = [...results].sort((a, b) => (a.age ?? Infinity) - (b.age ?? Infinity));
      sorted.forEach(res => {
        const fmtMatch = (res.title || '').match(/\b(epub|mobi|azw3?|pdf)\b/i);
        const fmt = fmtMatch ? fmtMatch[1].toUpperCase() : '';
        const age = formatAge(res.age);
        const titleHtml = res.info_url
          ? `<a href="${escapeHtml(res.info_url)}" target="_blank" class="prowlarr-result-title">${escapeHtml(res.title || '—')}</a>`
          : `<div class="prowlarr-result-title">${escapeHtml(res.title || '—')}</div>`;
        const row = document.createElement('div');
        row.className = 'prowlarr-result-row';
        row.innerHTML = `
          ${titleHtml}
          <div class="prowlarr-result-meta">
            <div class="prowlarr-result-info">
              ${fmt ? `<span class="badge" style="background:var(--surface2);color:var(--text)">${fmt}</span>` : ''}
              <span>${res.protocol === 'torrent' ? 'Torrent' : 'Usenet'}</span>
              <span>${formatBytes(res.size)}</span>
              ${res.seeders != null ? `<span>${res.seeders}S</span>` : ''}
              ${age != null ? `<span class="td-dim">${age}</span>` : ''}
              <span>${escapeHtml(res.indexer || '—')}</span>
            </div>
            <button class="btn btn-primary btn-sm series-pack-dl-btn" style="flex-shrink:0">${ICON_DOWNLOAD}<span class="prowlarr-dl-label"> Download</span></button>
          </div>
        `;
        row.querySelector('.series-pack-dl-btn').onclick = async (e) => {
          const btn = e.currentTarget;
          btn.disabled = true;
          btn.innerHTML = ICON_SPINNER;
          try {
            await api(`/series/${id}/download-pack`, {
              method: 'POST',
              body: {
                download_url: res.download_url, protocol: res.protocol,
                indexer: res.indexer, guid: res.guid, title: res.title,
                info_url: res.info_url, size: res.size, type: 'ebook',
              },
            });
            btn.innerHTML = ICON_CHECK;
            btn.classList.replace('btn-primary', 'btn-success');
            toast('Series pack download started!');
            // Switch to polling view
            setTimeout(loadSeriesPackSection, 1500);
          } catch (err) {
            toast('Download failed: ' + err.message, 'error');
            btn.disabled = false;
            btn.innerHTML = `${ICON_DOWNLOAD}<span class="prowlarr-dl-label"> Download</span>`;
          }
        };
        container.appendChild(row);
      });
    }

    loadSeriesExtras();
    loadMissing();
    if (isAdmin()) loadSeriesPackSection();
  } catch (err) {
    renderError(app, render);
  }
});

// ── Book detail: request history helpers ──────────────────────────────────────

function historyEventIcon(type) {
  if (type === 'created')      return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>';
  if (type === 'state_change') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>';
  if (type === 'searched')     return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
  if (type === 'grabbed')      return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
  if (type === 'cancelled')    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
  return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/></svg>';
}

function historyEventLabel(ev) {
  const d = ev.detail || {};
  if (ev.event_type === 'created')
    return `Request created — ${d.status || ''}`;
  if (ev.event_type === 'state_change')
    return `Status: ${d.from || '?'} → ${d.to || '?'}` + (d.reason ? ` <span class="td-dim">— ${escapeHtml(d.reason)}</span>` : '');
  if (ev.event_type === 'searched')
    return `Searched Prowlarr — ${d.results ?? '?'} result${d.results === 1 ? '' : 's'}`;
  if (ev.event_type === 'grabbed') {
    const mb = d.size ? ` ${(d.size / 1024 / 1024).toFixed(0)} MB` : '';
    const titleHtml = d.info_url
      ? `<a href="${escapeHtml(d.info_url)}" target="_blank" style="color:var(--accent);text-decoration:none">${escapeHtml(d.title || '?')}</a>`
      : escapeHtml(d.title || '?');
    return `Grabbed: ${titleHtml} via ${escapeHtml(d.indexer || '?')}${mb}`;
  }
  if (ev.event_type === 'cancelled')
    return `Request cancelled`;
  return escapeHtml(ev.event_type);
}

function appendFormatHistory(container, bookId, type) {
  api(`/books/${bookId}/request-history`).then(events => {
    // Build request_id → type map: prefer live JOIN data, fall back to created event detail
    const reqTypeMap = {};
    for (const ev of events) {
      if (ev.request_type) reqTypeMap[ev.request_id] = ev.request_type;
      else if (ev.event_type === 'created' && (ev.detail || {}).type) reqTypeMap[ev.request_id] = ev.detail.type;
    }
    const filtered = events.filter(ev => reqTypeMap[ev.request_id] === type);
    if (!filtered.length) return;
    const rows = filtered.map(ev => {
      const ts = ev.created_at ? new Date(ev.created_at).toLocaleString() : '';
      return `<div class="history-row">
        <span class="history-icon td-dim">${historyEventIcon(ev.event_type)}</span>
        <span class="history-label">${historyEventLabel(ev)}</span>
        <span class="history-ts td-dim">${ts}</span>
      </div>`;
    }).join('');
    const histEl = document.createElement('div');
    histEl.className = 'detail-fmt-history mt-1';
    histEl.innerHTML = `<div class="td-dim" style="font-size:0.78rem;margin-bottom:0.25rem;margin-top:0.75rem">History</div><div class="history-timeline">${rows}</div>`;
    const detail = container.querySelector('.detail-fmt-detail');
    if (detail) detail.appendChild(histEl);
  }).catch(() => {});
}

// ── Book detail: format rows ───────────────────────────────────────────────────

function renderDetailFormats(container, book, onRefresh) {
  const libraryFormats = book.formats || [];
  const activeRequests = book.requests || [];
  const bookId = book.id;

  const fmtKey = (type, narrator) => `${type}::${narrator || ''}`;
  const rows = [];
  const seen = new Set();

  for (const fmt of libraryFormats) {
    const key = fmtKey(fmt.type, fmt.narrator);
    seen.add(key);
    rows.push({ status: 'in_library', type: fmt.type, narrator: fmt.narrator || null, fmt, request: null });
  }
  for (const req of activeRequests) {
    const key = fmtKey(req.type, req.narrator);
    if (!seen.has(key)) {
      seen.add(key);
      rows.push({ status: req.status, type: req.type, narrator: req.narrator || null, fmt: null, request: req });
    }
  }
  for (const type of ['ebook', 'audiobook']) {
    if (!rows.some(r => r.type === type)) {
      rows.push({ status: 'missing', type, narrator: null, fmt: null, request: null });
    }
  }

  container.innerHTML = '';
  rows.forEach(row => {
    const wrap = document.createElement('div');
    wrap.className = 'collapsible-row';

    const badgeCls = row.status === 'in_library'
      ? 'badge-completed'
      : row.status === 'missing'
        ? 'badge-neutral'
        : `badge-${row.status}`;
    const badgeTitle = row.status === 'in_library' ? 'In library' : row.status;
    const typeLabel = row.type === 'audiobook' ? 'Audiobook' : 'Ebook';
    const narratorHtml = row.narrator
      ? `<span class="detail-fmt-narrator">${escapeHtml(row.narrator)}</span>`
      : '';

    wrap.innerHTML = `
      <button class="collapsible-trigger">
        <span class="badge ${badgeCls}" title="${badgeTitle}">${typeIcon(row.type)}</span>
        <span class="detail-fmt-type">${typeLabel}</span>
        ${narratorHtml}
        <span class="collapsible-chevron">${ICON_CHEVRON_DOWN}</span>
      </button>
      <div class="collapsible-content" style="display:none"></div>
    `;

    const trigger = wrap.querySelector('.collapsible-trigger');
    const content = wrap.querySelector('.collapsible-content');
    trigger.onclick = () => {
      const open = content.style.display !== 'none';
      if (open) {
        content.style.display = 'none';
        trigger.querySelector('.collapsible-chevron').classList.remove('open');
      } else {
        content.style.display = '';
        trigger.querySelector('.collapsible-chevron').classList.add('open');
        if (!content.dataset.populated) {
          content.dataset.populated = '1';
          renderDetailFormatContent(content, row, bookId, onRefresh);
        }
      }
    };
    container.appendChild(wrap);
  });
}

// ── Shared: Prowlarr result list ──────────────────────────────────────────────
// Renders Prowlarr search results into `container`. Each result gets a Download
// button wired to POST /requests/{reqId}/download. onSuccess() called after.
function renderProwlarrResults(container, results, reqId, onSuccess) {
  if (!results || !results.length) {
    container.innerHTML = `<div class="text-dim">No results found.</div>`;
    return;
  }
  container.innerHTML = '';
  const sorted = [...results].sort((a, b) => (a.age ?? Infinity) - (b.age ?? Infinity));
  sorted.forEach(res => {
    const fmtMatch = (res.title || '').match(/\b(mp3|m4b|m4a|flac|opus|ogg|aac|epub|mobi|azw3?|pdf)\b/i);
    const fmt = fmtMatch ? fmtMatch[1].toUpperCase() : '';
    const age = formatAge(res.age);
    const titleHtml = res.info_url
      ? `<a href="${escapeHtml(res.info_url)}" target="_blank" class="prowlarr-result-title">${escapeHtml(res.title || '—')}</a>`
      : `<div class="prowlarr-result-title">${escapeHtml(res.title || '—')}</div>`;
    const row = document.createElement('div');
    row.className = 'prowlarr-result-row';
    row.innerHTML = `
      ${titleHtml}
      <div class="prowlarr-result-meta">
        <div class="prowlarr-result-info">
          ${fmt ? `<span class="badge" style="background:var(--surface2);color:var(--text)">${fmt}</span>` : ''}
          <span>${res.protocol === 'torrent' ? 'Torrent' : 'Usenet'}</span>
          <span>${formatBytes(res.size)}</span>
          ${res.seeders != null ? `<span>${res.seeders}S</span>` : ''}
          ${age != null ? `<span class="td-dim">${age}</span>` : ''}
          <span>${escapeHtml(res.indexer || '—')}</span>
        </div>
        ${isAdmin() ? `<button class="btn btn-primary btn-sm prowlarr-dl-btn" style="flex-shrink:0">${ICON_DOWNLOAD}<span class="prowlarr-dl-label"> Download</span></button>` : ''}
      </div>
    `;
    row.querySelector('.prowlarr-dl-btn').onclick = async (e) => {
      const btn = e.currentTarget;
      btn.disabled = true;
      btn.innerHTML = ICON_SPINNER;
      try {
        await api(`/requests/${reqId}/download`, {
          method: 'POST',
          body: { download_url: res.download_url, protocol: res.protocol, indexer: res.indexer, guid: res.guid, title: res.title, info_url: res.info_url, size: res.size },
        });
        btn.innerHTML = ICON_CHECK;
        btn.classList.replace('btn-primary', 'btn-success');
        toast('Download started!');
        if (onSuccess) onSuccess();
      } catch (err) {
        toast('Download failed: ' + err.message, 'error');
        btn.disabled = false;
        btn.innerHTML = `${ICON_DOWNLOAD}<span class="prowlarr-dl-label"> Download</span>`;
      }
    };
    container.appendChild(row);
  });
}

function renderDetailFormatContent(container, row, bookId, onRefresh) {
  const refresh = onRefresh || (() => {});
  if (row.status === 'in_library') {
    const fmt = row.fmt;
    container.innerHTML = `
      <div class="detail-fmt-detail">
        ${fmt.abs_url ? `<div class="detail-fmt-kv"><a href="${escapeHtml(fmt.abs_url)}" target="_blank" class="detail-fmt-link">Open in AudioBookShelf</a></div>` : ''}
        ${fmt.abs_id ? `<div class="detail-fmt-kv"><span class="td-dim">ABS item</span> <span class="td-mono">${escapeHtml(fmt.abs_id)}</span></div>` : ''}
        ${fmt.fulfilled_by_request_id ? `<div class="detail-fmt-kv"><span class="td-dim">Download request</span> <span class="td-mono">${escapeHtml(fmt.fulfilled_by_request_id)}</span></div>` : ''}
        ${!fmt.abs_id && !fmt.fulfilled_by_request_id ? `<div class="detail-fmt-kv td-dim">Added from AudioBookShelf library</div>` : ''}
      </div>
    `;
  } else if (row.status !== 'missing') {
    const req = row.request;
    const canSearch = isAdmin() && ['requested', 'failed', 'completed'].includes(req.status);
    const canRetry = isAdmin() && req.status === 'failed';
    const canCancel = isAdmin() || !_authUser || !req.requested_by_user_id || req.requested_by_user_id === _authUser?.user_id;
    container.innerHTML = `
      <div class="detail-fmt-detail">
        <div class="detail-fmt-kv"><span class="td-dim">Status</span> <span class="badge badge-${req.status}">${escapeHtml(req.status)}</span></div>
        ${isAdmin() && req.requested_by_username ? `<div class="detail-fmt-kv"><span class="td-dim">Requested by</span> <span>${escapeHtml(req.requested_by_username)}</span></div>` : ''}
        <div class="detail-fmt-actions">
          ${canRetry ? `<button class="btn btn-primary btn-sm detail-fmt-retry">Retry organize</button>` : ''}
          ${canSearch ? `<button class="btn btn-secondary btn-sm detail-fmt-search">${ICON_SEARCH} Search Prowlarr</button>` : ''}
          ${canCancel ? `<button class="btn btn-secondary btn-sm detail-fmt-cancel">Cancel</button>` : ''}
        </div>
        <div class="detail-fmt-search-results mt-1"></div>
      </div>
    `;
    if (canRetry) {
      const retryBtn = container.querySelector('.detail-fmt-retry');
      retryBtn.onclick = async () => {
        retryBtn.disabled = true;
        retryBtn.textContent = 'Retrying…';
        try {
          await api(`/requests/${req.id}/organize`, { method: 'POST' });
          toast('Organize restarted');
          setTimeout(refresh, 1500);
        } catch {
          toast('Retry failed', 'error');
          retryBtn.disabled = false;
          retryBtn.textContent = 'Retry organize';
        }
      };
    }
    if (canCancel) container.querySelector('.detail-fmt-cancel').onclick = async () => {
      try {
        await api(`/requests/${req.id}`, { method: 'DELETE' });
        toast('Request cancelled');
        refresh();
      } catch {
        toast('Failed to cancel request', 'error');
      }
    };
    if (canSearch) {
      container.querySelector('.detail-fmt-search').onclick = async (e) => {
        const btn = e.currentTarget;
        const resultsEl = container.querySelector('.detail-fmt-search-results');
        btn.disabled = true;
        btn.innerHTML = ICON_SPINNER + ' Searching…';
        try {
          const data = await api(`/requests/${req.id}/search-indexers`, { method: 'POST' });
          const results = data.results || [];
          if (data.error) {
            resultsEl.innerHTML = `<div class="text-dim">${escapeHtml(data.error)}</div>`;
          } else {
            renderProwlarrResults(resultsEl, results, req.id, refresh);
          }
        } catch {
          resultsEl.innerHTML = `<div class="text-dim">Search failed.</div>`;
        } finally {
          btn.disabled = false;
          btn.innerHTML = ICON_SEARCH + ' Search Prowlarr';
        }
      };
    }
  } else {
    const isAudio = row.type === 'audiobook';
    container.innerHTML = `
      <div class="detail-fmt-detail">
        <div class="detail-fmt-request-form">
          ${isAudio ? `<input type="text" class="input detail-fmt-narrator-input" placeholder="Narrator (optional)">` : ''}
          <button class="btn btn-primary btn-sm detail-fmt-request-btn">Request ${escapeHtml(row.type)}</button>
        </div>
      </div>
    `;
    container.querySelector('.detail-fmt-request-btn').onclick = async () => {
      const narrator = isAudio ? (container.querySelector('.detail-fmt-narrator-input')?.value.trim() || null) : null;
      try {
        const result = await api('/requests', { method: 'POST', body: { book_id: bookId, type: row.type, narrator } });
        if (result.skipped) toast('Already requested', 'info');
        else toast('Request created');
        refresh();
      } catch {
        toast('Failed to create request', 'error');
      }
    };
  }
  appendFormatHistory(container, bookId, row.type);
}

// Book detail
route('/library/book', async (params, qp) => {
  const bookId = qp.book_id;
  if (!bookId) { app.innerHTML = `<div class="state-empty mt-2">No book specified.</div>`; return; }
  renderLoading(app);
  try {
    const book = await api(`/books/${bookId}`);
    const hcSlug = (book.link || {}).hardcover_slug;
    const hcUrl = hcSlug ? `https://hardcover.app/books/${hcSlug}` : '';

    const authorHtml = (book.authors || []).map(a => {
      const name = escapeHtml(a.name);
      return a.id ? `<a href="#/library/authors/${a.id}" class="detail-link">${name}</a>` : name;
    }).join(', ');
    const seriesItems = (book.series || []).map(s => {
      const pos = s.position;
      const posFmt = pos ? (() => { const n = parseFloat(pos); return isNaN(n) ? pos : (n % 1 === 0 ? String(Math.floor(n)) : String(n)); })() : '';
      const label = escapeHtml(s.name) + (posFmt ? ' #' + posFmt : '');
      return (s.id && s.library_count > 0) ? `<a href="#/library/series/${s.id}" class="detail-link">${label}</a>` : label;
    });

    app.innerHTML = `<div class="narrow-page">
      <div class="page-header">
        <span class="page-title">${ICON_EBOOK} ${escapeHtml(book.title)}</span>
      </div>
      <div class="card mb-2">
        <div class="book-detail-card">
          ${book.cover_url
            ? `<img class="detail-cover${book.cover_url.startsWith('/api/abs/') ? ' abs-cover' : ''}" src="${escapeHtml(book.cover_url)}" alt="" loading="lazy">`
            : `<div class="detail-cover-placeholder">${ICON_EBOOK}</div>`
          }
          <div class="book-detail-card-meta">
            ${authorHtml ? `<div class="detail-author">${authorHtml}</div>` : ''}
            ${seriesItems.length ? `<div class="detail-series">${seriesItems.join('<br>')}</div>` : ''}
            ${book.rating ? `<div class="detail-rating">${ICON_STAR} ${book.rating.toFixed(1)} <span style="opacity:0.6">(${book.rating_count || 0})</span></div>` : ''}
            ${book.release_date ? `<div class="detail-release-date td-dim">${(book.release_date >= new Date().toISOString().slice(0,10) || (book.release_date.endsWith('-01-01') && book.release_date.substring(0,4) >= String(new Date().getFullYear()))) ? '<span class="badge badge-neutral">Unreleased</span> ' : ''}${book.release_date.endsWith('-01-01') && book.release_date.substring(0,4) >= String(new Date().getFullYear()) ? book.release_date.substring(0,4) : book.release_date}</div>` : ''}
            ${hcUrl ? `<a href="${escapeHtml(hcUrl)}" target="_blank" class="detail-hc-link">${ICON_HC()} Hardcover</a>` : ''}
          </div>
        </div>
      </div>
      <div class="section-heading">Formats</div>
      <div id="book-formats-section"></div>
      <div id="book-abs-section" class="mt-2"></div>
      <div id="book-hc-section" class="mt-2"></div>
      <div id="book-debug-section"></div>
    </div>`;

    renderDetailFormats(document.getElementById('book-formats-section'), book, () => {
      api(`/books/${bookId}`).then(updated => {
        renderDetailFormats(document.getElementById('book-formats-section'), updated, null);
      }).catch(() => {});
    });

    // HC match section
    const hcSection = document.getElementById('book-hc-section');
    if (hcSection) {
      setupHcCard(hcSection, 'book', bookId, (book.link || {}).hardcover_id, (book.link || {}).hardcover_slug);
    }

    // Debug card (async, only if debug_view is enabled)
    api('/settings').then(s => {
      if (!(s.general || {}).debug_view) return;
      const link = book.link || {};
      const bookRows = Object.entries(link).map(([k, v]) =>
        `<tr><td class="td-dim" style="white-space:nowrap;padding-right:1rem">book.${escapeHtml(k)}</td><td class="td-mono">${escapeHtml(String(v ?? '—'))}</td></tr>`
      ).join('');
      const authorRows = (book.authors || []).map(a =>
        `<tr><td class="td-dim" style="white-space:nowrap;padding-right:1rem">${escapeHtml(a.name)}</td>` +
        `<td class="td-mono">${escapeHtml(a.abs_author_id || '—')} / ${escapeHtml(a.hardcover_author_id || '—')}</td></tr>`
      ).join('');
      const authorHeader = (book.authors || []).length
        ? `<tr><td colspan="2" class="td-dim" style="padding-top:0.75rem;font-size:0.75rem">author — abs_id / hardcover_id</td></tr>${authorRows}`
        : '';
      const dbg = document.getElementById('book-debug-section');
      if (dbg) dbg.innerHTML = `
        <div class="section-heading mt-2">Debug: Links</div>
        <div class="card" style="overflow-x:auto">
          <table class="data-table"><tbody>${bookRows}${authorHeader}</tbody></table>
        </div>
      `;
    }).catch(() => {});

  } catch (err) {
    renderError(app, render);
  }
});

// Queue (Requests + Downloads tabs) — admins; plain Requests list — users
route('/requests', async (params, qp) => {
  if (!isAdmin()) {
    app.innerHTML = `<div class="narrow-page">
      <div class="page-header">
        <span class="page-title">${ICON_REQUESTS} Requests</span>
      </div>
      <div id="queue-content"></div>
    </div>`;
    const content = document.getElementById('queue-content');
    renderRequestsTab(content, qp);
    return;
  }

  const validTabs = ['requests', 'downloads', 'pending', 'search'];
  const tab = validTabs.includes(qp.tab) ? qp.tab : 'requests';

  app.innerHTML = `<div class="narrow-page">
    <div class="page-header">
      <span class="page-title">${ICON_REQUESTS} Queue</span>
    </div>
    <div class="tabs">
      <button class="tab-btn${tab === 'requests' ? ' active' : ''}" data-tab="requests">Requests</button>
      <button class="tab-btn${tab === 'downloads' ? ' active' : ''}" data-tab="downloads">Downloads</button>
      <button class="tab-btn${tab === 'pending' ? ' active' : ''}" data-tab="pending">Pending</button>
      <button class="tab-btn${tab === 'search' ? ' active' : ''}" data-tab="search">Search</button>
    </div>
    <div id="queue-content"></div>
  </div>`;

  app.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    btn.onclick = () => {
      const hp = getHashParams();
      if (btn.dataset.tab !== 'requests') hp.tab = btn.dataset.tab;
      else delete hp.tab;
      history.replaceState(null, '', buildHash('/requests', hp));
      render();
    };
  });

  const content = document.getElementById('queue-content');
  if (tab === 'downloads') { renderDownloadsTab(content); return; }
  if (tab === 'pending') { renderPendingTab(content); return; }
  if (tab === 'search') { renderSearchAllTab(content); return; }

  renderRequestsTab(content, qp);
});

function renderRequestsTab(content, qp) {
  const statusFilter = qp.requests_status || '';
  const typeFilter = qp.requests_type || '';

  const statusOptions = ['', 'requested', 'snatched', 'downloading', 'downloaded', 'merging', 'organizing', 'in_library', 'completed', 'failed'];
  const statusSelect = `
    <select id="status-filter">
      ${statusOptions.map(s => `<option value="${s}" ${s === statusFilter ? 'selected' : ''}>${s || 'All statuses'}</option>`).join('')}
    </select>
  `;
  const typeSelect = `
    <select id="type-filter">
      <option value="" ${!typeFilter ? 'selected' : ''}>All types</option>
      <option value="audiobook" ${typeFilter === 'audiobook' ? 'selected' : ''}>Audiobook</option>
      <option value="ebook" ${typeFilter === 'ebook' ? 'selected' : ''}>Ebook</option>
    </select>
  `;

  function fetchRequests(p) {
    const qs = new URLSearchParams(p);
    if (statusFilter) qs.set('status', statusFilter);
    if (typeFilter) qs.set('type', typeFilter);
    return api('/requests?' + qs.toString());
  }

  renderTable({
    container: content,
    stateKey: 'requests',
    headers: [
      { label: 'Book', key: 'book_title', sortable: true },
      { label: 'Author', key: 'author', sortable: false, klass: 'col-hide-mobile' },
      { label: 'Format', key: 'type', sortable: false },
      { label: 'Narrator', key: 'narrator', sortable: false, klass: 'col-hide-mobile' },
      { label: 'Created', key: 'created_at', sortable: true, klass: 'col-hide-mobile' },
      { label: '', key: '_actions', sortable: false, style: 'width:100px' },
    ],
    fetchFn: fetchRequests,
    extraControls: statusSelect + typeSelect,
    renderRow: (r, tr) => {
      tr.dataset.requestId = r.id;
      tr.dataset.reqStatus = r.status;
      tr.dataset.releaseDate = r.release_date || '';
      tr.innerHTML = `
        <td><a href="#/library/book?book_id=${r.book_id}">${escapeHtml(r.book_title || r.title || '—')}</a>${r.release_date && (r.release_date >= new Date().toISOString().slice(0,10) || (r.release_date.endsWith('-01-01') && r.release_date.substring(0,4) >= String(new Date().getFullYear()))) ? ` <span class="badge badge-neutral" title="${r.release_date.endsWith('-01-01') && r.release_date < new Date().toISOString().slice(0,10) ? 'Expected ' + r.release_date.substring(0,4) : 'Releases ' + r.release_date}">Unreleased</span>` : (r.release_date_fetched && !r.release_date ? ` <span class="badge badge-neutral" title="No release date known">No date</span>` : '')}</td>
        <td class="td-dim col-hide-mobile">${escapeHtml(r.author || '—')}</td>
        <td><span class="badge badge-${r.status}" title="${r.type} — ${r.status}">${typeIcon(r.type)}<span class="col-hide-mobile"> ${r.status}</span></span></td>
        <td class="td-dim col-hide-mobile">${escapeHtml(r.narrator || '—')}</td>
        <td class="td-dim col-hide-mobile">${formatDate(r.created_at)}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-delete style="color:var(--danger)">Delete</button>
        </td>
      `;
      tr.querySelector('[data-delete]').onclick = () => confirmAction(
        tr.querySelector('[data-delete]'), 'Confirm?', async () => {
          await api(`/requests/${r.id}`, { method: 'DELETE' });
          tr.remove();
          toast('Request deleted.');
        }
      )();
    },
    emptyMessage: statusFilter ? `No ${statusFilter} requests.` : 'No requests yet.',
  });

  // Wire up filter selects
  setTimeout(() => {
    document.getElementById('status-filter')?.addEventListener('change', e => {
      const hp = getHashParams();
      if (e.target.value) hp.requests_status = e.target.value;
      else delete hp.requests_status;
      location.hash = buildHash('/requests', hp).slice(1);
    });
    document.getElementById('type-filter')?.addEventListener('change', e => {
      const hp = getHashParams();
      if (e.target.value) hp.requests_type = e.target.value;
      else delete hp.requests_type;
      location.hash = buildHash('/requests', hp).slice(1);
    });
  }, 0);
}


// Shared: render the downloads tab content into a container element
function renderDownloadsTab(container) {
  container.innerHTML = `<div class="state-loading">${ICON_SPINNER}</div>`;
  let pollTimer;

  async function loadDownloads() {
    try {
      const data = await api('/downloads');

      if (data.client_unreachable) {
        if (!container.querySelector('#dl-warn')) {
          const el = document.createElement('div');
          el.id = 'dl-warn';
          el.className = 'banner-abs';
          el.style.cssText = 'margin-bottom:1rem;border-radius:4px';
          el.textContent = '⚠ Download client unreachable — showing last known status.';
          container.prepend(el);
        }
      }

      const items = data.items || data;
      if (!Array.isArray(items) || !items.length) {
        container.innerHTML = `<div class="state-empty">Nothing downloading right now.</div>`;
        return;
      }

      const listEl = container.querySelector('#dl-list') || (() => {
        container.innerHTML = '';
        const el = document.createElement('div');
        el.id = 'dl-list';
        container.appendChild(el);
        return el;
      })();

      listEl.innerHTML = items.map(dl => `
        <div class="card mb-1">
          <div style="display:flex;justify-content:space-between;gap:0.5rem;align-items:flex-start">
            <div>
              <div style="font-weight:500"><a href="#/requests/${dl.request_id}">${escapeHtml(dl.book_title || '—')}</a></div>
              <div class="text-dim" style="font-size:0.8rem">${escapeHtml(dl.author || '')}${dl.author && dl.type ? ' · ' : ''}${dl.type ? typeIcon(dl.type) : ''}</div>
              <div class="text-dim" style="font-size:0.75rem;margin-top:0.2rem">${escapeHtml(dl.release_title || dl.indexer || '')}</div>
            </div>
            <span class="badge badge-${dl.status || 'downloading'}" style="flex-shrink:0">${dl.status || 'downloading'}</span>
          </div>
          ${dl.progress != null ? `
            <div class="progress-bar-track mt-1">
              <div class="progress-bar-fill" style="width:${Math.round(dl.progress)}%"></div>
            </div>
            <div class="text-dim mt-1" style="font-size:0.78rem">
              ${Math.round(dl.progress)}%${formatEta(dl.eta) != null ? ' · ETA ' + formatEta(dl.eta) : ''}${dl.speed ? ' · ' + formatBytes(dl.speed) + '/s' : ''}${dl.size ? ' · ' + formatBytes(dl.size) : ''}
            </div>
          ` : ''}
        </div>
      `).join('');
    } catch {
      renderError(container, loadDownloads);
    }
  }

  loadDownloads();
  pollTimer = setInterval(loadDownloads, 5000);
  window.addEventListener('hashchange', () => clearInterval(pollTimer), { once: true });
}

function renderSearchAllTab(container) {
  const today = new Date().toISOString().slice(0, 10);
  container.innerHTML = `<div class="state-loading">${ICON_SPINNER}</div>`;

  api('/requests?status=requested&limit=200').then(data => {
    const eligible = (data.items || []).filter(r => {
      if (!r.release_date) return false;
      if (r.release_date > today) return false;
      if (r.release_date.endsWith('-01-01') && r.release_date.substring(0, 4) >= String(new Date().getFullYear())) return false;
      return true;
    });

    if (!eligible.length) {
      container.innerHTML = `<div class="state-empty">No searchable requests — all items are unreleased or have no release date.</div>`;
      return;
    }

    // Group by book so dual-format requests appear as one card
    const groups = new Map();
    eligible.forEach(r => {
      if (!groups.has(r.book_id)) {
        groups.set(r.book_id, { book_id: r.book_id, title: r.book_title || r.title || '—', author: r.author || '', requests: [] });
      }
      groups.get(r.book_id).requests.push(r);
    });

    container.innerHTML = '';
    const searchQueue = []; // flat list of {r, resultsEl}

    groups.forEach(group => {
      const card = document.createElement('div');
      card.className = 'search-all-card';

      const formatsHtml = group.requests.map(r =>
        `<div class="search-all-format">
          <div class="search-all-format-label">
            <span class="badge badge-${r.status}" title="${r.type}">${typeIcon(r.type)}</span>
          </div>
          <div class="search-all-card-results" data-req-id="${r.id}">${ICON_SPINNER}</div>
        </div>`
      ).join('');

      card.innerHTML = `
        <div class="search-all-card-header">
          <a href="#/library/book?book_id=${escapeHtml(group.book_id)}" class="search-all-card-title">${escapeHtml(group.title)}</a>
          <span class="text-dim" style="font-size:0.85rem;margin-left:0.4rem">${escapeHtml(group.author)}</span>
        </div>
        ${formatsHtml}
      `;
      container.appendChild(card);

      group.requests.forEach(r => {
        searchQueue.push({ r, resultsEl: card.querySelector(`.search-all-card-results[data-req-id="${r.id}"]`) });
      });
    });

    // Search concurrently, max 3 at a time
    let idx = 0;
    async function worker() {
      while (idx < searchQueue.length) {
        const { r, resultsEl } = searchQueue[idx++];
        if (!resultsEl) continue;
        try {
          const data = await api(`/requests/${r.id}/search-indexers`, { method: 'POST' });
          if (data.error) {
            resultsEl.innerHTML = `<div class="text-dim" style="padding:0.5rem 0">${escapeHtml(data.error)}</div>`;
          } else {
            renderProwlarrResults(resultsEl, data.results || [], r.id, null);
          }
        } catch {
          resultsEl.innerHTML = `<div class="text-dim" style="padding:0.5rem 0">Search failed.</div>`;
        }
      }
    }
    Promise.all(Array.from({ length: Math.min(3, searchQueue.length) }, worker));
  }).catch(() => {
    container.innerHTML = `<div class="state-empty">Failed to load requests.</div>`;
  });
}

function renderPendingTab(container) {
  container.innerHTML = `<div class="state-loading">${ICON_SPINNER}</div>`;
  api('/requests/pending').then(data => {
    const groups = data.groups || [];
    if (!groups.length) {
      container.innerHTML = `<div class="state-empty">No pending requests.</div>`;
      return;
    }
    container.innerHTML = '';

    groups.forEach(group => {
      const pendingTypes = new Set(group.requests.map(r => r.type));
      const extraTypes = new Set();

      const card = document.createElement('div');
      card.className = 'pending-card';

      function draw() {
        const requesters = [...new Set(group.requests.map(r => r.requested_by).filter(Boolean))];
        const earliest = group.requests.reduce((a, b) => a.created_at < b.created_at ? a : b).created_at;

        const pills = ['audiobook', 'ebook'].map(t => {
          if (pendingTypes.has(t)) {
            return `<span class="badge badge-pending" title="${t}">${typeIcon(t)}</span>`;
          } else if (extraTypes.has(t)) {
            return `<button class="badge badge-requested fmt-pill" data-add="${t}" title="Remove ${t}">${typeIcon(t)}</button>`;
          } else {
            return `<button class="badge badge-neutral fmt-pill" data-add="${t}" title="Also approve ${t}">${typeIcon(t)}</button>`;
          }
        }).join('');

        card.innerHTML = `
          <div class="pending-card-body">
            <div class="pending-card-title">
              <a href="#/library/book?book_id=${escapeHtml(group.book_id)}">${escapeHtml(group.book_title)}</a>
              <span class="text-dim" style="font-size:0.85rem;margin-left:0.4rem">${escapeHtml(group.author || '')}</span>
            </div>
            <div class="pending-card-row">
              <div class="pending-card-pills">${pills}</div>
              <div class="text-dim" style="font-size:0.8rem;white-space:nowrap">
                ${escapeHtml(requesters.join(', ') || '—')} · ${formatDate(earliest)}
              </div>
            </div>
          </div>
          <div class="pending-card-actions"></div>
        `;

        const actionsEl = card.querySelector('.pending-card-actions');
        actionsEl.innerHTML = `
          <button class="btn-icon btn-icon-approve" title="Approve">${ICON_CHECK}</button>
          <button class="btn-icon btn-icon-reject" title="Reject">${ICON_CROSS}</button>
        `;

        card.querySelectorAll('[data-add]').forEach(btn => {
          btn.onclick = () => {
            const t = btn.dataset.add;
            if (extraTypes.has(t)) extraTypes.delete(t); else extraTypes.add(t);
            draw();
          };
        });

        actionsEl.querySelector('.btn-icon-approve').onclick = async (e) => {
          e.currentTarget.disabled = true;
          actionsEl.querySelector('.btn-icon-reject').disabled = true;
          const types = [...pendingTypes, ...extraTypes];
          try {
            await api(`/requests/book/${group.book_id}/approve`, { method: 'POST', body: { types } });
            card.querySelectorAll('[data-add]').forEach(b => b.disabled = true);
            actionsEl.innerHTML = `<span class="badge badge-requested" style="font-size:0.78rem;padding:0.25rem 0.6rem">Approved</span>`;
            card.classList.add('pending-card--done');
          } catch { toast('Failed to approve.', 'error'); draw(); }
        };

        actionsEl.querySelector('.btn-icon-reject').onclick = async (e) => {
          e.currentTarget.disabled = true;
          actionsEl.querySelector('.btn-icon-approve').disabled = true;
          try {
            await api(`/requests/book/${group.book_id}/reject`, { method: 'POST' });
            card.querySelectorAll('[data-add]').forEach(b => b.disabled = true);
            actionsEl.innerHTML = `<span class="badge badge-failed" style="font-size:0.78rem;padding:0.25rem 0.6rem">Rejected</span>`;
            card.classList.add('pending-card--done');
          } catch { toast('Failed to reject.', 'error'); draw(); }
        };
      }

      draw();
      container.appendChild(card);
    });
  }).catch(() => {
    container.innerHTML = `<div class="state-empty">Failed to load pending requests.</div>`;
  });
}

// /#/downloads redirects to Queue > Downloads tab
route('/downloads', () => {
  history.replaceState(null, '', '#/requests?tab=downloads');
  render();
});

// Dashboard
route('/dashboard', async () => {
  if (!isAdmin()) { navigate('/'); return; }
  renderLoading(app);
  try {
    const [status, syncStatus, settings] = await Promise.all([
      api('/status'),
      api('/sync/status'),
      api('/settings'),
    ]);

    const req = status.requests || {};
    const activeCount = (req.snatched || 0) + (req.downloading || 0) + (req.downloaded || 0) + (req.merging || 0) + (req.organizing || 0);

    app.innerHTML = `<div class="narrow-page">
      <div class="page-header"><span class="page-title">Dashboard</span></div>

      <div class="section-heading">Library</div>
      <div class="stats-row">
        <div class="stat-card clickable" onclick="navigate('/library/books')">
          <div class="stat-value">${status.books || 0}</div>
          <div class="stat-label">Books</div>
        </div>
        <div class="stat-card clickable" onclick="navigate('/library/authors')">
          <div class="stat-value">${status.authors || 0}</div>
          <div class="stat-label">Authors</div>
        </div>
        <div class="stat-card clickable" onclick="navigate('/library/series')">
          <div class="stat-value">${status.series || 0}</div>
          <div class="stat-label">Series</div>
        </div>
      </div>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">${status.audiobooks || 0}</div>
          <div class="stat-label">Audiobooks</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${status.ebooks || 0}</div>
          <div class="stat-label">Ebooks</div>
        </div>
      </div>

      <div class="section-heading">Queue</div>
      <div class="stats-row">
        <div class="stat-card clickable" onclick="navigate('/requests')">
          <div class="stat-value">${req.requested || 0}</div>
          <div class="stat-label">Requested</div>
        </div>
        <div class="stat-card clickable" onclick="navigate('/requests?tab=downloads')">
          <div class="stat-value${activeCount ? ' text-accent' : ''}">${activeCount}</div>
          <div class="stat-label">Downloading</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${req.completed || 0}</div>
          <div class="stat-label">Completed</div>
        </div>
        <div class="stat-card">
          <div class="stat-value${req.failed ? ' text-red' : ''}">${req.failed || 0}</div>
          <div class="stat-label">Failed</div>
        </div>
      </div>

      <div id="dash-active-downloads"></div>

      <div class="section-heading">Hardcover Links</div>
      <div class="stats-row">
        <div class="stat-card${status.unlinked_books ? ' clickable' : ''}" ${status.unlinked_books ? `onclick="navigate('/library/books', {unlinked:'1'})"` : ''}>
          <div class="stat-value${status.unlinked_books ? '' : ' text-green'}">${status.unlinked_books || 0}</div>
          <div class="stat-label">Books unlinked</div>
        </div>
        <div class="stat-card${status.unlinked_authors ? ' clickable' : ''}" ${status.unlinked_authors ? `onclick="navigate('/library/authors', {unlinked:'1'})"` : ''}>
          <div class="stat-value${status.unlinked_authors ? '' : ' text-green'}">${status.unlinked_authors || 0}</div>
          <div class="stat-label">Authors unlinked</div>
        </div>
        <div class="stat-card${status.unlinked_series ? ' clickable' : ''}" ${status.unlinked_series ? `onclick="navigate('/library/series', {unlinked:'1'})"` : ''}>
          <div class="stat-value${status.unlinked_series ? '' : ' text-green'}">${status.unlinked_series || 0}</div>
          <div class="stat-label">Series unlinked</div>
        </div>
      </div>

      <div class="section-heading">Scheduled Tasks</div>
      <div class="tasks-list" id="dash-tasks"></div>

      ${(settings.general || {}).debug_view ? `
      <div class="section-heading mt-2">Status Pill Legend</div>
      <div class="card" style="padding:0.75rem 1rem;display:flex;flex-direction:column;gap:0.6rem">
        ${[
          ['Request states', [['pending','Pending'],['requested','Requested'],['snatched','Snatched'],['downloading','Downloading'],['downloaded','Downloaded'],['merging','Merging'],['organizing','Organizing'],['completed','Completed'],['in_library','In Library'],['failed','Failed']]],
          ['Misc',           [['upcoming','Upcoming'],['missing','Missing'],['sso','SSO'],['neutral','Neutral']]],
        ].map(([heading, pills]) => `
          <div>
            <div style="font-size:0.72rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.35rem">${heading}</div>
            <div style="display:flex;flex-wrap:wrap;gap:0.4rem">${pills.map(([cls, label]) => `<span class="badge badge-${cls}">${label}</span>`).join('')}</div>
          </div>`).join('')}
      </div>` : ''}
    </div>`;

    const DASH_TASKS = [
      { key: 'library_sync',  label: 'Library sync',  endpoint: '/sync/library'       },
      { key: 'cache_refresh', label: 'Cache refresh', endpoint: '/sync/cache-refresh' },
      { key: 'auto_search',   label: 'Auto search',   endpoint: null                  },
    ];

    function _taskResultHtml(result, running) {
      if (!result) return '';
      if (running) return escapeHtml(result);
      if (result.startsWith('error:')) return `<span class="text-red">${escapeHtml(result)}</span>`;
      if (result === 'ok') return '<span class="text-green">ok</span>';
      return escapeHtml(result) + '\n<span class="text-green">done</span>';
    }

    function renderDashTask(key, label, endpoint, t) {
      const disabled = !t.next_run && !t.running;
      return `
        <div class="stat-card${disabled ? ' stat-card-disabled' : ''}" id="dash-task-${key}">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem">
            <div style="font-size:0.9rem;font-weight:600">${label}</div>
            ${endpoint ? `<button class="btn btn-ghost btn-sm dash-run-btn" data-endpoint="${endpoint}" data-key="${key}" style="font-size:0.78rem;padding:0.15rem 0.5rem;white-space:nowrap">${ICON_PLAY} Run</button>` : ''}
          </div>
          <div class="text-dim mt-1" style="font-size:0.78rem" id="dash-task-status-${key}">
            ${disabled ? 'Disabled' : t.running ? `${ICON_SPINNER} running` : t.last_run ? `Last: ${formatDate(t.last_run)}` : 'Never run'}
          </div>
          ${!disabled && (t.last_result || t.running) ? `<div class="${t.running ? 'text-dim' : ''}" style="font-size:0.78rem;margin-top:0.2rem;white-space:pre-line" id="dash-task-result-${key}">${_taskResultHtml(t.last_result || '', t.running)}</div>` : `<div id="dash-task-result-${key}"></div>`}
        </div>
      `;
    }

    function updateDashTasks(s) {
      DASH_TASKS.forEach(({ key, label, endpoint }) => {
        const t = s[key] || {};
        const card = document.getElementById(`dash-task-${key}`);
        if (!card) return;
        const statusEl = document.getElementById(`dash-task-status-${key}`);
        const resultEl = document.getElementById(`dash-task-result-${key}`);
        const disabled = !t.next_run && !t.running;
        if (statusEl) statusEl.innerHTML = disabled ? 'Disabled' : t.running ? `${ICON_SPINNER} running` : t.last_run ? `Last: ${formatDate(t.last_run)}` : 'Never run';
        if (resultEl) {
          resultEl.className = t.running ? 'text-dim' : '';
          resultEl.style.fontSize = '0.78rem';
          resultEl.style.marginTop = '0.2rem';
          resultEl.style.whiteSpace = 'pre-line';
          resultEl.innerHTML = (!disabled && t.last_result) ? _taskResultHtml(t.last_result, t.running) : '';
        }
      });
    }

    const tasksEl = document.getElementById('dash-tasks');
    if (tasksEl) {
      tasksEl.innerHTML = DASH_TASKS.map(({ key, label, endpoint }) =>
        renderDashTask(key, label, endpoint, syncStatus[key] || {})
      ).join('');

      tasksEl.querySelectorAll('.dash-run-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          btn.disabled = true;
          const key = btn.dataset.key;
          try {
            await api(btn.dataset.endpoint, { method: 'POST' });
            toast(`${DASH_TASKS.find(t => t.key === key)?.label} started`, 'info');
            const poll = setInterval(async () => {
              if (!document.getElementById(`dash-task-${key}`)) { clearInterval(poll); return; }
              const s = await api('/sync/status');
              updateDashTasks(s);
              if (!s[key]?.running) clearInterval(poll);
            }, 2000);
          } catch (err) {
            toast('Failed: ' + err.message, 'error');
          } finally {
            btn.disabled = false;
          }
        });
      });
    }
    // Active downloads section — polls every 5s while on page
    const dlSection = document.getElementById('dash-active-downloads');
    let dlPollTimer;
    async function loadDashDownloads() {
      if (!document.getElementById('dash-active-downloads')) { clearInterval(dlPollTimer); return; }
      try {
        const data = await api('/downloads');
        const items = (data.items || []).filter(d => d.progress != null || d.status === 'snatched' || d.status === 'downloading');
        if (!items.length) { dlSection.innerHTML = ''; return; }
        dlSection.innerHTML = `<div class="section-heading">Active Downloads</div>` +
          items.map(dl => `
            <div class="card mb-1">
              <div style="display:flex;justify-content:space-between;gap:0.5rem;align-items:flex-start">
                <div>
                  <div style="font-weight:500">${escapeHtml(dl.book_title || '—')}</div>
                  <div class="text-dim" style="font-size:0.8rem">${escapeHtml(dl.author || '')}${dl.author && dl.type ? ' · ' : ''}${dl.type ? typeIcon(dl.type) : ''}</div>
                </div>
                <span class="badge badge-${dl.status || 'downloading'}" style="flex-shrink:0">${dl.status || 'downloading'}</span>
              </div>
              ${dl.progress != null ? `
                <div class="progress-bar-track mt-1">
                  <div class="progress-bar-fill" style="width:${Math.round(dl.progress)}%"></div>
                </div>
                <div class="text-dim mt-1" style="font-size:0.78rem">
                  ${Math.round(dl.progress)}%${formatEta(dl.eta) != null ? ' · ETA ' + formatEta(dl.eta) : ''}${dl.speed ? ' · ' + formatBytes(dl.speed) + '/s' : ''}${dl.size ? ' · ' + formatBytes(dl.size) : ''}
                </div>` : ''}
            </div>`).join('');
      } catch { dlSection.innerHTML = ''; }
    }
    loadDashDownloads();
    dlPollTimer = setInterval(loadDashDownloads, 5000);
    window.addEventListener('hashchange', () => clearInterval(dlPollTimer), { once: true });

  } catch (err) {
    renderError(app, render);
  }
});

// Profile
route('/profile', async () => {
  if (!_authUser) { navigate('/'); return; }
  app.innerHTML = `<div class="narrow-page" style="max-width:400px">
    <div class="page-header"><span class="page-title">${ICON_AUTHOR} Profile</span></div>
    <div class="card">
      <div style="display:flex;flex-direction:column;gap:0.75rem">
        <div class="detail-fmt-kv"><span class="td-dim">Username</span><span>${escapeHtml(_authUser.username)}</span></div>
        ${_authUser.email ? `<div class="detail-fmt-kv"><span class="td-dim">Email</span><span>${escapeHtml(_authUser.email)}</span></div>` : ''}
        <div class="detail-fmt-kv"><span class="td-dim">Role</span><span>${escapeHtml(_authUser.role)}</span></div>
      </div>
    </div>
    <div style="margin-top:1rem">
      <button class="btn btn-secondary" id="profile-logout-btn">Sign out</button>
    </div>
  </div>`;
  document.getElementById('profile-logout-btn').addEventListener('click', async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    _authUser = null;
    updateNavForRole();
    navigate('/login');
  });
});

// Settings
route('/settings', async (params, qp) => {
  if (!isAdmin()) { navigate('/'); return; }
  renderLoading(app);
  try {
    const settings = await api('/settings');

    const tabs = ['General', 'ABS', 'Prowlarr', 'qBittorrent', 'SABnzbd', 'Hardcover', 'Notifications', 'Tasks', 'Auth'];
    const initialTab = tabs.includes(qp.tab) ? qp.tab : tabs[0];

    app.innerHTML = `<div class="narrow-page">
      <div class="page-header"><span class="page-title">${ICON_SETTINGS} Settings</span></div>
      <div class="tabs-wrap">
        <div class="tabs">
          ${tabs.map(t => `<button class="tab-btn${t === initialTab ? ' active' : ''}" data-tab="${t}">${t}</button>`).join('')}
        </div>
      </div>
      <div id="settings-content"></div>
    </div>`;

    const content = document.getElementById('settings-content');
    setupTabScrollHints(app.querySelector('.tabs-wrap'));

    function renderFeedback(el, ok, msg) {
      el.className = 'form-feedback ' + (ok ? 'ok' : 'err');
      el.textContent = ok ? '✓ ' + msg : '✗ ' + msg;
    }

    function buildTabContent(tabName) {
      switch (tabName) {
        case 'General': return buildGeneralTab(settings);
        case 'ABS': return buildAbsTab(settings);
        case 'Prowlarr': return buildProwlarrTab(settings);
        case 'qBittorrent': return buildQbtTab(settings);
        case 'SABnzbd': return buildSabnzbdTab(settings);
        case 'Hardcover': return buildHardcoverTab(settings);
        case 'Notifications': return buildNotificationsTab(settings);
        case 'Tasks': return buildTasksTab(settings);
        case 'Auth': return buildAuthTab(settings);
        default: return '<div class="text-dim">Coming soon.</div>';
      }
    }

    function showTab(name, updateHash = true) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
      content.innerHTML = buildTabContent(name);
      wireTabEvents(name);
      if (updateHash) {
        const hp = name !== tabs[0] ? { tab: name } : {};
        history.replaceState(null, '', buildHash('/settings', hp));
      }
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.onclick = () => showTab(btn.dataset.tab);
    });

    showTab(initialTab, false);

    function field(label, key, value, type = 'text', hint = '') {
      const masked = type === 'password' ? 'password' : 'text';
      return `
        <div class="form-group">
          <label class="form-label">${escapeHtml(label)}</label>
          <input type="${masked}" class="form-input" data-key="${key}" value="${escapeHtml(value || '')}">
          ${hint ? `<div class="form-hint">${hint}</div>` : ''}
        </div>
      `;
    }

    function checkbox(label, key, checked, hint = '') {
      return `
        <div class="form-group">
          <label style="display:flex;align-items:center;gap:0.5rem;cursor:pointer">
            <input type="checkbox" data-key="${key}" ${checked ? 'checked' : ''}>
            <span>${escapeHtml(label)}</span>
          </label>
          ${hint ? `<div class="form-hint">${hint}</div>` : ''}
        </div>
      `;
    }

    function saveButton(section) {
      return `
        <div class="form-actions">
          <button class="btn btn-primary" data-save="${section}">Save</button>
          <span class="form-feedback" id="feedback-${section}"></span>
        </div>
      `;
    }

    function testButton(service) {
      return `<button class="btn btn-secondary" data-test="${service}">Test Connection</button>`;
    }

    function buildGeneralTab(s) {
      const g = s.general || {};
      const sepDirs = !!g.separate_type_dirs;
      return `
        ${field('Output directory', 'output_dir', g.output_dir)}
        ${checkbox('Separate directories by type (audiobooks/ebooks)', 'separate_type_dirs', sepDirs)}
        <div id="prefix-fields" style="${sepDirs ? '' : 'display:none'}">
          ${field('Audiobook directory prefix', 'audiobook_prefix', g.audiobook_prefix)}
          ${field('Ebook directory prefix', 'ebook_prefix', g.ebook_prefix)}
        </div>
        ${field('Public URL', 'public_url', g.public_url || '', 'text', 'Externally reachable URL for this app, e.g. https://athenaeum.example.com — required for OIDC')}
        ${checkbox('Group series in search results', 'group_series_in_search', g.group_series_in_search)}
        ${checkbox('Merge multi-file audiobooks into single M4B', 'merge_multifile_audiobooks', g.merge_multifile_audiobooks)}
        ${checkbox('Debug view', 'debug_view', g.debug_view)}
        ${saveButton('general')}
      `;
    }

    function buildAbsTab(s) {
      const a = s.audiobookshelf || {};
      const savedIds = Array.isArray(a.library_id) ? a.library_id : [];
      return `
        ${field('ABS URL', 'url', a.url, 'text', 'e.g. http://192.168.1.10:13378 — used for browser links')}
        ${field('Internal ABS URL', 'internal_url', a.internal_url || '', 'text', 'Optional — Docker internal URL e.g. http://abs:13378')}
        ${field('API Key', 'api_key', a.api_key, 'password')}
        <div class="form-group">
          <label class="form-label">Libraries</label>
          <div id="abs-library-list" data-saved-ids="${escapeHtml(JSON.stringify(savedIds))}" style="margin-top:0.25rem">
            ${savedIds.length
              ? `<div class="text-dim" style="font-size:0.85rem">${savedIds.length} library ID${savedIds.length !== 1 ? 's' : ''} saved — click Test Connection to reload.</div>`
              : `<div class="text-dim" style="font-size:0.85rem">Click Test Connection to load available libraries.</div>`
            }
          </div>
        </div>
        <div class="form-actions">
          ${testButton('abs')}
          <button class="btn btn-primary" data-save="audiobookshelf">Save</button>
          <span class="form-feedback" id="feedback-audiobookshelf"></span>
        </div>
        <div id="test-abs-result" class="mt-1"></div>
      `;
    }

    function buildProwlarrTab(s) {
      const p = s.prowlarr || {};
      return `
        ${field('URL', 'url', p.url)}
        ${field('API Key', 'api_key', p.api_key, 'password')}
        ${field('Indexer tag filter', 'tag', p.tag || '', 'text', 'e.g. books — only search indexers with this tag')}
        <div class="form-actions">
          ${testButton('prowlarr')}
          <button class="btn btn-primary" data-save="prowlarr">Save</button>
          <span class="form-feedback" id="feedback-prowlarr"></span>
        </div>
        <div id="test-prowlarr-result" class="mt-1"></div>
      `;
    }

    function buildQbtTab(s) {
      const q = s.qbittorrent || {};
      return `
        ${field('URL', 'url', q.url)}
        ${field('Username', 'username', q.username)}
        ${field('Password', 'password', q.password, 'password')}
        ${field('Download directory', 'download_dir', q.download_dir)}
        <div class="form-actions">
          ${testButton('qbittorrent')}
          <button class="btn btn-primary" data-save="qbittorrent">Save</button>
          <span class="form-feedback" id="feedback-qbittorrent"></span>
        </div>
        <div id="test-qbittorrent-result" class="mt-1"></div>
      `;
    }

    function buildSabnzbdTab(s) {
      const sb = s.sabnzbd || {};
      return `
        ${field('URL', 'url', sb.url)}
        ${field('API Key', 'api_key', sb.api_key, 'password')}
        <div class="form-actions">
          ${testButton('sabnzbd')}
          <button class="btn btn-primary" data-save="sabnzbd">Save</button>
          <span class="form-feedback" id="feedback-sabnzbd"></span>
        </div>
        <div id="test-sabnzbd-result" class="mt-1"></div>
      `;
    }

    function buildHardcoverTab(s) {
      const h = s.hardcover || {};
      return `
        ${field('API Key', 'api_key', h.api_key, 'password')}
        ${field('Preferred language', 'preferred_language', h.preferred_language)}
        <div class="form-actions">
          ${testButton('hardcover')}
          <button class="btn btn-primary" data-save="hardcover">Save</button>
          <span class="form-feedback" id="feedback-hardcover"></span>
        </div>
        <div id="test-hardcover-result" class="mt-1"></div>
      `;
    }

    function buildNotificationsTab(s) {
      const n = s.notifications || {};
      return `
        <div class="form-group">
          <label class="form-label">Notification URLs</label>
          <textarea class="form-input" data-key="urls" rows="5"
            placeholder="One Apprise URL per line&#10;e.g. pover://token/userkey&#10;e.g. mailto://user:pass@smtp.example.com"
            style="font-family:var(--font-mono,monospace);font-size:0.82rem;resize:vertical"
          >${escapeHtml(n.urls || '')}</textarea>
          <div class="text-dim" style="font-size:0.78rem;margin-top:0.3rem">
            Supports 60+ services via <a href="https://github.com/caronc/apprise/wiki" target="_blank" rel="noopener" style="color:var(--accent)">Apprise URL syntax</a>.
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Batch window (seconds)</label>
          <input type="number" class="form-input" data-key="batch_window"
            value="${escapeHtml(String(n.batch_window ?? 60))}"
            min="10" max="3600" style="width:120px">
          <div class="text-dim" style="font-size:0.78rem;margin-top:0.3rem">
            Notifications within this window are grouped into a single message.
          </div>
        </div>
        ${saveButton('notifications')}
        <button class="btn btn-ghost btn-sm" id="test-notifications-btn" style="margin-top:0.5rem">Send test notification</button>
        <span id="test-notifications-result" class="text-dim" style="font-size:0.82rem;margin-left:0.5rem"></span>
      `;
    }

    const TASK_DEFS = [
      { key: 'library_sync',  label: 'Library sync',  default: '0 2 * * *',    endpoint: '/sync/library' },
      { key: 'cache_refresh', label: 'Cache refresh', default: '0 3 * * *',    endpoint: '/sync/cache-refresh' },
      { key: 'auto_search',   label: 'Auto search',   default: '0 */6 * * *',  endpoint: null },
    ];

    function buildTasksTab(s) {
      const sch = s.schedule || {};
      const taskRows = TASK_DEFS.map(t => `
        <div class="task-row">
          <div class="task-cell-name">
            <div class="task-cell-name-top">
              <span style="font-weight:500">${t.label}</span>
              ${t.endpoint
                ? `<button class="btn btn-ghost btn-sm" data-run="${t.endpoint}" title="Run now" style="font-size:0.78rem;padding:0.15rem 0.4rem;white-space:nowrap">${ICON_PLAY} Run</button>`
                : ''
              }
            </div>
            <div class="text-dim" style="font-size:0.75rem">default: ${t.default}</div>
          </div>
          <input type="text" class="form-input task-cell-cron" data-key="${t.key}"
            value="${escapeHtml(sch[t.key] || '')}"
            style="font-family:var(--font-mono,monospace);font-size:0.85rem">
          <div id="task-next-${t.key}" class="task-cell-next text-dim" style="font-size:0.82rem;padding-top:0.45rem">${sch[t.key] ? 'Next: —' : 'Disabled'}</div>
          <div id="task-last-${t.key}" class="task-cell-last text-dim" style="font-size:0.82rem;padding-top:0.45rem">Last: —</div>
        </div>
      `).join('');

      return `
        <div class="tasks-grid">
          <div class="tasks-header-row">
            <div class="form-label">Task</div>
            <div class="form-label">Schedule</div>
            <div class="form-label">Next run</div>
            <div class="form-label">Last run</div>
          </div>
          ${taskRows}
        </div>
        <div class="form-actions" style="margin-top:1rem">
          <button class="btn btn-primary" data-save="schedule">Save</button>
          <span class="form-feedback" id="feedback-schedule"></span>
        </div>
      `;
    }

    function buildAuthTab(s) {
      const a = s.auth || {};
      const publicUrl = (s.general || {}).public_url || '';
      const redirectUri = publicUrl ? `${publicUrl}/api/auth/oidc/callback` : '(set General → Public URL first)';
      return `
        <div class="section-heading">Users</div>
        <div id="auth-users-list"><span class="text-dim">${ICON_SPINNER} Loading…</span></div>
        <div style="margin-top:1rem">
          <div class="section-heading">Add user</div>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:flex-end">
            <div class="form-group" style="margin-bottom:0;flex:1;min-width:140px">
              <label class="form-label">Username</label>
              <input class="form-input" id="new-user-username" type="text">
            </div>
            <div class="form-group" style="margin-bottom:0;flex:1;min-width:160px">
              <label class="form-label">Email <span class="text-dim">(optional)</span></label>
              <input class="form-input" id="new-user-email" type="email">
            </div>
            <div class="form-group" style="margin-bottom:0;flex:1;min-width:140px">
              <label class="form-label">Temp password</label>
              <input class="form-input" id="new-user-password" type="password">
            </div>
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">Role</label>
              <select class="form-input" id="new-user-role">
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button class="btn btn-primary" id="add-user-btn">Add user</button>
          </div>
          <span class="form-feedback" id="add-user-feedback"></span>
        </div>

        ${_authUser && _authUser.role === 'admin' ? `
        <div class="section-heading" style="margin-top:1.5rem">Account</div>
        <div style="display:flex;gap:0.5rem;align-items:center">
          <span class="text-dim">Signed in as <strong>${escapeHtml(_authUser.username)}</strong></span>
          <button class="btn btn-secondary btn-sm" id="logout-btn">Sign out</button>
        </div>
        ` : ''}

        <div class="section-heading" style="margin-top:1.5rem">Login methods</div>
        ${checkbox('Enable form login (username + password)', 'form_enabled', a.form_enabled)}
        ${checkbox('Enable OIDC / SSO login', 'oidc_enabled', a.oidc_enabled, 'When enabled, the login page redirects to your OIDC provider. Add ?force_local to the login URL to bypass and use form login.')}

        <div id="oidc-settings-block" style="${a.oidc_enabled ? '' : 'display:none'}">
          <div class="section-heading" style="margin-top:1.5rem">OIDC settings</div>
          <div class="form-group">
            <label class="form-label">Provider URL</label>
            <div style="display:flex;gap:0.5rem;align-items:center">
              <input type="text" class="form-input" data-key="oidc_provider_url" value="${escapeHtml(a.oidc_provider_url || '')}" style="flex:1" placeholder="e.g. https://sso.example.com/application/o/athenaeum">
              <button class="btn btn-secondary" id="oidc-verify-btn" type="button">Verify</button>
            </div>
            <div class="form-hint">Issuer URL — Athenaeum auto-discovers all endpoints from here</div>
            <div id="oidc-verify-result" style="margin-top:0.4rem;font-size:0.85rem"></div>
          </div>
          ${field('Client ID', 'oidc_client_id', a.oidc_client_id || '')}
          ${field('Client Secret', 'oidc_client_secret', a.oidc_client_secret || '', 'password')}
          ${field('Scopes', 'oidc_scopes', a.oidc_scopes || 'openid email profile')}
          ${field('Session duration (days)', 'session_days', String(a.session_days || 30))}
          <div class="form-group">
            <label class="form-label">Redirect URI <span class="text-dim">(register this with your provider)</span></label>
            <input class="form-input" type="text" value="${escapeHtml(redirectUri)}" readonly onclick="this.select()" style="font-family:var(--font-mono,monospace);font-size:0.85rem;cursor:pointer">
          </div>
        </div>
        ${saveButton('auth')}
      `;
    }

    async function loadSyncStatus() {
      let s;
      try {
        s = await api('/sync/status');
        for (const [task, t] of Object.entries(s)) {
          const nextEl = document.getElementById(`task-next-${task}`);
          const lastEl = document.getElementById(`task-last-${task}`);
          if (nextEl) {
            const cronInput = content.querySelector(`[data-key="${task}"]`);
            const hasSchedule = cronInput && cronInput.value.trim();
            nextEl.textContent = t.next_run ? 'Next: ' + formatDateTime(t.next_run) : (hasSchedule ? '—' : 'Disabled');
          }
          if (lastEl) {
            if (t.running) {
              lastEl.className = 'text-dim';
              lastEl.innerHTML = `${ICON_SPINNER} running`;
            } else if (t.last_run) {
              const resultHtml = t.last_result
                ? ` <span class="${t.last_result === 'ok' ? 'text-green' : 'text-red'}">${escapeHtml(t.last_result)}</span>`
                : '';
              lastEl.className = 'text-dim';
              lastEl.style.fontSize = '0.82rem';
              lastEl.style.paddingTop = '0.45rem';
              lastEl.innerHTML = 'Last: ' + formatDateTime(t.last_run) + resultHtml;
            } else {
              lastEl.textContent = 'Last: Never';
            }
          }
        }
      } catch { /* ignore */ }
      return s;
    }

    function wireTabEvents(tabName) {
      // Save buttons
      content.querySelectorAll('[data-save]').forEach(btn => {
        btn.onclick = async () => {
          const section = btn.dataset.save;
          const feedback = document.getElementById(`feedback-${section}`);
          const inputs = content.querySelectorAll('[data-key]');
          const partial = {};
          inputs.forEach(inp => {
            const key = inp.dataset.key;
            const val = inp.type === 'checkbox' ? inp.checked : inp.value;
            if (val === '********') return;
            partial[key] = val;
          });
          // ABS library selection via checkboxes
          if (section === 'audiobookshelf') {
            const checks = content.querySelectorAll('.abs-lib-check');
            if (checks.length > 0) {
              partial.library_id = Array.from(checks).filter(c => c.checked).map(c => c.value);
            }
          }
          btn.disabled = true;
          try {
            await api('/settings', { method: 'PUT', body: { [section]: partial } });
            renderFeedback(feedback, true, 'Saved');
            checkAbsBanner();
          } catch (err) {
            renderFeedback(feedback, false, err.message);
          } finally {
            btn.disabled = false;
          }
        };
      });

      // Test buttons
      content.querySelectorAll('[data-test]').forEach(btn => {
        btn.onclick = async () => {
          const svc = btn.dataset.test;
          const resultEl = document.getElementById(`test-${svc}-result`);
          btn.disabled = true;
          btn.textContent = 'Testing…';
          // Collect current (unsaved) form values, including sentinels so the
          // backend knows to fall back to the saved value for masked fields.
          const formData = {};
          content.querySelectorAll('[data-key]').forEach(inp => {
            formData[inp.dataset.key] = inp.type === 'checkbox' ? inp.checked : inp.value;
          });
          try {
            const r = await api(`/settings/test/${svc}`, { method: 'POST', body: formData });
            if (svc === 'abs') {
              const libs = r.libraries || [];
              const listEl = document.getElementById('abs-library-list');
              const savedIds = listEl ? JSON.parse(listEl.dataset.savedIds || '[]') : [];
              if (listEl) {
                if (libs.length) {
                  listEl.innerHTML = libs.map(l => `
                    <label style="display:flex;align-items:center;gap:0.5rem;margin-top:0.35rem;cursor:pointer">
                      <input type="checkbox" class="abs-lib-check" value="${escapeHtml(l.id)}"
                        ${savedIds.includes(l.id) ? 'checked' : ''}>
                      <span>${escapeHtml(l.name)}</span>
                      <span class="text-dim" style="font-size:0.78rem">${escapeHtml(l.id)}</span>
                    </label>`).join('');
                } else {
                  listEl.innerHTML = '<div class="text-dim" style="font-size:0.85rem">No libraries found.</div>';
                }
              }
              if (resultEl) resultEl.innerHTML = `<div class="text-green" style="font-size:0.85rem">&#10003; Connected — ${libs.length} librar${libs.length !== 1 ? 'ies' : 'y'} found</div>`;
            } else if (resultEl) {
              resultEl.innerHTML = `<div class="text-green" style="font-size:0.85rem">&#10003; Connected: ${escapeHtml(JSON.stringify(r))}</div>`;
            }
          } catch (err) {
            if (resultEl) {
              resultEl.innerHTML = `<div class="text-red" style="font-size:0.85rem">✗ ${escapeHtml(err.message)}</div>`;
            }
          } finally {
            btn.disabled = false;
            btn.textContent = 'Test Connection';
          }
        };
      });

      // Notifications test button
      const testNotifBtn = document.getElementById('test-notifications-btn');
      if (testNotifBtn) {
        testNotifBtn.onclick = async () => {
          const resultEl = document.getElementById('test-notifications-result');
          testNotifBtn.disabled = true;
          testNotifBtn.textContent = 'Sending…';
          const urlsEl = content.querySelector('[data-key="urls"]');
          const urls = urlsEl ? urlsEl.value : '';
          try {
            await api('/settings/test/notifications', { method: 'POST', body: { urls } });
            if (resultEl) resultEl.textContent = 'Test sent successfully';
          } catch (err) {
            if (resultEl) resultEl.textContent = err.message;
          } finally {
            testNotifBtn.disabled = false;
            testNotifBtn.textContent = 'Send test notification';
          }
        };
      }

      // Auth tab
      if (tabName === 'Auth') {
        // Load users list
        const loadUsers = async () => {
          const listEl = document.getElementById('auth-users-list');
          if (!listEl) return;
          try {
            const data = await api('/users');
            const users = data.users || [];
            if (!users.length) { listEl.innerHTML = '<div class="text-dim">No users yet.</div>'; return; }
            listEl.innerHTML = `<div class="user-cards">${users.map(u => `
              <div class="card user-card">
                <div class="user-card-name">${escapeHtml(u.username)}${u.force_password_change ? ' <span class="badge badge-warn">PW change</span>' : ''}${u.oidc_linked ? ' <span class="badge badge-sso">SSO</span>' : ''}</div>
                <div class="form-group" style="margin-bottom:0.5rem">
                  <label class="form-label">Email</label>
                  <input type="email" class="form-input" data-user-email="${u.id}" value="${escapeHtml(u.email || '')}" placeholder="—">
                </div>
                <div class="form-group" style="margin-bottom:0.75rem">
                  <label class="form-label">Role</label>
                  <select class="form-input" data-user-role="${u.id}">
                    <option value="user" ${u.role === 'user' ? 'selected' : ''}>user</option>
                    <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>admin</option>
                  </select>
                </div>
                <div style="display:flex;gap:0.5rem">
                  <button class="btn btn-sm btn-secondary" data-reset-pw="${u.id}">Reset PW</button>
                  <button class="btn btn-sm btn-danger" data-delete-user="${u.id}">Delete</button>
                </div>
              </div>`).join('')}
            </div>`;

            listEl.querySelectorAll('[data-user-email]').forEach(input => {
              const save = async () => {
                try {
                  await api(`/users/${input.dataset.userEmail}`, { method: 'PATCH', body: { email: input.value.trim() } });
                  toast('Email updated.');
                } catch { toast('Failed to update email.', 'error'); }
              };
              input.addEventListener('blur', save);
              input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); input.blur(); } });
            });
            listEl.querySelectorAll('[data-user-role]').forEach(sel => {
              sel.addEventListener('change', async () => {
                try {
                  await api(`/users/${sel.dataset.userRole}`, { method: 'PATCH', body: { role: sel.value } });
                  toast('Role updated.');
                } catch { toast('Failed to update role.', 'error'); }
              });
            });
            listEl.querySelectorAll('[data-reset-pw]').forEach(btn => {
              btn.addEventListener('click', async () => {
                const pw = prompt('New temporary password:');
                if (!pw) return;
                try {
                  await api(`/users/${btn.dataset.resetPw}/reset-password`, { method: 'POST', body: { new_password: pw } });
                  toast('Password reset.');
                  loadUsers();
                } catch { toast('Failed.', 'error'); }
              });
            });
            listEl.querySelectorAll('[data-delete-user]').forEach(btn => {
              btn.addEventListener('click', async () => {
                if (!confirm('Delete this user?')) return;
                try {
                  await api(`/users/${btn.dataset.deleteUser}`, { method: 'DELETE' });
                  toast('User deleted.');
                  loadUsers();
                } catch { toast('Failed.', 'error'); }
              });
            });
          } catch { listEl.innerHTML = '<div class="text-dim">Failed to load users.</div>'; }
        };
        loadUsers();

        document.getElementById('add-user-btn')?.addEventListener('click', async () => {
          const username = document.getElementById('new-user-username').value.trim();
          const email = document.getElementById('new-user-email').value.trim();
          const password = document.getElementById('new-user-password').value;
          const role = document.getElementById('new-user-role').value;
          const fb = document.getElementById('add-user-feedback');
          if (!username || !password) { fb.textContent = 'Username and password required.'; return; }
          try {
            await api('/users', { method: 'POST', body: { username, email: email || undefined, password, role } });
            toast('User created.');
            document.getElementById('new-user-username').value = '';
            document.getElementById('new-user-email').value = '';
            document.getElementById('new-user-password').value = '';
            fb.textContent = '';
            loadUsers();
          } catch (err) { fb.textContent = err.message; }
        });

        document.getElementById('logout-btn')?.addEventListener('click', async () => {
          await fetch('/api/auth/logout', { method: 'POST' });
          _authUser = null;
          navigate('/login');
        });

        content.querySelector('[data-key="oidc_enabled"]')?.addEventListener('change', function() {
          const block = document.getElementById('oidc-settings-block');
          if (block) block.style.display = this.checked ? '' : 'none';
        });

        document.getElementById('oidc-verify-btn')?.addEventListener('click', async () => {
          const btn = document.getElementById('oidc-verify-btn');
          const resultEl = document.getElementById('oidc-verify-result');
          const url = content.querySelector('[data-key="oidc_provider_url"]')?.value?.trim();
          if (!url) { resultEl.style.color = 'var(--color-error)'; resultEl.textContent = 'Enter a Provider URL first.'; return; }
          btn.disabled = true;
          btn.textContent = 'Verifying…';
          resultEl.textContent = '';
          try {
            const data = await api('/auth/oidc/verify', { method: 'POST', body: { provider_url: url } });
            resultEl.style.color = 'var(--color-success, green)';
            resultEl.textContent = `Provider reachable — issuer: ${data.issuer}`;
          } catch (err) {
            resultEl.style.color = 'var(--color-error)';
            resultEl.textContent = err.message || 'Could not reach provider.';
          } finally {
            btn.disabled = false;
            btn.textContent = 'Verify';
          }
        });

        // Validate: form_enabled requires at least one admin user before saving
        const authSaveBtn = content.querySelector('[data-save="auth"]');
        if (authSaveBtn) {
          const origClick = authSaveBtn.onclick;
          authSaveBtn.onclick = async (e) => {
            const formEnabled = content.querySelector('[data-key="form_enabled"]')?.checked;
            if (formEnabled) {
              try {
                const data = await api('/users');
                const admins = (data.users || []).filter(u => u.role === 'admin');
                if (!admins.length) {
                  toast('Create an admin user before enabling form login.', 'error');
                  return;
                }
              } catch {}
            }
            if (origClick) origClick.call(authSaveBtn, e);
            else authSaveBtn.dispatchEvent(new MouseEvent('click', { bubbles: false }));
          };
        }
      }

      // General tab: toggle prefix fields based on separate_type_dirs checkbox
      if (tabName === 'General') {
        const sepCheck = content.querySelector('[data-key="separate_type_dirs"]');
        const prefixFields = document.getElementById('prefix-fields');
        if (sepCheck && prefixFields) {
          sepCheck.addEventListener('change', () => {
            prefixFields.style.display = sepCheck.checked ? '' : 'none';
          });
        }
      }

      // Tasks tab specific
      if (tabName === 'Tasks') {
        loadSyncStatus();

        // Live next-run preview as cron expression changes
        TASK_DEFS.forEach(t => {
          const input = content.querySelector(`[data-key="${t.key}"]`);
          const nextEl = document.getElementById(`task-next-${t.key}`);
          if (!input || !nextEl) return;
          let debounce;
          input.addEventListener('input', () => {
            clearTimeout(debounce);
            const expr = input.value.trim();
            if (!expr) { nextEl.className = 'task-cell-next text-dim'; nextEl.style.fontSize = '0.82rem'; nextEl.style.paddingTop = '0.45rem'; nextEl.textContent = 'Disabled'; return; }
            debounce = setTimeout(async () => {
              try {
                const r = await api(`/schedule/next-run?expr=${encodeURIComponent(expr)}`);
                nextEl.className = 'text-dim';
                nextEl.style.fontSize = '0.82rem';
                nextEl.style.paddingTop = '0.45rem';
                nextEl.textContent = 'Next: ' + (r.next_run ? formatDateTime(r.next_run) : '—');
              } catch {
                nextEl.className = 'text-red';
                nextEl.textContent = 'invalid';
              }
            }, 400);
          });
        });

        content.querySelectorAll('[data-run]').forEach(btn => {
          btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
              await api(btn.dataset.run, { method: 'POST' });
              const label = TASK_DEFS.find(t => t.endpoint === btn.dataset.run)?.label || 'Task';
              toast(`${label} started`, 'info');
              // Poll until task finishes
              const taskKey = TASK_DEFS.find(t => t.endpoint === btn.dataset.run)?.key;
              const poll = setInterval(async () => {
                if (!document.getElementById(`task-next-${taskKey}`)) { clearInterval(poll); return; }
                const s = await loadSyncStatus();
                if (!s || !s[taskKey]?.running) clearInterval(poll);
              }, 2000);
            } catch (err) {
              toast('Failed: ' + err.message, 'error');
            } finally {
              btn.disabled = false;
            }
          });
        });
      }
    }
  } catch (err) {
    renderError(app, render);
  }
});

// ── Boot ──────────────────────────────────────────────────────────────────────

window.addEventListener('hashchange', () => {
  updateActiveNav();
  // Close library popup on any navigation
  document.getElementById('nb-library-popup').style.display = 'none';
  render();
});

// ── Theme ─────────────────────────────────────────────────────────────────────

function applyTheme(theme) {
  document.documentElement.classList.toggle('light', theme === 'light');
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.innerHTML = theme === 'light' ? ICON_MOON : ICON_SUN;
}

function toggleTheme() {
  const current = document.documentElement.classList.contains('light') ? 'light' : 'dark';
  const next = current === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', next);
  applyTheme(next);
}

window.addEventListener('DOMContentLoaded', async () => {
  // Apply saved theme before first render to avoid flash
  applyTheme(localStorage.getItem('theme') || 'light');
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

  // Populate bottom nav icons
  document.getElementById('nb-search').innerHTML    = ICON_SEARCH;
  document.getElementById('nb-library').innerHTML   = ICON_LIBRARY;
  document.getElementById('nb-queue').innerHTML     = ICON_REQUESTS;
  document.getElementById('nb-dashboard').innerHTML = ICON_DASHBOARD;
  document.getElementById('nb-settings').innerHTML  = ICON_SETTINGS;
  document.getElementById('nb-profile').innerHTML   = ICON_AUTHOR;

  // Library popup toggle
  const nbLibBtn = document.getElementById('nb-library');
  const nbLibPopup = document.getElementById('nb-library-popup');
  nbLibBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = nbLibPopup.style.display !== 'none';
    nbLibPopup.style.display = isOpen ? 'none' : 'block';
  });
  document.addEventListener('click', () => {
    nbLibPopup.style.display = 'none';
  });
  nbLibPopup.addEventListener('click', (e) => {
    e.stopPropagation();
    nbLibPopup.style.display = 'none';
  });

  // Auth check before first render
  try {
    const meRes = await fetch('/api/auth/me');
    if (meRes.ok) {
      _authUser = await meRes.json();
      if (_authUser.force_password_change && getHashPath() !== '/change-password') {
        location.hash = '#/change-password';
      }
    } else if (meRes.status === 401) {
      const body = await meRes.json().catch(() => ({}));
      const modes = (body.detail || {}).modes || [];
      if (modes.length > 0 && getHashPath() !== '/login' && getHashPath() !== '/change-password') {
        const dest = location.hash.slice(1) || '/';
        location.hash = buildHash('/login', dest !== '/login' ? { next: dest } : {}).slice(1);
      } else if (modes.length > 0 && getHashPath() === '/login') {
        // Already on login page — check if force_local is set in URL and persist it
        const qp = getHashParams();
        if ('force_local' in qp) sessionStorage.setItem('force_local', '1');
      }
    }
  } catch {}

  updateNavForRole();
  updateActiveNav();
  render();
  checkAbsBanner();

  // Apply square covers from ABS library settings (coverAspectRatio 1=square, 0=tall)
  api('/abs/library-settings').then(s => {
    document.body.classList.toggle('square-covers', s.cover_aspect_ratio === 1);
  }).catch(() => {});
});
