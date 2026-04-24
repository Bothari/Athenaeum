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
      if (reset) tbody.innerHTML = '';
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

  fetchAndAppend(true);
  return {
    reload() { offset = 0; allLoaded = false; fetchAndAppend(true); },
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
      const val = idInput.value.trim();
      if (!val) return;
      this.disabled = true;
      try {
        const resolvedSlug = idInput.dataset.resolvedSlug || '';
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

// ── Shared: renderSeriesCard ───────────────────────────────────────────────────

function renderSeriesCard(series) {
  const el = document.createElement('div');
  el.className = 'entity-card';
  el.innerHTML = `
    <div class="entity-card-name">${escapeHtml(series.name)}</div>
    <div class="entity-card-meta">${series.library_count || 0} book${series.library_count !== 1 ? 's' : ''}${series.requested_count > 0 ? ` <span class="td-dim">(+${series.requested_count})</span>` : ''}</div>
  `;
  el.onclick = () => navigate('/library/series/' + series.id);
  return el;
}

// ── Shared: renderDetailStats ──────────────────────────────────────────────────
// stats: { inLibrary, total, requested, missing, loadingMissing }

function renderDetailStats(name, stats) {
  const missingVal = stats.loadingMissing
    ? `<span class="spin" style="font-size:1.2rem;line-height:1">⟳</span>`
    : (stats.missing != null ? stats.missing : '—');
  return `
    <div class="card mb-2">
      <div class="stats-row" style="margin-bottom:0">
        <div class="stat-card">
          <div class="stat-value">${stats.inLibrary || 0}</div>
          <div class="stat-label">In library</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.requested || 0}</div>
          <div class="stat-label">Requested</div>
        </div>
        <div class="stat-card" id="series-stat-missing">
          <div class="stat-value">${missingVal}</div>
          <div class="stat-label">Missing</div>
        </div>
      </div>
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
      narrator: req ? (req.narrator || '') : '',
      reqId: req ? (req.id || null) : null,
      libNarrator: lib ? (lib.narrator || '') : '',
    };
  }

  function render() {
    const ab = state['audiobook'];
    const eb = state['ebook'];

    function pill(type) {
      const s = state[type];
      const typeName = type === 'audiobook' ? 'Audiobook' : 'Ebook';
      const tips = { 'in-library': `${typeName} — in library`, 'requested': `${typeName} — click to cancel`, 'unmonitored': `${typeName} — click to request` };
      const badgeClass = s.mode === 'in-library' ? 'badge-in_library' : s.mode === 'requested' ? 'badge-requested' : 'badge-unmonitored';
      return `<button class="badge ${badgeClass} fmt-pill" data-type="${type}" title="${tips[s.mode]}"${s.mode === 'in-library' ? ' disabled' : ''}>${typeIcon(type)}</button>`;
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

        if (!bookId) {
          const book = await api('/books', { method: 'POST', body: {
            title: result.title, author: result.author,
            cover_url: result.cover_url || null,
            series: result.series?.[0]?.name || null,
            series_position: result.series?.[0]?.position || null,
            metadata_source: result.metadata_source || null,
            metadata_id: result.metadata_id || null,
            metadata_url: result.metadata_url || null,
            hardcover_slug: result.slug || null,
          }});
          result.book_id = book.id;
          bookId = book.id;
          const bookUrl = buildHash('/library/book', { book_id: bookId });
          card.querySelectorAll('.search-card-cover-link, .search-card-title-link').forEach(a => { a.href = bookUrl; });
        }

        const req = await api('/requests', { method: 'POST', body: { book_id: bookId, type, narrator: narratorVal } });
        if (req.skipped) toast('Already requested', 'info');
        s.reqId = req.id || null;
        s.mode = 'requested';
        render();
        if (onRequestSuccess) onRequestSuccess({ id: bookId }, result, [type]);
      } catch (err) {
        toast('Request failed: ' + err.message, 'error');
        dot.disabled = false;
      }

    } else if (s.mode === 'requested') {
      if (!s.reqId) { toast('Cannot cancel — unknown request ID', 'warning'); dot.disabled = false; return; }
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
      app.innerHTML = `<div class="narrow-page">
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
      </div>`;
      document.getElementById('vt-poster').onclick = () => { localStorage.setItem('detail_view', 'poster'); renderAuthorBooksView(); };
      document.getElementById('vt-list').onclick   = () => { localStorage.setItem('detail_view', 'list');   renderAuthorBooksView(); };

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
    renderAuthorBooksView();
  } catch (err) {
    renderError(app, render);
  }
});

// Library: Series list
route('/library/series', async () => {
  app.innerHTML = `<div class="narrow-page">
    <div class="page-header"><span class="page-title">${ICON_SERIES} Series</span></div>
    <div id="series-content"></div>
  </div>`;
  const content = document.getElementById('series-content');
  let seriesUnlinked = false;
  const seriesTable = renderTable({
    container: content,
    stateKey: 'series',
    headers: [
      { label: 'Name', key: 'name', sortable: true },
      { label: 'Books', key: 'library_count', sortable: true, style: 'width:80px' },
    ],
    fetchFn: (p) => api('/series?' + new URLSearchParams(p).toString()),
    extraFetchParams: () => seriesUnlinked ? { unlinked: '1' } : {},
    extraControls: `<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.875rem;white-space:nowrap;cursor:pointer"><input type="checkbox" id="series-unlinked-cb"> Unlinked only</label>`,
    renderRow: (s) => `
      <td><a href="#/library/series/${s.id}">${escapeHtml(s.name)}</a></td>
      <td class="td-dim">${s.library_count || 0}${s.requested_count > 0 ? ` <span style="opacity:0.6">(+${s.requested_count})</span>` : ''}</td>
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
        <div id="series-stats">${renderDetailStats(seriesName, { inLibrary, total: booksData.length, requested, loadingMissing: true })}</div>
        <div class="section-heading">Books in Library</div>
        <div id="series-books"></div>
        <div id="series-missing-section"></div>
        <div id="series-hc-section" class="mt-2"></div>
        <div id="series-debug-section"></div>
      </div>`;
      document.getElementById('vt-poster').onclick = () => { localStorage.setItem('detail_view', 'poster'); renderSeriesBooksView(); loadSeriesExtras(); loadMissing(); };
      document.getElementById('vt-list').onclick   = () => { localStorage.setItem('detail_view', 'list');   renderSeriesBooksView(); loadSeriesExtras(); loadMissing(); };

      const booksContainer = document.getElementById('series-books');
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
        const missingCard = document.getElementById('series-stat-missing');
        if (missingCard) {
          const count = (data.items && !data.error) ? data.items.length : null;
          missingCard.querySelector('.stat-value').textContent = count != null ? String(count) : '—';
        }
        if (data.error || !data.items || !data.items.length) {
          sec.innerHTML = data.items && !data.items.length
            ? `<div class="section-heading mt-2">Missing from Series</div><p class="td-dim" style="padding:0.5rem 0">All books accounted for.</p>`
            : '';
          return;
        }
        const label = `Missing from Series (${data.items.length}${data.truncated ? '+' : ''})`;
        sec.innerHTML = `<div class="section-heading mt-2">${label}</div>`;
        data.items.forEach(result => {
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
          sec.appendChild(card);
        });
      } catch {
        sec.innerHTML = '';
        const missingCard = document.getElementById('series-stat-missing');
        if (missingCard) missingCard.querySelector('.stat-value').textContent = '—';
      }
    }

    loadSeriesExtras();
    loadMissing();
  } catch (err) {
    renderError(app, render);
  }
});

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
        ? 'badge-unmonitored'
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
  results.forEach(res => {
    const fmtMatch = (res.title || '').match(/\b(mp3|m4b|m4a|flac|opus|ogg|aac|epub|mobi|azw3?|pdf)\b/i);
    const fmt = fmtMatch ? fmtMatch[1].toUpperCase() : '';
    const row = document.createElement('div');
    row.className = 'prowlarr-result-row';
    row.innerHTML = `
      <div class="prowlarr-result-title">${escapeHtml(res.title || '—')}</div>
      <div class="prowlarr-result-meta">
        <div class="prowlarr-result-info">
          ${fmt ? `<span class="badge" style="background:var(--surface2);color:var(--text)">${fmt}</span>` : ''}
          <span>${res.protocol === 'torrent' ? 'Torrent' : 'Usenet'}</span>
          <span>${formatBytes(res.size)}</span>
          ${res.seeders != null ? `<span>${res.seeders}S</span>` : ''}
          <span>${escapeHtml(res.indexer || '—')}</span>
        </div>
        <button class="btn btn-primary btn-sm prowlarr-dl-btn" style="flex-shrink:0">${ICON_DOWNLOAD}<span class="prowlarr-dl-label"> Download</span></button>
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
    const canSearch = ['requested', 'failed', 'completed'].includes(req.status);
    container.innerHTML = `
      <div class="detail-fmt-detail">
        <div class="detail-fmt-kv"><span class="td-dim">Status</span> <span class="badge badge-${req.status}">${escapeHtml(req.status)}</span></div>
        <div class="detail-fmt-actions">
          ${canSearch ? `<button class="btn btn-primary btn-sm detail-fmt-search">${ICON_SEARCH} Search Prowlarr</button>` : ''}
          <button class="btn btn-secondary btn-sm detail-fmt-cancel">Cancel</button>
        </div>
        <div class="detail-fmt-search-results mt-1"></div>
      </div>
    `;
    container.querySelector('.detail-fmt-cancel').onclick = async () => {
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
      return s.id ? `<a href="#/library/series/${s.id}" class="detail-link">${label}</a>` : label;
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
            ${book.release_date ? `<div class="detail-release-date td-dim">${book.release_date >= new Date().toISOString().slice(0,10) ? '<span class="badge badge-unmonitored">Unreleased</span> ' : ''}${book.release_date}</div>` : ''}
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

// Queue (Requests + Downloads tabs)
route('/requests', async (params, qp) => {
  const tab = qp.tab === 'downloads' ? 'downloads' : 'requests';

  app.innerHTML = `<div class="narrow-page">
    <div class="page-header">
      <span class="page-title">${ICON_REQUESTS} Queue</span>
      <button class="btn btn-primary btn-sm" id="search-all-btn">Search all</button>
    </div>
    <div class="tabs">
      <button class="tab-btn${tab === 'requests' ? ' active' : ''}" data-tab="requests">Requests</button>
      <button class="tab-btn${tab === 'downloads' ? ' active' : ''}" data-tab="downloads">Downloads</button>
    </div>
    <div id="queue-content"></div>
  </div>`;

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
        <td><a href="#/library/book?book_id=${r.book_id}">${escapeHtml(r.book_title || r.title || '—')}</a>${r.release_date && r.release_date >= new Date().toISOString().slice(0,10) ? ` <span class="badge badge-unmonitored" title="Releases ${r.release_date}">Unreleased</span>` : ''}</td>
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
          tr.nextElementSibling?.classList.contains('search-expansion-row') && tr.nextElementSibling.remove();
          tr.remove();
          toast('Request deleted.');
        }
      )();
    },
    emptyMessage: statusFilter ? `No ${statusFilter} requests.` : 'No requests yet.',
  });

  // Allow expansion rows to overflow the scroll container on mobile
  content.querySelector('.table-wrap')?.style.setProperty('overflow-x', 'visible');

  // Search all — fires individual searches per row, results expand inline
  document.getElementById('search-all-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('search-all-btn');
    document.querySelectorAll('.search-expansion-row').forEach(r => r.remove());

    const requestedRows = [...document.querySelectorAll('tr[data-req-status="requested"]')];
    if (!requestedRows.length) { toast('No requested items.'); return; }

    btn.disabled = true; btn.textContent = 'Searching…';

    const today = new Date().toISOString().slice(0, 10);

    function makeExpansion(tr) {
      const expRow = document.createElement('tr');
      expRow.className = 'search-expansion-row';
      const expCell = document.createElement('td');
      expCell.colSpan = 999;
      expCell.className = 'search-expansion-cell';
      const expDiv = document.createElement('div');
      expDiv.className = 'search-expansion';
      expRow.appendChild(expCell);
      expCell.appendChild(expDiv);
      tr.after(expRow);
      return expDiv;
    }

    // Build expansion rows immediately — unreleased skipped, others show spinner
    const toSearch = [];
    requestedRows.forEach(tr => {
      const expDiv = makeExpansion(tr);
      const rd = tr.dataset.releaseDate;
      if (rd && rd > today) {
        expDiv.innerHTML = `<span class="text-dim">Skipped — unreleased${rd ? ` (releases ${rd})` : ''}</span>`;
      } else {
        expDiv.innerHTML = `<span class="text-dim">${ICON_SPINNER} Searching…</span>`;
        toSearch.push({ tr, expDiv, reqId: tr.dataset.requestId });
      }
    });

    // Search concurrently, max 3 at a time
    const sem = 3;
    let idx = 0;
    async function worker() {
      while (idx < toSearch.length) {
        const { expDiv, reqId } = toSearch[idx++];
        try {
          const data = await api(`/requests/${reqId}/search-indexers`, { method: 'POST' });
          if (data.error) {
            expDiv.innerHTML = `<span class="text-dim">${escapeHtml(data.error)}</span>`;
          } else {
            renderProwlarrResults(expDiv, data.results || [], reqId, null);
          }
        } catch {
          expDiv.innerHTML = `<span class="text-dim">Search failed.</span>`;
        }
      }
    }
    await Promise.all(Array.from({ length: Math.min(sem, toSearch.length) }, worker));

    btn.disabled = false; btn.textContent = 'Search all';
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
              <div class="progress-bar-fill" style="width:${Math.round(dl.progress)}%"></div>
            </div>
            <div class="text-dim mt-1" style="font-size:0.78rem">
              ${Math.round(dl.progress)}%
              ${dl.eta ? ' · ETA ' + dl.eta : ''}
              ${dl.speed ? ' · ' + formatBytes(dl.speed) + '/s' : ''}
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
      <div class="tasks-list" id="dash-tasks"></div>
    </div>`;

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
          ${!disabled && (t.last_result || t.running) ? `<div class="${t.running ? 'text-dim' : resultClass}" style="font-size:0.78rem;margin-top:0.2rem" id="dash-task-result-${key}">${escapeHtml(t.last_result || '')}</div>` : `<div id="dash-task-result-${key}"></div>`}
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
          resultEl.className = t.running ? 'text-dim' : resultClass;
          resultEl.style.fontSize = '0.78rem';
          resultEl.style.marginTop = '0.2rem';
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

    app.innerHTML = `<div class="narrow-page">
      <div class="page-header"><span class="page-title">${ICON_SETTINGS} Settings</span></div>
      <div class="tabs-wrap">
        <div class="tabs">
          ${tabs.map((t, i) => `<button class="tab-btn${i === 0 ? ' active' : ''}" data-tab="${t}">${t}</button>`).join('')}
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
