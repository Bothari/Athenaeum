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

const ICON_HC = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 7v10M16 7v10M8 12h8"/></svg>`;

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

function formatBytes(bytes) {
  if (!bytes) return '—';
  const gb = bytes / 1e9;
  if (gb >= 1) return gb.toFixed(1) + ' GB';
  return (bytes / 1e6).toFixed(0) + ' MB';
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

// ── API helper ─────────────────────────────────────────────────────────────────

async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
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
  let offset = parseInt(params[`${stateKey}_offset`] || '0', 10);
  let total = 0;
  let loading = false;
  let allLoaded = false;
  let observer = null;

  function updateUrlParams() {
    const allParams = getHashParams();
    allParams[`${stateKey}_sort`] = sort;
    allParams[`${stateKey}_dir`] = dir;
    if (q) allParams[`${stateKey}_q`] = q;
    else delete allParams[`${stateKey}_q`];
    if (offset) allParams[`${stateKey}_offset`] = String(offset);
    else delete allParams[`${stateKey}_offset`];
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
      return `<th class="${sortable}${active}" data-key="${h.key}"${style}>${escapeHtml(h.label)} ${h.sortable !== false ? sortIcon(h.key) : ''}</th>`;
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
      if (reset) tbody.innerHTML = '';
      if (data.items.length === 0 && reset) {
        tbody.innerHTML = `<tr><td colspan="${headers.length}" class="state-empty">${emptyMessage}</td></tr>`;
        allLoaded = true;
        return;
      }
      data.items.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = renderRow(item);
        tbody.appendChild(tr);
      });
      allLoaded = data.items.length < LIMIT;
      if (!allLoaded) attachObserver();
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
      <table>
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

  fetchAndAppend(true);
  return {
    reload() { offset = 0; allLoaded = false; fetchAndAppend(true); },
  };
}

// ── Shared: renderTryLinkLog ───────────────────────────────────────────────────

function renderTryLinkLog(log, type) {
  const hcBaseUrl = { book: 'https://hardcover.app/books', author: 'https://hardcover.app/authors', series: 'https://hardcover.app/series' }[type] || 'https://hardcover.app';
  const resultColors = { linked: 'var(--color-success)', no_match: 'var(--color-error)', no_results: 'var(--color-error)', conflict: 'var(--color-warning)', error: 'var(--color-error)', no_api_key: 'var(--color-error)', not_found: 'var(--color-error)' };
  const color = resultColors[log.result] || 'var(--color-text-dim)';
  let html = `<div style="font-size:0.8rem;background:var(--color-surface);border:1px solid var(--color-border);border-radius:6px;padding:0.75rem;overflow-x:auto">`;
  html += `<div style="margin-bottom:0.5rem;font-family:monospace"><span class="td-dim">result: </span><strong style="color:${color}">${escapeHtml(log.result || '—')}</strong>`;
  if (log.reason) html += ` <span class="td-dim">${escapeHtml(log.reason)}</span>`;
  if (log.error) html += ` <span style="color:var(--color-error)">${escapeHtml(log.error)}</span>`;
  html += `</div>`;
  if (log.query) html += `<div style="margin-bottom:0.5rem;font-family:monospace"><span class="td-dim">query: </span>${escapeHtml(log.query)}</div>`;

  if (type === 'book' && log.candidates && log.candidates.length) {
    html += `<table style="width:100%;border-collapse:collapse;margin-top:0.25rem"><thead><tr style="color:var(--color-text-dim)">
      <th style="text-align:left;padding:2px 6px">title</th>
      <th style="text-align:left;padding:2px 6px">author</th>
      <th style="padding:2px 6px">t</th>
      <th style="padding:2px 6px">a</th>
      <th style="padding:2px 6px"></th>
    </tr></thead><tbody>`;
    for (const c of log.candidates) {
      const rowStyle = c.is_best ? 'background:var(--color-surface-raised)' : '';
      const tColor = c.t_score >= 90 ? 'var(--color-success)' : 'var(--color-error)';
      const aColor = c.a_score >= 85 ? 'var(--color-success)' : 'var(--color-error)';
      const openUrl = c.slug ? `${hcBaseUrl}/${encodeURIComponent(c.slug)}` : '';
      html += `<tr style="${rowStyle}">
        <td style="padding:2px 6px">${c.is_best ? '<strong>' : ''}${escapeHtml(c.title)}${c.is_best ? '</strong>' : ''}</td>
        <td style="padding:2px 6px;color:var(--color-text-dim)">${escapeHtml(c.author)}</td>
        <td style="padding:2px 6px;color:${tColor};text-align:center">${c.t_score}</td>
        <td style="padding:2px 6px;color:${aColor};text-align:center">${c.a_score}</td>
        <td style="padding:2px 6px;white-space:nowrap">
          <button class="btn btn-primary btn-sm try-link-use-btn" data-hc-id="${escapeHtml(c.hc_id)}" style="padding:1px 6px;font-size:0.75rem">Link</button>
          ${openUrl ? `<a href="${escapeHtml(openUrl)}" target="_blank" class="btn btn-secondary btn-sm" style="padding:1px 6px;margin-left:2px" title="Open on Hardcover">${ICON_HC}</a>` : ''}
        </td>
      </tr>`;
    }
    html += `</tbody></table>`;
  } else if ((type === 'author' || type === 'series') && log.candidates && log.candidates.length) {
    html += `<table style="width:100%;border-collapse:collapse;margin-top:0.25rem"><thead><tr style="color:var(--color-text-dim)">
      <th style="text-align:left;padding:2px 6px">name</th>
      <th style="padding:2px 6px">score</th>
      <th style="padding:2px 6px"></th>
    </tr></thead><tbody>`;
    for (const c of log.candidates) {
      const rowStyle = c.is_best ? 'background:var(--color-surface-raised)' : '';
      const scoreColor = c.score >= 85 ? 'var(--color-success)' : 'var(--color-error)';
      const openUrl = c.slug ? `${hcBaseUrl}/${encodeURIComponent(c.slug)}` : '';
      html += `<tr style="${rowStyle}">
        <td style="padding:2px 6px">${c.is_best ? '<strong>' : ''}${escapeHtml(c.name)}${c.is_best ? '</strong>' : ''}</td>
        <td style="padding:2px 6px;color:${scoreColor};text-align:center">${c.score}</td>
        <td style="padding:2px 6px;white-space:nowrap">
          <button class="btn btn-primary btn-sm try-link-use-btn" data-hc-id="${escapeHtml(c.hc_id)}" style="padding:1px 6px;font-size:0.75rem">Link</button>
          ${openUrl ? `<a href="${escapeHtml(openUrl)}" target="_blank" class="btn btn-secondary btn-sm" style="padding:1px 6px;margin-left:2px" title="Open on Hardcover">${ICON_HC}</a>` : ''}
        </td>
      </tr>`;
    }
    html += `</tbody></table>`;
  }

  if (log.result === 'linked') {
    if (log.series_linked && log.series_linked.length) {
      html += `<div style="margin-top:0.5rem;color:var(--color-success)">series linked: ${log.series_linked.map(s => escapeHtml(s.local)).join(', ')}</div>`;
    }
    if (log.authors_linked && log.authors_linked.length) {
      html += `<div style="margin-top:0.25rem;color:var(--color-success)">authors linked: ${log.authors_linked.map(a => escapeHtml(a.local)).join(', ')}</div>`;
    }
  }
  html += `</div>`;
  return html;
}

// ── Shared: renderBookCard ─────────────────────────────────────────────────────

function renderBookCard(book) {
  const author = Array.isArray(book.authors)
    ? book.authors.map(a => a.name).join(', ')
    : (book.author || '');
  const coverImg = book.cover_url
    ? `<img class="book-card-cover" src="${escapeHtml(book.cover_url)}" alt="" loading="lazy">`
    : `<div class="book-card-cover-placeholder">${ICON_EBOOK}</div>`;
  const requests = Array.isArray(book.requests) ? book.requests : [];
  const badges = requests.map(r =>
    `<span class="badge badge-${r.status}">${typeIcon(r.type)}</span>`
  ).join('');

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

// ── Shared: renderSeriesCard ───────────────────────────────────────────────────

function renderSeriesCard(series) {
  const el = document.createElement('div');
  el.className = 'entity-card';
  el.innerHTML = `
    <div class="entity-card-name">${escapeHtml(series.name)}</div>
    <div class="entity-card-meta">${series.book_count || 0} book${series.book_count !== 1 ? 's' : ''}</div>
  `;
  el.onclick = () => navigate('/library/series/' + series.id);
  return el;
}

// ── Shared: renderDetailStats ──────────────────────────────────────────────────
// stats: { inLibrary, total, requested, missing, loadingMissing }

function renderDetailStats(name, stats) {
  const missingText = stats.loadingMissing
    ? `<span class="text-dim">${ICON_SPINNER} loading…</span>`
    : (stats.missing != null ? `${stats.missing} missing` : '—');
  const total = stats.total || '?';
  const pct = (stats.inLibrary && stats.total)
    ? Math.round(stats.inLibrary / stats.total * 100) + '%'
    : '';
  return `
    <div class="card mb-2">
      <div class="stats-row" style="margin-bottom:0">
        <div class="stat-card">
          <div class="stat-value">${stats.inLibrary || 0}</div>
          <div class="stat-label">In library${total !== '?' ? ' / ' + total : ''}</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.requested || 0}</div>
          <div class="stat-label">Requested</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${missingText}</div>
          <div class="stat-label">Missing</div>
        </div>
        ${pct ? `<div class="stat-card"><div class="stat-value">${pct}</div><div class="stat-label">Complete</div></div>` : ''}
      </div>
    </div>
  `;
}

// ── Shared: expandRequestForm ──────────────────────────────────────────────────
// slot: Element to render into
// result: search result shape
// onSuccess: optional callback(createdBook, result, selectedTypes)

function expandRequestForm(slot, result, onSuccess = null) {
  const libFormats = result.library_formats || [];
  const existingReqs = result.existing_requests || [];

  function libFormat(type) {
    return libFormats.find(f => f.type === type);
  }
  function existingReq(type) {
    return existingReqs.find(r => r.type === type && r.status !== 'failed');
  }

  function fmtBtnLabel(type, narratorVal) {
    const ex = existingReq(type);
    if (ex) return `${typeIcon(type)} ${ex.status}`;
    const lib = libFormat(type);
    if (lib && type === 'audiobook' && lib.narrator) return `${typeIcon(type)} have (${lib.narrator})`;
    if (lib) return `${typeIcon(type)} have`;
    return typeIcon(type) + ' ' + (type === 'audiobook' ? 'Audiobook' : 'Ebook');
  }

  function isBtnDisabled(type, narratorVal) {
    const ex = existingReq(type);
    if (ex) return true;
    if (type === 'audiobook') {
      const lib = libFormat('audiobook');
      if (lib && lib.narrator && narratorVal &&
          lib.narrator.toLowerCase() === narratorVal.toLowerCase()) return true;
    }
    return false;
  }

  let selectedType = null;
  let narrator = '';

  function render() {
    slot.innerHTML = `
      <div class="request-form">
        <div class="request-format-btns">
          <button class="btn btn-secondary btn-sm${selectedType === 'audiobook' ? ' btn-primary' : ''}"
            id="rf-audiobook" ${isBtnDisabled('audiobook', narrator) ? 'disabled' : ''}>
            ${fmtBtnLabel('audiobook', narrator)}
          </button>
          <button class="btn btn-secondary btn-sm${selectedType === 'ebook' ? ' btn-primary' : ''}"
            id="rf-ebook" ${isBtnDisabled('ebook', narrator) ? 'disabled' : ''}>
            ${fmtBtnLabel('ebook', narrator)}
          </button>
        </div>
        ${selectedType === 'audiobook' ? `
          <div class="request-narrator">
            <input type="text" id="rf-narrator" placeholder="Narrator (optional)" value="${escapeHtml(narrator)}">
          </div>
        ` : ''}
        ${selectedType ? `
          <div class="request-submit-row">
            <button class="btn btn-primary btn-sm" id="rf-submit">Request</button>
            <button class="btn btn-ghost btn-sm" id="rf-cancel">Cancel</button>
          </div>
        ` : ''}
      </div>
    `;

    slot.querySelector('#rf-audiobook').onclick = () => {
      selectedType = selectedType === 'audiobook' ? null : 'audiobook';
      render();
    };
    slot.querySelector('#rf-ebook').onclick = () => {
      selectedType = selectedType === 'ebook' ? null : 'ebook';
      render();
    };
    if (selectedType === 'audiobook') {
      slot.querySelector('#rf-narrator').oninput = (e) => { narrator = e.target.value; };
    }
    if (selectedType) {
      slot.querySelector('#rf-submit').onclick = () => submitRequest();
      slot.querySelector('#rf-cancel').onclick = () => {
        selectedType = null; narrator = ''; render();
      };
    }
  }

  async function submitRequest() {
    const submitBtn = slot.querySelector('#rf-submit');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.innerHTML = ICON_SPINNER + ' Requesting…'; }

    try {
      // Try POST /api/books (creates book + request if new)
      const body = {
        title: result.title,
        author: result.author,
        cover_url: result.cover_url || null,
        series: result.series && result.series[0] ? result.series[0].name : null,
        series_position: result.series && result.series[0] ? result.series[0].position : null,
        metadata_source: result.metadata_source || null,
        metadata_id: result.metadata_id || null,
        metadata_url: result.metadata_url || null,
        requests: [{ type: selectedType, narrator: selectedType === 'audiobook' ? (narrator || null) : null }],
      };

      let book, skipped = false;
      if (result.book_id) {
        // Book already exists — just create the request
        const reqResult = await api('/requests', {
          method: 'POST',
          body: { book_id: result.book_id, type: selectedType, narrator: selectedType === 'audiobook' ? (narrator || null) : null },
        });
        skipped = reqResult.skipped === true;
        book = { id: result.book_id };
      } else {
        const res = await api('/books', { method: 'POST', body });
        book = res;
        skipped = res._skipped_requests > 0 && res._created_requests === 0;
      }

      if (skipped) {
        toast('Request already exists', 'info');
      } else {
        toast('Requested!', 'success');
      }

      if (onSuccess) {
        onSuccess(book, result, [selectedType]);
      } else {
        navigate('/library/book', { book_id: book.id });
      }
    } catch (err) {
      toast('Request failed: ' + err.message, 'error');
      if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = 'Request'; }
    }
  }

  render();
}

// ── Shared: renderSearchResults ────────────────────────────────────────────────
// container: Element
// results: array of search result shape
// onRequestSuccess: optional callback(book, result, types) — if null, navigates to book

function renderSearchResults(container, results, onRequestSuccess = null) {
  if (!results || results.length === 0) {
    container.innerHTML = `<div class="state-empty">No results found.</div>`;
    return;
  }

  container.innerHTML = `<div class="search-results-header">${results.length} result${results.length !== 1 ? 's' : ''}</div>`;

  results.forEach(result => {
    const card = document.createElement('div');
    card.className = 'search-card';

    const seriesStr = (result.series && result.series[0])
      ? `${escapeHtml(result.series[0].name)}${result.series[0].position ? ' #' + result.series[0].position : ''}`
      : '';

    const ratingStr = result.rating
      ? `${ICON_STAR} ${result.rating.toFixed(1)} (${result.rating_count || 0})`
      : '';

    const inLibBadge = result.in_library
      ? `<span class="badge badge-in_library">${ICON_CHECK} in library</span>`
      : '';

    card.innerHTML = `
      ${result.cover_url
        ? `<img class="search-card-cover" src="${escapeHtml(result.cover_url)}" alt="" loading="lazy">`
        : `<div class="search-card-cover-placeholder">${ICON_EBOOK}</div>`
      }
      <div class="search-card-body">
        <div class="search-card-title">${escapeHtml(result.title)}</div>
        <div class="search-card-author">${escapeHtml(result.author)}</div>
        ${seriesStr ? `<div class="search-card-series">${seriesStr}</div>` : ''}
        <div class="search-card-meta">
          ${ratingStr ? `<span class="search-card-rating">${ratingStr}</span>` : ''}
          ${inLibBadge}
        </div>
        <div class="search-card-actions">
          <button class="btn btn-secondary btn-sm" data-req-toggle>
            ${ICON_DOWNLOAD} Request
          </button>
          ${result.book_id ? `<a href="${buildHash('/library/book', { book_id: result.book_id })}" class="btn btn-ghost btn-sm">View</a>` : ''}
        </div>
        <div class="search-card-slot"></div>
      </div>
    `;

    const reqBtn = card.querySelector('[data-req-toggle]');
    const slot = card.querySelector('.search-card-slot');

    reqBtn.onclick = () => {
      if (slot.innerHTML.trim()) {
        slot.innerHTML = '';
        return;
      }
      expandRequestForm(slot, result, (book, res, types) => {
        slot.innerHTML = '';
        // Update in-place
        card.querySelector('.search-card-actions .btn-secondary').innerHTML = `${ICON_CHECK} Requested`;
        card.querySelector('.search-card-actions .btn-secondary').disabled = true;
        if (onRequestSuccess) onRequestSuccess(book, res, types);
      });
    };

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

async function render() {
  // Remove home-page class before every render; home route re-adds it
  document.body.classList.remove('home-page');
  const path = getHashPath() || '/';
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
  };
  for (const [id, test] of Object.entries(nbMap)) {
    if (test()) document.getElementById(id)?.classList.add('active');
  }
}

// ── Routes ────────────────────────────────────────────────────────────────────

// Home / Search
route('/', async (params, qp) => {
  document.body.classList.add('home-page');

  const q = qp.q || '';
  const author = qp.author || '';
  const series = qp.series || '';
  const advanced = qp.advanced === '1';
  const hasValue = !!(q || author || series);

  app.innerHTML = `
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
  `;

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
    const qVal = qInput.value.trim();
    const authorVal = document.getElementById('search-author')?.value.trim() || '';
    const seriesVal = document.getElementById('search-series')?.value.trim() || '';
    const isAdv = advFields.classList.contains('open');

    if (!qVal && !authorVal && !seriesVal) return;

    // Update URL
    const newParams = {};
    if (qVal) newParams.q = qVal;
    if (authorVal) newParams.author = authorVal;
    if (seriesVal) newParams.series = seriesVal;
    if (isAdv) newParams.advanced = '1';
    history.replaceState(null, '', buildHash('/', newParams));

    // Move input to top
    searchPage.classList.remove('empty');

    renderLoading(resultsDiv);

    try {
      let data;
      if (isAdv) {
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
    app.innerHTML = `
      <div class="page-header"><span class="page-title">${ICON_LIBRARY} Books</span></div>
      <div id="books-content"></div>
    `;

    const content = document.getElementById('books-content');

    let booksUnlinked = false;
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
      extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="books-unlinked-cb"> Unlinked only</label>`,
      renderRow: (b) => {
        const author = Array.isArray(b.authors) ? b.authors.map(a => a.name).join(', ') : '—';
        const requests = b.requests || [];
        const inLibraryTypes = new Set(requests.filter(r => r.status === 'in_library').map(r => r.type));
        const pending = requests.filter(r => r.status !== 'in_library');
        const formatBadges = [...inLibraryTypes].map(t =>
          `<span class="badge badge-in_library">${typeIcon(t)}</span>`
        ).join(' ');
        const pendingBadges = pending.map(r =>
          `<span class="badge badge-${r.status}">${typeIcon(r.type)} ${r.status}</span>`
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
  app.innerHTML = `
    <div class="page-header"><span class="page-title">${ICON_AUTHOR} Authors</span></div>
    <div id="authors-content"></div>
  `;
  const content = document.getElementById('authors-content');
  let authorsUnlinked = false;
  const authorsTable = renderTable({
    container: content,
    stateKey: 'authors',
    headers: [
      { label: 'Name', key: 'name', sortable: true },
      { label: 'Books', key: 'book_count', sortable: true, style: 'width:80px' },
    ],
    fetchFn: (p) => api('/authors?' + new URLSearchParams(p).toString()),
    extraFetchParams: () => authorsUnlinked ? { unlinked: '1' } : {},
    extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="authors-unlinked-cb"> Unlinked only</label>`,
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
      app.innerHTML = `
        <div class="page-header">
          <span class="page-title">${ICON_AUTHOR} ${escapeHtml(authorName)}</span>
          <div class="view-toggle">
            <button class="view-toggle-btn${view === 'poster' ? ' active' : ''}" id="vt-poster" title="Poster">${ICON_GRID_V}</button>
            <button class="view-toggle-btn${view === 'list' ? ' active' : ''}" id="vt-list" title="List">${ICON_LIST_V}</button>
          </div>
        </div>
        <div id="author-books"></div>
        <div id="author-hc-section" class="mt-2"></div>
        <div id="author-debug-section"></div>
      `;
      document.getElementById('vt-poster').onclick = () => { localStorage.setItem('detail_view', 'poster'); renderAuthorBooksView(); };
      document.getElementById('vt-list').onclick   = () => { localStorage.setItem('detail_view', 'list');   renderAuthorBooksView(); };

      // HC match section
      const authorEntry = books.flatMap(b => b.authors || []).find(a => a.id === id) || {};
      const hcAuthorId = authorEntry.hardcover_author_id;
      const authorHcSection = document.getElementById('author-hc-section');
      if (authorHcSection) {
        const renderAuthorHcSection = (currentHcId) => {
          authorHcSection.innerHTML = `
            <div class="section-heading">Hardcover</div>
            <div class="card">
              <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap">
                ${currentHcId
                  ? `<span class="text-dim" style="font-size:0.875rem">Linked to HC #${escapeHtml(String(currentHcId))}</span>
                     <button class="btn btn-secondary btn-sm" id="author-unlink-btn" style="padding:2px 8px;font-size:0.8rem">Unlink</button>`
                  : `<span class="text-dim" style="font-size:0.875rem">Not linked to Hardcover.</span>`
                }
              </div>
              <div style="margin-bottom:0.75rem">
                <button class="btn btn-secondary btn-sm" id="author-try-link-btn">${currentHcId ? 'Re-run match' : 'Try HC match'}</button>
              </div>
              <div id="author-try-link-result"></div>
              <div style="display:flex;gap:0.5rem;align-items:center;margin-top:0.75rem">
                <input type="text" class="form-input" id="author-hc-id-input" placeholder="Paste HC ID to set manually" style="flex:1;min-width:0">
                <button class="btn btn-secondary btn-sm" id="author-set-link-btn">Set</button>
              </div>
            </div>
          `;
          const resultEl = document.getElementById('author-try-link-result');
          document.getElementById('author-try-link-btn').onclick = async function() {
            this.disabled = true;
            this.textContent = 'Matching...';
            try {
              const log = await api(`/sync/try-link/author/${id}`, { method: 'POST' });
              resultEl.innerHTML = renderTryLinkLog(log, 'author');
            } catch (e) {
              resultEl.innerHTML = `<p style="color:var(--color-error);font-size:0.875rem">${escapeHtml(String(e))}</p>`;
            }
            this.disabled = false;
            this.textContent = 'Re-run match';
          };
          resultEl.addEventListener('click', async e => {
            const btn = e.target.closest('.try-link-use-btn');
            if (!btn) return;
            btn.disabled = true;
            try {
              const hcId = btn.dataset.hcId;
              await api(`/sync/link/author/${id}`, { method: 'PUT', body: { hardcover_id: hcId } });
              renderAuthorHcSection(hcId);
              toast('Linked', 'success');
            } catch (e) {
              toast('Failed: ' + e, 'error');
              btn.disabled = false;
            }
          });
          const unlinkBtn = document.getElementById('author-unlink-btn');
          if (unlinkBtn) unlinkBtn.onclick = async function() {
            this.disabled = true;
            try {
              await api(`/sync/link/author/${id}`, { method: 'PUT', body: { hardcover_id: '' } });
              renderAuthorHcSection(null);
              toast('Unlinked', 'success');
            } catch (e) {
              toast('Unlink failed: ' + e, 'error');
              this.disabled = false;
            }
          };
          document.getElementById('author-set-link-btn').onclick = async function() {
            const hcId = document.getElementById('author-hc-id-input').value.trim();
            if (!hcId) return;
            this.disabled = true;
            try {
              await api(`/sync/link/author/${id}`, { method: 'PUT', body: { hardcover_id: hcId } });
              renderAuthorHcSection(hcId);
              toast('Link updated', 'success');
            } catch (e) {
              toast('Failed: ' + e, 'error');
            }
            this.disabled = false;
          };
        };
        renderAuthorHcSection(hcAuthorId);
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
    renderAuthorBooksView();
  } catch (err) {
    renderError(app, render);
  }
});

// Library: Series list
route('/library/series', async () => {
  app.innerHTML = `
    <div class="page-header"><span class="page-title">${ICON_SERIES} Series</span></div>
    <div id="series-content"></div>
  `;
  const content = document.getElementById('series-content');
  let seriesUnlinked = false;
  const seriesTable = renderTable({
    container: content,
    stateKey: 'series',
    headers: [
      { label: 'Name', key: 'name', sortable: true },
      { label: 'Books', key: 'book_count', sortable: true, style: 'width:80px' },
    ],
    fetchFn: (p) => api('/series?' + new URLSearchParams(p).toString()),
    extraFetchParams: () => seriesUnlinked ? { unlinked: '1' } : {},
    extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="series-unlinked-cb"> Unlinked only</label>`,
    renderRow: (s) => `
      <td><a href="#/library/series/${s.id}">${escapeHtml(s.name)}</a></td>
      <td class="td-dim">${s.book_count || 0}</td>
    `,
    emptyMessage: 'No series yet. Series are added automatically when books with series data are synced.',
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
    const [booksData] = await Promise.all([
      api(`/series/${id}/books`),
    ]);

    const seriesName = booksData.length && booksData[0].series
      ? (booksData[0].series.find(s => s.id === id) || booksData[0].series[0] || {}).name || 'Series'
      : 'Series';

    const inLibrary = booksData.filter(b => (b.requests || []).some(r => r.status === 'in_library')).length;
    const requested = booksData.filter(b => (b.requests || []).some(r => !['in_library', 'failed'].includes(r.status))).length;

    function renderSeriesBooksView() {
      const view = localStorage.getItem('detail_view') || 'list';
      app.innerHTML = `
        <div class="page-header">
          <span class="page-title">${ICON_SERIES} ${escapeHtml(seriesName)}</span>
          <div class="view-toggle">
            <button class="view-toggle-btn${view === 'poster' ? ' active' : ''}" id="vt-poster" title="Poster">${ICON_GRID_V}</button>
            <button class="view-toggle-btn${view === 'list' ? ' active' : ''}" id="vt-list" title="List">${ICON_LIST_V}</button>
          </div>
        </div>
        <div id="series-stats">${renderDetailStats(seriesName, { inLibrary, total: booksData.length, requested, loadingMissing: true })}</div>
        <div class="section-heading">Books in Library</div>
        <div id="series-books"></div>
        <div id="series-missing-section"></div>
        <div id="series-hc-section" class="mt-2"></div>
        <div id="series-debug-section"></div>
      `;
      document.getElementById('vt-poster').onclick = () => { localStorage.setItem('detail_view', 'poster'); renderSeriesBooksView(); loadSeriesExtras(); };
      document.getElementById('vt-list').onclick   = () => { localStorage.setItem('detail_view', 'list');   renderSeriesBooksView(); loadSeriesExtras(); };

      const booksContainer = document.getElementById('series-books');
      if (view === 'list') {
        const table = document.createElement('table');
        table.className = 'data-table';
        table.innerHTML = `<thead><tr><th style="width:3rem">#</th><th>Title</th><th style="width:100px">Formats</th></tr></thead>`;
        const tbody = document.createElement('tbody');
        booksData.forEach(b => {
          const inLibTypes = (b.requests || []).filter(r => r.status === 'in_library').map(r => r.type);
          const fmtBadges = inLibTypes.map(t => `<span class="badge badge-in_library">${typeIcon(t)}</span>`).join(' ');
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
        booksData.forEach(b => grid.appendChild(renderBookCard(b)));
        booksContainer.appendChild(grid);
      }
    }
    renderSeriesBooksView();

    // Load missing books async
    async function loadSeriesExtras() {
      const seriesLink = (booksData[0]?.series || []).find(s => s.id === id);
      const hcSeriesId = seriesLink?.hardcover_series_id;
      if (hcSeriesId) {
        try {
          const missing = await api(`/series/${id}/missing`);
          const statsEl = document.getElementById('series-stats');
          if (statsEl) statsEl.innerHTML = renderDetailStats(seriesName, {
            inLibrary,
            total: booksData.length + (missing.results || []).length,
            requested,
            missing: (missing.results || []).length,
            loadingMissing: false,
          });

          const missingSection = document.getElementById('series-missing-section');
          if (missingSection && missing.results && missing.results.length) {
            missingSection.innerHTML = `<div class="section-heading mt-2">Missing Books</div><div id="missing-results"></div>`;
            renderSearchResults(document.getElementById('missing-results'), missing.results, () => {});
            if (missing.truncated) {
              missingSection.innerHTML += `<p class="text-dim mt-1" style="font-size:0.85rem">Showing first 50 entries — this series is too large to display in full.</p>`;
            }
          } else {
            const statsEl2 = document.getElementById('series-stats');
            if (statsEl2) statsEl2.innerHTML = renderDetailStats(seriesName, {
              inLibrary, total: booksData.length, requested, missing: 0, loadingMissing: false,
            });
          }
        } catch {
          const statsEl = document.getElementById('series-stats');
          if (statsEl) statsEl.innerHTML = renderDetailStats(seriesName, {
            inLibrary, total: booksData.length, requested, loadingMissing: false,
          });
        }
      } else {
        const statsEl = document.getElementById('series-stats');
        if (statsEl) statsEl.innerHTML = renderDetailStats(seriesName, {
          inLibrary, total: booksData.length, requested, loadingMissing: false,
        });
      }

      // HC match section + debug card
      try {
        const [s, seriesData] = await Promise.all([api('/settings'), api(`/series/${id}`)]);
        const hcSeriesId = (seriesData.link || {}).hardcover_series_id;
        const seriesHcSection = document.getElementById('series-hc-section');
        if (seriesHcSection) {
          const renderSeriesHcSection = (currentHcId) => {
            seriesHcSection.innerHTML = `
              <div class="section-heading">Hardcover</div>
              <div class="card">
                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap">
                  ${currentHcId
                    ? `<span class="text-dim" style="font-size:0.875rem">Linked to HC #${escapeHtml(String(currentHcId))}</span>
                       <button class="btn btn-secondary btn-sm" id="series-unlink-btn" style="padding:2px 8px;font-size:0.8rem">Unlink</button>`
                    : `<span class="text-dim" style="font-size:0.875rem">Not linked to Hardcover.</span>`
                  }
                </div>
                <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;margin-bottom:0.75rem">
                  <button class="btn btn-secondary btn-sm" id="series-try-link-btn">${currentHcId ? 'Re-run match' : 'Try HC match'}</button>
                </div>
                <div id="series-try-link-result"></div>
                <div style="display:flex;gap:0.5rem;align-items:center;margin-top:0.75rem">
                  <input type="text" class="form-input" id="series-hc-id-input" placeholder="Paste HC ID to set manually" style="flex:1;min-width:0">
                  <button class="btn btn-secondary btn-sm" id="series-set-link-btn">Set</button>
                </div>
              </div>
            `;
            const resultEl = document.getElementById('series-try-link-result');
            document.getElementById('series-try-link-btn').onclick = async function() {
              this.disabled = true;
              this.textContent = 'Matching...';
              try {
                const log = await api(`/sync/try-link/series/${id}`, { method: 'POST' });
                resultEl.innerHTML = renderTryLinkLog(log, 'series');
              } catch (e) {
                resultEl.innerHTML = `<p style="color:var(--color-error);font-size:0.875rem">${escapeHtml(String(e))}</p>`;
              }
              this.disabled = false;
              this.textContent = 'Re-run match';
            };
            resultEl.addEventListener('click', async e => {
              const btn = e.target.closest('.try-link-use-btn');
              if (!btn) return;
              btn.disabled = true;
              try {
                const hcId = btn.dataset.hcId;
                await api(`/sync/link/series/${id}`, { method: 'PUT', body: { hardcover_id: hcId } });
                renderSeriesHcSection(hcId);
                toast('Linked', 'success');
              } catch (e) {
                toast('Failed: ' + e, 'error');
                btn.disabled = false;
              }
            });
            const unlinkBtn = document.getElementById('series-unlink-btn');
            if (unlinkBtn) unlinkBtn.onclick = async function() {
              this.disabled = true;
              try {
                await api(`/sync/link/series/${id}`, { method: 'PUT', body: { hardcover_id: '' } });
                renderSeriesHcSection(null);
                toast('Unlinked', 'success');
              } catch (e) {
                toast('Unlink failed: ' + e, 'error');
                this.disabled = false;
              }
            };
            document.getElementById('series-set-link-btn').onclick = async function() {
              const hcId = document.getElementById('series-hc-id-input').value.trim();
              if (!hcId) return;
              this.disabled = true;
              try {
                await api(`/sync/link/series/${id}`, { method: 'PUT', body: { hardcover_id: hcId } });
                renderSeriesHcSection(hcId);
                toast('Link updated', 'success');
              } catch (e) {
                toast('Failed: ' + e, 'error');
              }
              this.disabled = false;
            };
          };
          renderSeriesHcSection(hcSeriesId);
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
    loadSeriesExtras();
  } catch (err) {
    renderError(app, render);
  }
});

// Book detail
route('/library/book', async (params, qp) => {
  const bookId = qp.book_id;
  if (!bookId) { app.innerHTML = `<div class="state-empty mt-2">No book specified.</div>`; return; }
  renderLoading(app);
  try {
    const book = await api(`/books/${bookId}`);
    const author = (book.authors || []).map(a => a.name).join(', ');
    const seriesInfo = (book.series || []).map(s => `${s.name}${s.position ? ' #' + s.position : ''}`).join(', ');

    app.innerHTML = `
      <div class="detail-header">
        ${book.cover_url
          ? `<img class="detail-cover" src="${escapeHtml(book.cover_url)}" alt="">`
          : `<div class="detail-cover-placeholder">${ICON_EBOOK}</div>`}
        <div class="detail-meta">
          <div class="detail-title">${escapeHtml(book.title)}</div>
          <div class="detail-author">${escapeHtml(author)}</div>
          ${seriesInfo ? `<div class="detail-series">${escapeHtml(seriesInfo)}</div>` : ''}
          <div class="detail-badges">
            ${(book.requests || []).filter(r => r.status === 'in_library').map(r =>
              `<span class="badge badge-in_library">${typeIcon(r.type)}${r.narrator ? ' ' + escapeHtml(r.narrator) : ''}</span>`
            ).join('')}
            ${(book.requests || []).filter(r => r.status !== 'in_library').map(r =>
              `<span class="badge badge-${r.status}">${typeIcon(r.type)} ${r.status}</span>`
            ).join('')}
          </div>
        </div>
      </div>
      <div id="book-requests-section"></div>
      <div id="book-abs-section" class="mt-2"></div>
      <div id="book-hc-section" class="mt-2"></div>
      <div id="book-debug-section"></div>
    `;

    // HC match section
    const hcSection = document.getElementById('book-hc-section');
    if (hcSection) {
      const renderBookHcSection = (currentHcId) => {
        hcSection.innerHTML = `
          <div class="section-heading">Hardcover</div>
          <div class="card">
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap">
              ${currentHcId
                ? `<span class="text-dim" style="font-size:0.875rem">Linked to HC #${escapeHtml(String(currentHcId))}</span>
                   <button class="btn btn-secondary btn-sm" id="book-unlink-btn" style="padding:2px 8px;font-size:0.8rem">Unlink</button>`
                : `<span class="text-dim" style="font-size:0.875rem">Not linked to Hardcover.</span>`
              }
            </div>
            <div style="margin-bottom:0.75rem">
              <button class="btn btn-secondary btn-sm" id="book-try-link-btn">${currentHcId ? 'Re-run match' : 'Try HC match'}</button>
            </div>
            <div id="book-try-link-result"></div>
            <div style="display:flex;gap:0.5rem;align-items:center;margin-top:0.75rem">
              <input type="text" class="form-input" id="book-hc-id-input" placeholder="Paste HC ID to set manually" style="flex:1;min-width:0">
              <button class="btn btn-secondary btn-sm" id="book-set-link-btn">Set</button>
            </div>
          </div>
        `;
        const resultEl = document.getElementById('book-try-link-result');
        document.getElementById('book-try-link-btn').onclick = async function() {
          this.disabled = true;
          this.textContent = 'Matching...';
          try {
            const log = await api(`/sync/try-link/book/${bookId}`, { method: 'POST' });
            resultEl.innerHTML = renderTryLinkLog(log, 'book');
          } catch (e) {
            resultEl.innerHTML = `<p style="color:var(--color-error);font-size:0.875rem">Request failed: ${escapeHtml(String(e))}</p>`;
          }
          this.disabled = false;
          this.textContent = 'Re-run match';
        };
        resultEl.addEventListener('click', async e => {
          const btn = e.target.closest('.try-link-use-btn');
          if (!btn) return;
          btn.disabled = true;
          try {
            const hcId = btn.dataset.hcId;
            await api(`/sync/link/book/${bookId}`, { method: 'PUT', body: { hardcover_id: hcId } });
            renderBookHcSection(hcId);
            toast('Linked', 'success');
          } catch (e) {
            toast('Failed: ' + e, 'error');
            btn.disabled = false;
          }
        });
        const unlinkBtn = document.getElementById('book-unlink-btn');
        if (unlinkBtn) unlinkBtn.onclick = async function() {
          this.disabled = true;
          try {
            await api(`/sync/link/book/${bookId}`, { method: 'PUT', body: { hardcover_id: '' } });
            renderBookHcSection(null);
            toast('Unlinked', 'success');
          } catch (e) {
            toast('Unlink failed: ' + e, 'error');
            this.disabled = false;
          }
        };
        document.getElementById('book-set-link-btn').onclick = async function() {
          const hcId = document.getElementById('book-hc-id-input').value.trim();
          if (!hcId) return;
          this.disabled = true;
          try {
            await api(`/sync/link/book/${bookId}`, { method: 'PUT', body: { hardcover_id: hcId } });
            renderBookHcSection(hcId);
            toast('Link updated', 'success');
          } catch (e) {
            toast('Failed: ' + e, 'error');
          }
          this.disabled = false;
        };
      };
      renderBookHcSection((book.link || {}).hardcover_id);
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

    // Requests section — only non-in_library requests
    const reqSection = document.getElementById('book-requests-section');
    const pendingRequests = (book.requests || []).filter(r => r.status !== 'in_library');
    if (pendingRequests.length) {
      reqSection.innerHTML = `<div class="section-heading">Requests</div>`;
      pendingRequests.forEach(req => {
        const row = document.createElement('div');
        row.className = 'collapsible-row';
        row.innerHTML = `
          <button class="collapsible-trigger">
            <span class="badge badge-${req.status}">${typeIcon(req.type)} ${req.status}</span>
            ${req.narrator ? `<span class="text-dim" style="font-size:0.85rem">— ${escapeHtml(req.narrator)}</span>` : ''}
            <span style="margin-left:auto">${ICON_CHEVRON_DOWN}</span>
          </button>
          <div class="collapsible-content" style="display:none">
            <div class="flex-gap mt-1" id="req-actions-${req.id}">
              <a href="#/requests/${req.id}" class="btn btn-secondary btn-sm">View detail</a>
              <button class="btn btn-ghost btn-sm" id="req-delete-${req.id}">Delete</button>
            </div>
          </div>
        `;
        const trigger = row.querySelector('.collapsible-trigger');
        const content = row.querySelector('.collapsible-content');
        trigger.onclick = () => {
          const open = content.style.display !== 'none';
          content.style.display = open ? 'none' : 'block';
          trigger.querySelector('svg:last-child').outerHTML = open ? ICON_CHEVRON_DOWN : ICON_CHEVRON_UP;
        };
        document.addEventListener('click', () => {}, { once: true });
        reqSection.appendChild(row);

        // Delete button
        setTimeout(() => {
          const deleteBtn = document.getElementById(`req-delete-${req.id}`);
          if (deleteBtn) {
            deleteBtn.onclick = () => confirmAction(deleteBtn, 'Confirm delete', async () => {
              try {
                await api(`/requests/${req.id}`, { method: 'DELETE' });
                row.remove();
                toast('Request deleted');
              } catch {
                toast('Delete failed', 'error');
              }
            });
          }
        }, 0);
      });
    }
  } catch (err) {
    renderError(app, render);
  }
});

// Queue (Requests + Downloads tabs)
route('/requests', async (params, qp) => {
  const tab = qp.tab === 'downloads' ? 'downloads' : 'requests';

  app.innerHTML = `
    <div class="page-header"><span class="page-title">${ICON_REQUESTS} Queue</span></div>
    <div class="tabs">
      <button class="tab-btn${tab === 'requests' ? ' active' : ''}" data-tab="requests">Requests</button>
      <button class="tab-btn${tab === 'downloads' ? ' active' : ''}" data-tab="downloads">Downloads</button>
    </div>
    <div id="queue-content"></div>
  `;

  app.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    btn.onclick = () => {
      const hp = getHashParams();
      if (btn.dataset.tab === 'downloads') hp.tab = 'downloads';
      else delete hp.tab;
      history.replaceState(null, '', buildHash('/requests', hp));
      render();
    };
  });

  const content = document.getElementById('queue-content');
  if (tab === 'downloads') { renderDownloadsTab(content); return; }

  const statusFilter = qp.requests_status || '';
  const typeFilter = qp.requests_type || '';

  const statusOptions = ['', 'requested', 'monitored', 'snatched', 'downloading', 'organizing', 'in_library', 'failed'];
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
      { label: 'Author', key: 'author', sortable: false },
      { label: 'Type', key: 'type', sortable: false, style: 'width:50px' },
      { label: 'Status', key: 'status', sortable: true },
      { label: 'Narrator', key: 'narrator', sortable: false },
      { label: 'Created', key: 'created_at', sortable: true },
      { label: '', key: '_actions', sortable: false, style: 'width:100px' },
    ],
    fetchFn: fetchRequests,
    extraControls: statusSelect + typeSelect,
    renderRow: (r) => `
      <td><a href="#/library/book?book_id=${r.book_id}">${escapeHtml(r.book_title || r.title || '—')}</a></td>
      <td class="td-dim">${escapeHtml(r.author || '—')}</td>
      <td>${typeIcon(r.type)}</td>
      <td><span class="badge badge-${r.status}">${r.status}</span></td>
      <td class="td-dim">${escapeHtml(r.narrator || '—')}</td>
      <td class="td-dim">${formatDate(r.created_at)}</td>
      <td></td>
    `,
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
});

// Request detail
route('/requests/:id', async ({ id }) => {
  renderLoading(app);
  try {
    const req = await api(`/requests/${id}`);
    app.innerHTML = `
      <div class="page-header">
        <span class="page-title">${ICON_REQUESTS} Request</span>
        <a href="#/requests" class="btn btn-ghost btn-sm">← Back</a>
      </div>
      <div class="card">
        <div><strong>${escapeHtml(req.book_title || '—')}</strong></div>
        <div class="text-dim mt-1">${typeIcon(req.type)} ${req.type}</div>
        <div class="mt-1"><span class="badge badge-${req.status}">${req.status}</span></div>
        ${req.narrator ? `<div class="text-dim mt-1">Narrator: ${escapeHtml(req.narrator)}</div>` : ''}
        <div class="text-dim mt-1" style="font-size:0.8rem">Created: ${formatDate(req.created_at)}</div>
      </div>
      <div id="req-detail-actions" class="flex-gap mt-2">
        <button class="btn btn-primary btn-sm" id="search-prowlarr-btn">${ICON_SEARCH} Search Prowlarr</button>
      </div>
      <div id="req-indexer-results" class="mt-2"></div>
      <div id="req-downloads" class="mt-2"></div>
    `;

    // Load downloads
    try {
      const dlData = await api(`/requests/${id}/downloads`);
      const dlSection = document.getElementById('req-downloads');
      if (dlData && dlData.length) {
        dlSection.innerHTML = `<div class="section-heading">Download History</div>`;
        dlData.forEach(dl => {
          const row = document.createElement('div');
          row.className = 'card mt-1';
          row.style.fontSize = '0.85rem';
          row.innerHTML = `
            <div>${escapeHtml(dl.title || '—')}</div>
            <div class="text-dim">${escapeHtml(dl.indexer || '—')} · ${dl.protocol || '—'} · ${formatBytes(dl.size)}</div>
            <div class="text-dim mt-1"><span class="badge badge-${dl.status}">${dl.status}</span> ${formatDate(dl.grabbed_at)}</div>
            ${dl.download_path ? `<div class="text-mono mt-1">${escapeHtml(dl.download_path)}</div>` : ''}
          `;
          dlSection.appendChild(row);
        });
      }
    } catch { /* no downloads yet */ }

    // Prowlarr search
    document.getElementById('search-prowlarr-btn').onclick = async () => {
      const btn = document.getElementById('search-prowlarr-btn');
      btn.disabled = true;
      btn.innerHTML = ICON_SPINNER + ' Searching…';
      const resultsDiv = document.getElementById('req-indexer-results');
      renderLoading(resultsDiv);
      try {
        const results = await api(`/requests/${id}/search-indexers`, { method: 'POST' });
        if (!results || !results.length) {
          resultsDiv.innerHTML = `<div class="state-empty">No results found.</div>`;
        } else {
          resultsDiv.innerHTML = `<div class="section-heading">Indexer Results (${results.length})</div>`;
          results.forEach(r => {
            const row = document.createElement('div');
            row.className = 'card mt-1';
            row.style.fontSize = '0.85rem';
            row.innerHTML = `
              <div style="display:flex;justify-content:space-between;align-items:start;gap:0.5rem">
                <div>
                  <div>${escapeHtml(r.title || '—')}</div>
                  <div class="text-dim">${escapeHtml(r.indexer || '—')} · ${r.protocol || '—'} · ${formatBytes(r.size)}</div>
                </div>
                <button class="btn btn-primary btn-sm" data-grab>Download</button>
              </div>
            `;
            row.querySelector('[data-grab]').onclick = async () => {
              try {
                await api(`/requests/${id}/download`, {
                  method: 'POST',
                  body: {
                    download_url: r.download_url,
                    protocol: r.protocol,
                    indexer: r.indexer,
                    guid: r.guid,
                    title: r.title,
                    info_url: r.info_url,
                    size: r.size,
                  },
                });
                toast('Download started!');
                navigate('/requests/' + id);
              } catch (err) {
                toast('Download failed: ' + err.message, 'error');
              }
            };
            resultsDiv.appendChild(row);
          });
        }
      } catch (err) {
        renderError(resultsDiv, () => document.getElementById('search-prowlarr-btn')?.click());
      } finally {
        btn.disabled = false;
        btn.innerHTML = ICON_SEARCH + ' Search Prowlarr';
      }
    };
  } catch (err) {
    renderError(app, render);
  }
});

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
        const el = document.createElement('div');
        el.id = 'dl-list';
        container.appendChild(el);
        return el;
      })();

      listEl.innerHTML = items.map(dl => `
        <div class="card mb-1">
          <div style="display:flex;justify-content:space-between;gap:0.5rem">
            <div>
              <div>${escapeHtml(dl.title || dl.book_title || '—')}</div>
              <div class="text-dim" style="font-size:0.8rem">${dl.download_client || '—'}</div>
            </div>
            <span class="badge badge-${dl.status || 'downloading'}">${dl.status || 'downloading'}</span>
          </div>
          ${dl.progress != null ? `
            <div class="progress-bar-track mt-1">
              <div class="progress-bar-fill" style="width:${Math.round(dl.progress * 100)}%"></div>
            </div>
            <div class="text-dim mt-1" style="font-size:0.78rem">
              ${Math.round(dl.progress * 100)}%
              ${dl.eta ? ' · ETA ' + dl.eta : ''}
              ${dl.speed ? ' · ' + dl.speed : ''}
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

// /#/downloads redirects to Queue > Downloads tab
route('/downloads', () => {
  history.replaceState(null, '', '#/requests?tab=downloads');
  render();
});

// Dashboard
route('/dashboard', async () => {
  renderLoading(app);
  try {
    const [status, syncStatus] = await Promise.all([
      api('/status'),
      api('/sync/status'),
    ]);

    app.innerHTML = `
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

      <div class="section-heading">Hardcover Links</div>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value${status.unlinked_books ? '' : ' text-green'}">${status.unlinked_books || 0}</div>
          <div class="stat-label">Books unlinked</div>
        </div>
        <div class="stat-card">
          <div class="stat-value${status.unlinked_authors ? '' : ' text-green'}">${status.unlinked_authors || 0}</div>
          <div class="stat-label">Authors unlinked</div>
        </div>
        <div class="stat-card">
          <div class="stat-value${status.unlinked_series ? '' : ' text-green'}">${status.unlinked_series || 0}</div>
          <div class="stat-label">Series unlinked</div>
        </div>
      </div>

      <div class="section-heading">Scheduled Tasks</div>
      <div class="stats-row tasks-row" id="dash-tasks"></div>
    `;

    const DASH_TASKS = [
      { key: 'library_sync',  label: 'Library sync',  endpoint: '/sync/library'       },
      { key: 'cache_refresh', label: 'Cache refresh', endpoint: '/sync/cache-refresh' },
      { key: 'auto_search',   label: 'Auto search',   endpoint: null                  },
    ];

    function renderDashTask(key, label, endpoint, t) {
      const disabled = !t.next_run && !t.running;
      const resultClass = (t.last_result === 'ok') ? 'text-green' : (t.last_result ? 'text-red' : '');
      return `
        <div class="stat-card${disabled ? ' stat-card-disabled' : ''}" id="dash-task-${key}">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem">
            <div style="font-size:0.9rem;font-weight:600">${label}</div>
            ${endpoint ? `<button class="btn btn-ghost btn-sm dash-run-btn" data-endpoint="${endpoint}" data-key="${key}" style="font-size:0.78rem;padding:0.15rem 0.5rem;white-space:nowrap">${ICON_PLAY} Run</button>` : ''}
          </div>
          <div class="text-dim mt-1" style="font-size:0.78rem" id="dash-task-status-${key}">
            ${disabled ? 'Disabled' : t.running ? `${ICON_SPINNER} running` : t.last_run ? `Last: ${formatDate(t.last_run)}` : 'Never run'}
          </div>
          ${!disabled && t.last_result ? `<div class="${resultClass}" style="font-size:0.78rem;margin-top:0.2rem" id="dash-task-result-${key}">${escapeHtml(t.last_result)}</div>` : `<div id="dash-task-result-${key}"></div>`}
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
          const resultClass = (t.last_result === 'ok') ? 'text-green' : (t.last_result ? 'text-red' : '');
          resultEl.className = resultClass;
          resultEl.textContent = (!disabled && t.last_result) ? t.last_result : '';
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
  } catch (err) {
    renderError(app, render);
  }
});

// Settings
route('/settings', async () => {
  renderLoading(app);
  try {
    const settings = await api('/settings');

    const tabs = ['General', 'ABS', 'Prowlarr', 'qBittorrent', 'SABnzbd', 'Hardcover', 'Pushover', 'Tasks'];

    app.innerHTML = `
      <div class="page-header"><span class="page-title">${ICON_SETTINGS} Settings</span></div>
      <div class="tabs-wrap">
        <div class="tabs">
          ${tabs.map((t, i) => `<button class="tab-btn${i === 0 ? ' active' : ''}" data-tab="${t}">${t}</button>`).join('')}
        </div>
      </div>
      <div id="settings-content"></div>
    `;

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
        case 'Pushover': return buildPushoverTab(settings);
        case 'Tasks': return buildTasksTab(settings);
        default: return '<div class="text-dim">Coming soon.</div>';
      }
    }

    function showTab(name) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
      content.innerHTML = buildTabContent(name);
      wireTabEvents(name);
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.onclick = () => showTab(btn.dataset.tab);
    });

    showTab('General');

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
        ${field('URL', 'url', a.url, 'text', 'e.g. http://192.168.1.10:13378')}
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

    function buildPushoverTab(s) {
      const p = s.pushover || {};
      return `
        ${field('App Token', 'app_token', p.app_token, 'password')}
        ${field('User Key', 'user_key', p.user_key, 'password')}
        ${saveButton('pushover')}
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

window.addEventListener('DOMContentLoaded', () => {
  // Apply saved theme before first render to avoid flash
  applyTheme(localStorage.getItem('theme') || 'light');
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

  // Populate bottom nav icons
  document.getElementById('nb-search').innerHTML    = ICON_SEARCH;
  document.getElementById('nb-library').innerHTML   = ICON_LIBRARY;
  document.getElementById('nb-queue').innerHTML     = ICON_REQUESTS;
  document.getElementById('nb-dashboard').innerHTML = ICON_DASHBOARD;
  document.getElementById('nb-settings').innerHTML  = ICON_SETTINGS;

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

  updateActiveNav();
  render();
  checkAbsBanner();

  // Apply square covers from ABS library settings (coverAspectRatio 1=square, 0=tall)
  api('/abs/library-settings').then(s => {
    document.body.classList.toggle('square-covers', s.cover_aspect_ratio === 1);
  }).catch(() => {});
});
