const REPOSITORY = 'https://github.com/Conroy1988/missionchief-uk-animated-graphics';
const RAW_REPOSITORY = 'https://raw.githubusercontent.com/Conroy1988/missionchief-uk-animated-graphics';

export const SERVICE_COLOURS = Object.freeze({
  fire: '#ff6b4a',
  ambulance: '#facc15',
  police: '#38bdf8',
  coastguard: '#fb923c',
  lifeboat: '#fb7185',
  'search-and-rescue': '#2dd4bf',
  recovery: '#f59e0b',
  airfield: '#a3e635',
  eod: '#c084fc',
  'multi-service': '#cbd5e1',
});

export const FOCUS_LABELS = Object.freeze({
  'role-differentiation': 'Role differentiation',
  'specialist-equipment': 'Specialist equipment',
  lighting: 'Fixture-aligned lighting',
  'grounding-shadow': 'Contact grounding shadow',
  redraw: 'v1.4 detail redraw',
});

export function normaliseQuery(value) {
  return String(value ?? '')
    .trim()
    .toLocaleLowerCase('en-GB')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

export function filterVehicles(vehicles, filters) {
  const query = normaliseQuery(filters.search);
  const terms = query ? query.split(/\s+/u) : [];
  return vehicles.filter((vehicle) => {
    if (filters.service !== 'all' && vehicle.service !== filters.service) return false;
    if (filters.focus !== 'all' && !vehicle.focus.includes(filters.focus)) return false;
    return terms.every((term) => vehicle.search_text.includes(term));
  });
}

export function sortVehicles(vehicles, sort) {
  const output = [...vehicles];
  const collator = new Intl.Collator('en-GB', { numeric: true, sensitivity: 'base' });
  if (sort === 'name') return output.sort((a, b) => collator.compare(a.label, b.label));
  if (sort === 'service') {
    return output.sort((a, b) => collator.compare(a.service_label, b.service_label) || a.slot - b.slot);
  }
  if (sort === 'size-desc') return output.sort((a, b) => b.width - a.width || a.slot - b.slot);
  if (sort === 'size-asc') return output.sort((a, b) => a.width - b.width || a.slot - b.slot);
  return output.sort((a, b) => a.slot - b.slot);
}

export function historicalAssetUrl(release, vehicle, mode, releases) {
  const releaseData = releases.find((item) => item.id === release);
  if (!releaseData) throw new Error(`Unknown gallery release: ${release}`);
  return `${RAW_REPOSITORY}/${release}/assets/exports/${releaseData.profile}/${mode}/${vehicle.asset_id}.png`;
}

export function currentAssetUrl(vehicle, mode, currentAssetBase) {
  return `${String(currentAssetBase).replace(/\/$/u, '')}/${mode}/${vehicle.asset_id}.png`;
}

export function parseViewState(search, defaults) {
  const params = new URLSearchParams(search);
  const state = { ...defaults };
  const allowed = {
    service: params.get('service'),
    focus: params.get('focus'),
    mode: params.get('mode'),
    map: params.get('map'),
    scale: Number(params.get('scale')),
    comparisonRelease: params.get('release'),
    sort: params.get('sort'),
  };
  state.search = params.get('q') ?? state.search;
  if (allowed.service) state.service = allowed.service;
  if (allowed.focus) state.focus = allowed.focus;
  if (['animated', 'static'].includes(allowed.mode)) state.mode = allowed.mode;
  if (['satellite', 'light', 'dark', 'grayscale'].includes(allowed.map)) state.map = allowed.map;
  if ([100, 75, 50].includes(allowed.scale)) state.scale = allowed.scale;
  if (allowed.comparisonRelease) state.comparisonRelease = allowed.comparisonRelease;
  if (['slot', 'name', 'service', 'size-desc', 'size-asc'].includes(allowed.sort)) state.sort = allowed.sort;
  state.compare = params.get('compare') === '1';
  return state;
}

export function serialiseViewState(state) {
  const params = new URLSearchParams();
  if (state.search) params.set('q', state.search);
  if (state.service !== 'all') params.set('service', state.service);
  if (state.focus !== 'all') params.set('focus', state.focus);
  if (state.mode !== 'animated') params.set('mode', state.mode);
  if (state.map !== 'satellite') params.set('map', state.map);
  if (state.scale !== 100) params.set('scale', String(state.scale));
  if (state.compare) {
    params.set('compare', '1');
    params.set('release', state.comparisonRelease);
  }
  if (state.sort !== 'slot') params.set('sort', state.sort);
  return params.toString();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function initGallery() {
  const root = document.querySelector('[data-fleet-gallery]');
  if (!(root instanceof HTMLElement) || root.dataset.ready === 'true') return;
  root.dataset.ready = 'true';

  const config = {
    catalogueUrl: root.dataset.catalogueUrl || 'vehicles.json',
    currentAssetBase: root.dataset.currentAssetBase || 'assets/exports/command',
  };

  const defaults = {
    search: '',
    service: 'all',
    focus: 'all',
    mode: 'animated',
    playing: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    map: 'satellite',
    scale: 100,
    compare: false,
    comparisonRelease: 'v1.3.0',
    sort: 'slot',
    replay: 0,
  };
  const state = parseViewState(window.location.search, defaults);

  const elements = {
    grid: root.querySelector('#fleet-grid'),
    summary: root.querySelector('#result-summary'),
    search: root.querySelector('#fleet-search'),
    services: root.querySelector('#service-chips'),
    focus: root.querySelector('#focus-filter'),
    sort: root.querySelector('#sort-order'),
    assetMode: root.querySelector('#asset-mode'),
    playback: root.querySelector('#playback-toggle'),
    restart: root.querySelector('#restart-animation'),
    scale: root.querySelector('#scale-mode'),
    map: root.querySelector('#map-mode'),
    compare: root.querySelector('#compare-toggle'),
    compareRelease: root.querySelector('#comparison-release'),
    compareReleaseLabel: root.querySelector('.comparison-release'),
    clear: root.querySelector('#clear-filters'),
    share: root.querySelector('#share-view'),
    empty: root.querySelector('#empty-state'),
  };

  const dialog = document.querySelector('#vehicle-dialog');
  const dialogContent = document.querySelector('#dialog-content');
  const dialogClose = document.querySelector('#dialog-close');
  const randomButton = document.querySelector('#random-vehicle');
  const toast = document.querySelector('#toast');
  let catalogue;
  let toastTimer;

  function notify(message) {
    if (!(toast instanceof HTMLElement)) return;
    toast.textContent = message;
    toast.classList.add('is-visible');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove('is-visible'), 2300);
  }

  function assetUrl(vehicle, mode, release = catalogue.release) {
    const url = release === catalogue.release
      ? currentAssetUrl(vehicle, mode, config.currentAssetBase)
      : historicalAssetUrl(release, vehicle, mode, catalogue.releases);
    return state.replay && mode === 'animated' ? `${url}?replay=${state.replay}` : url;
  }

  function updateAddress() {
    const query = serialiseViewState(state);
    const url = `${window.location.pathname}${query ? `?${query}` : ''}`;
    window.history.replaceState(null, '', url);
  }

  function serviceButtons() {
    const all = `<button class="filter-chip" type="button" data-service="all" aria-pressed="${state.service === 'all'}">All <span>${catalogue.total}</span></button>`;
    const services = catalogue.services.map((service) => (
      `<button class="filter-chip" type="button" data-service="${escapeHtml(service.id)}" aria-pressed="${state.service === service.id}" style="--service-colour:${SERVICE_COLOURS[service.id] || '#67e8f9'}">${escapeHtml(service.label)} <span>${service.count}</span></button>`
    )).join('');
    elements.services.innerHTML = all + services;
  }

  function syncControls() {
    elements.search.value = state.search;
    elements.focus.value = state.focus;
    elements.sort.value = state.sort;
    elements.map.value = state.map;
    elements.compare.checked = state.compare;
    elements.compareRelease.value = state.comparisonRelease;
    elements.compareRelease.disabled = !state.compare;
    elements.compareReleaseLabel.classList.toggle('is-disabled', !state.compare);
    elements.assetMode.querySelectorAll('[data-mode]').forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode));
    });
    elements.scale.querySelectorAll('[data-scale]').forEach((button) => {
      button.setAttribute('aria-pressed', String(Number(button.dataset.scale) === state.scale));
    });
    const paused = !state.playing;
    elements.playback.disabled = state.mode === 'static';
    elements.restart.disabled = state.mode === 'static';
    elements.playback.setAttribute('aria-pressed', String(paused));
    elements.playback.innerHTML = paused
      ? '<span aria-hidden="true">▶</span> Play'
      : '<span aria-hidden="true">Ⅱ</span> Pause';
    serviceButtons();
  }

  function imageMarkup(vehicle, release, label) {
    const mode = state.mode === 'animated' && state.playing ? 'animated' : 'static';
    return `<img loading="lazy" decoding="async" src="${escapeHtml(assetUrl(vehicle, mode, release))}" alt="${escapeHtml(vehicle.label)} ${mode} vehicle graphic, ${escapeHtml(label)}" width="${vehicle.width}" height="${vehicle.height}">`;
  }

  function cardMarkup(vehicle) {
    const cue = vehicle.cue || `${vehicle.frames}-frame map-scale asset`;
    const backgroundClass = `map-${state.map}`;
    const style = `--preview-scale:${state.scale / 100};--service-colour:${SERVICE_COLOURS[vehicle.service] || '#67e8f9'}`;
    let preview = imageMarkup(vehicle, catalogue.release, catalogue.release);
    if (state.compare) {
      preview = `<div class="comparison-grid">
        <div class="compare-pane">${imageMarkup(vehicle, state.comparisonRelease, state.comparisonRelease)}<span class="comparison-label">${escapeHtml(state.comparisonRelease)}</span></div>
        <div class="compare-pane">${imageMarkup(vehicle, catalogue.release, catalogue.release)}<span class="comparison-label">${escapeHtml(catalogue.release)}</span></div>
      </div>`;
    }
    return `<article class="vehicle-card" data-vehicle-id="${escapeHtml(vehicle.id)}" style="${style}">
      <div class="card-topline"><span class="slot-number">SLOT ${String(vehicle.slot).padStart(3, '0')}</span><span class="frame-badge">${vehicle.frames}F</span></div>
      <div class="preview-stage ${backgroundClass}">${preview}</div>
      <div class="card-content">
        <div class="service-line"><span class="service-tag">${escapeHtml(vehicle.service_label)}</span><span class="asset-size">${vehicle.width}×${vehicle.height}px</span></div>
        <h3>${escapeHtml(vehicle.label)}</h3>
        <p class="cue-line">${escapeHtml(cue)}</p>
        <button class="card-action" type="button" data-open-vehicle="${escapeHtml(vehicle.id)}"><span>Inspect unit</span><span aria-hidden="true">↗</span></button>
      </div>
    </article>`;
  }

  function render() {
    if (!catalogue) return;
    const filtered = sortVehicles(filterVehicles(catalogue.vehicles, state), state.sort);
    root.style.setProperty('--preview-scale', String(state.scale / 100));
    elements.grid.innerHTML = filtered.map(cardMarkup).join('');
    elements.grid.setAttribute('aria-busy', 'false');
    elements.grid.hidden = filtered.length === 0;
    elements.empty.hidden = filtered.length !== 0;
    const context = [];
    if (state.service !== 'all') context.push(catalogue.services.find((item) => item.id === state.service)?.label);
    if (state.focus !== 'all') context.push(catalogue.focus_views.find((item) => item.id === state.focus)?.label);
    elements.summary.innerHTML = `<strong>${filtered.length}</strong> of ${catalogue.total} vehicles${context.length ? ` · ${escapeHtml(context.filter(Boolean).join(' · '))}` : ''}`;
    syncControls();
    updateAddress();
  }

  function reset() {
    Object.assign(state, defaults, { replay: Date.now() });
    render();
  }

  function openVehicle(id) {
    const vehicle = catalogue.vehicles.find((item) => item.id === id);
    if (!vehicle || !(dialog instanceof HTMLDialogElement) || !(dialogContent instanceof HTMLElement)) return;
    const mode = state.mode === 'animated' && state.playing ? 'animated' : 'static';
    const focus = vehicle.focus.map((item) => `<li>${escapeHtml(FOCUS_LABELS[item] || item)}</li>`).join('');
    const staticBlob = `${REPOSITORY}/blob/${catalogue.release}/${vehicle.static_path}`;
    const animatedBlob = `${REPOSITORY}/blob/${catalogue.release}/${vehicle.animated_path}`;
    dialogContent.innerHTML = `<div class="dialog-grid" style="--preview-scale:${state.scale / 100};--service-colour:${SERVICE_COLOURS[vehicle.service] || '#67e8f9'}">
      <div class="dialog-preview map-${state.map}">
        <img src="${escapeHtml(assetUrl(vehicle, mode))}" alt="${escapeHtml(vehicle.label)} ${mode} vehicle graphic" width="${vehicle.width}" height="${vehicle.height}">
        <span class="dialog-preview-label">${state.scale}% · ${escapeHtml(state.map)} map simulation</span>
      </div>
      <div class="dialog-copy">
        <p class="eyebrow"><span class="service-tag">${escapeHtml(vehicle.service_label)}</span> · SLOT ${String(vehicle.slot).padStart(3, '0')}</p>
        <h2 id="dialog-title">${escapeHtml(vehicle.label)}</h2>
        <p class="dialog-cue">${escapeHtml(vehicle.cue || 'Validated Modern Command Clarity fleet asset.')}</p>
        <dl class="spec-grid">
          <div><dt>Canvas</dt><dd>${vehicle.width} × ${vehicle.height}px</dd></div>
          <div><dt>Animation</dt><dd>${vehicle.frames} frames</dd></div>
          <div><dt>Real length</dt><dd>${Number(vehicle.real_length_metres).toFixed(1)} metres</dd></div>
          <div><dt>MissionChief ID</dt><dd>${vehicle.edit_index}</dd></div>
        </dl>
        <ul class="focus-list">${focus}</ul>
        <div class="dialog-actions">
          <a class="button button-ghost" href="${escapeHtml(staticBlob)}" target="_blank" rel="noopener noreferrer">Static PNG ↗</a>
          <a class="button button-ghost" href="${escapeHtml(animatedBlob)}" target="_blank" rel="noopener noreferrer">Animated APNG ↗</a>
          <a class="button button-primary" href="${escapeHtml(vehicle.missionchief_url)}" target="_blank" rel="noopener noreferrer">Open MissionChief pack ↗</a>
        </div>
      </div>
    </div>`;
    dialog.showModal();
  }

  elements.search.addEventListener('input', () => {
    state.search = elements.search.value;
    render();
  });
  elements.services.addEventListener('click', (event) => {
    const button = event.target.closest('[data-service]');
    if (!(button instanceof HTMLButtonElement)) return;
    state.service = button.dataset.service || 'all';
    render();
  });
  elements.focus.addEventListener('change', () => { state.focus = elements.focus.value; render(); });
  elements.sort.addEventListener('change', () => { state.sort = elements.sort.value; render(); });
  elements.map.addEventListener('change', () => { state.map = elements.map.value; render(); });
  elements.assetMode.addEventListener('click', (event) => {
    const button = event.target.closest('[data-mode]');
    if (!(button instanceof HTMLButtonElement)) return;
    state.mode = button.dataset.mode;
    if (state.mode === 'animated') state.playing = true;
    state.replay = Date.now();
    render();
  });
  elements.scale.addEventListener('click', (event) => {
    const button = event.target.closest('[data-scale]');
    if (!(button instanceof HTMLButtonElement)) return;
    state.scale = Number(button.dataset.scale);
    render();
  });
  elements.playback.addEventListener('click', () => {
    state.playing = !state.playing;
    state.replay = Date.now();
    render();
  });
  elements.restart.addEventListener('click', () => { state.playing = true; state.replay = Date.now(); render(); });
  elements.compare.addEventListener('change', () => { state.compare = elements.compare.checked; render(); });
  elements.compareRelease.addEventListener('change', () => { state.comparisonRelease = elements.compareRelease.value; render(); });
  elements.clear.addEventListener('click', reset);
  elements.empty.addEventListener('click', (event) => { if (event.target.closest('[data-reset]')) reset(); });
  elements.grid.addEventListener('click', (event) => {
    const button = event.target.closest('[data-open-vehicle]');
    if (button) openVehicle(button.dataset.openVehicle);
  });
  elements.grid.addEventListener('error', (event) => {
    if (!(event.target instanceof HTMLImageElement) || event.target.dataset.failed === 'true') return;
    event.target.dataset.failed = 'true';
    const message = document.createElement('span');
    message.className = 'image-error';
    message.textContent = 'Preview unavailable for this release';
    event.target.parentElement?.append(message);
  }, true);
  elements.share.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      notify('Gallery view link copied');
    } catch {
      notify('Copy was blocked — use the browser address bar');
    }
  });
  dialogClose?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  randomButton?.addEventListener('click', () => {
    if (!catalogue) return;
    const vehicle = catalogue.vehicles[Math.floor(Math.random() * catalogue.vehicles.length)];
    openVehicle(vehicle.id);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
      event.preventDefault();
      elements.search.focus();
    }
  });

  fetch(config.catalogueUrl, { credentials: 'omit' })
    .then((response) => {
      if (!response.ok) throw new Error(`Catalogue request failed: ${response.status}`);
      return response.json();
    })
    .then((data) => {
      if (data.total !== 117 || data.vehicles?.length !== 117) throw new Error('Fleet catalogue is incomplete');
      catalogue = data;
      for (const focus of catalogue.focus_views) {
        elements.focus.insertAdjacentHTML('beforeend', `<option value="${escapeHtml(focus.id)}">${escapeHtml(focus.label)} · ${focus.count}</option>`);
      }
      for (const release of catalogue.releases.filter((item) => item.id !== catalogue.release)) {
        elements.compareRelease.insertAdjacentHTML('beforeend', `<option value="${escapeHtml(release.id)}">${escapeHtml(release.label)} · ${escapeHtml(release.summary)}</option>`);
      }
      if (!catalogue.releases.some((item) => item.id === state.comparisonRelease && item.id !== catalogue.release)) {
        state.comparisonRelease = 'v1.3.0';
      }
      if (state.service !== 'all' && !catalogue.services.some((item) => item.id === state.service)) {
        state.service = 'all';
      }
      if (state.focus !== 'all' && !catalogue.focus_views.some((item) => item.id === state.focus)) {
        state.focus = 'all';
      }
      render();
    })
    .catch((error) => {
      elements.grid.setAttribute('aria-busy', 'false');
      elements.grid.innerHTML = `<div class="empty-state"><h3>Fleet catalogue unavailable</h3><p>${escapeHtml(error.message)}</p></div>`;
      elements.summary.textContent = 'The gallery could not load its canonical vehicle data.';
    });
}

if (typeof document !== 'undefined') {
  initGallery();
  document.addEventListener('astro:page-load', initGallery);
}
