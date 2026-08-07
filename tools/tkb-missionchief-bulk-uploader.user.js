// ==UserScript==
// @name         TKB MissionChief UK Graphics Bulk Uploader
// @namespace    https://github.com/Conroy1988/missionchief-uk-animated-graphics
// @version      1.2.0
// @description  Uploads the numbered TKB UK Emergency Fleet static and animated graphics to MissionChief pack 5897, including the Modern Command Clarity profile.
// @author       TKB Gaming
// @match        https://www.missionchief.co.uk/vehicle_graphics/5897/edit*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(() => {
  'use strict';

  const PACK_ID = 5897;
  const EXPECTED_SLOTS = 117;
  const STORAGE_KEY = `tkb-mc-graphics-uploader-${PACK_ID}`;
  const EDIT_LINK_RE = new RegExp(`/vehicle_graphics/${PACK_ID}/vehicle_graphic_images/(\\d+)/edit(?:$|[?#])`);
  const FILE_RE = /^(\d{3})\s+-\s+.+\.png$/i;
  const RESPONSE_WORDS = /sonder|special|emergency|response|blue|light|rights|animated|animation|apng/i;
  const NORMAL_WORDS = /normal|without|station|standby|regular|default/i;
  const APNG_WORDS = /apng|animated|animation/i;
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  let selectedFiles = null;
  let liveSlots = [];
  let formProfile = null;
  let running = false;
  let stopRequested = false;

  const state = loadState();

  function loadState() {
    try {
      return {
        nextSlot: 1,
        completed: [],
        ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'),
      };
    } catch {
      return { nextSlot: 1, completed: [] };
    }
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function normalisePath(path) {
    return String(path || '').replace(/\\/g, '/');
  }

  function slotFromFilename(name) {
    const match = String(name || '').match(FILE_RE);
    return match ? Number(match[1]) : null;
  }

  function fieldDescriptor(input) {
    const id = input.id || '';
    const label = id ? input.ownerDocument.querySelector(`label[for="${CSS.escape(id)}"]`) : null;
    const container = input.closest('.form-group, .mb-3, .row, fieldset, .control-group, div');
    return [
      input.name,
      id,
      input.getAttribute('aria-label'),
      input.getAttribute('title'),
      label?.textContent,
      container?.textContent?.slice(0, 350),
    ]
      .filter(Boolean)
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function isLoginResponse(response, text) {
    return /\/users\/(sign_in|login)/i.test(response.url) || /name=["']user\[(email|login|password)\]/i.test(text);
  }

  function uniqueByName(inputs) {
    const seen = new Set();
    return inputs.filter((input) => {
      if (!input.name || seen.has(input.name)) return false;
      seen.add(input.name);
      return true;
    });
  }

  function classifyForm(documentNode, editUrl) {
    const forms = [...documentNode.querySelectorAll('form')];
    const form =
      forms.find((candidate) => candidate.querySelectorAll('input[type="file"][name]').length >= 2) ||
      forms.find((candidate) => candidate.querySelector('input[type="file"][name]'));

    if (!form) throw new Error(`No upload form found at ${editUrl}`);

    const fileInputs = uniqueByName([...form.querySelectorAll('input[type="file"][name]')]);
    if (fileInputs.length < 2) {
      throw new Error(`Expected two file fields at ${editUrl}; found ${fileInputs.length}`);
    }

    const described = fileInputs.map((input) => ({ input, text: fieldDescriptor(input) }));

    let animated = described.find(({ input }) => /image_sonderrechtes/i.test(input.name));
    let normal = described.find(({ input }) => /\[image\]$|\[image\](?:\[|$)|(^|_)image$/i.test(input.name) && !/sonder/i.test(input.name));

    animated ||= described.find(({ text }) => RESPONSE_WORDS.test(text));
    normal ||= described.find(({ text }) => !RESPONSE_WORDS.test(text));

    if (!normal || !animated || normal.input.name === animated.input.name) {
      normal = described[0];
      animated = described[1];
    }

    const checkboxInputs = uniqueByName([...form.querySelectorAll('input[type="checkbox"][name]')]);
    const apngCheckboxes = checkboxInputs
      .map((input) => ({ input, text: fieldDescriptor(input) }))
      .filter(({ text }) => APNG_WORDS.test(text));

    let animatedApng = apngCheckboxes.find(({ text }) => RESPONSE_WORDS.test(text));
    let normalApng = apngCheckboxes.find(({ text }) => NORMAL_WORDS.test(text) && !RESPONSE_WORDS.test(text));

    if (!animatedApng && apngCheckboxes.length === 1) animatedApng = apngCheckboxes[0];
    if (!animatedApng && apngCheckboxes.length >= 2) animatedApng = apngCheckboxes[1];
    if (!normalApng && apngCheckboxes.length >= 2) {
      normalApng = apngCheckboxes.find(({ input }) => input.name !== animatedApng?.input.name) || apngCheckboxes[0];
    }

    const action = new URL(form.getAttribute('action') || editUrl, window.location.origin).href;
    const method = (form.getAttribute('method') || 'post').toUpperCase();

    return {
      form,
      action,
      method,
      normalField: normal.input.name,
      animatedField: animated.input.name,
      normalApngField: normalApng?.input.name || null,
      animatedApngField: animatedApng?.input.name || null,
      fileFieldSummary: described.map(({ input, text }) => ({ name: input.name, text })),
      apngFieldSummary: apngCheckboxes.map(({ input, text }) => ({ name: input.name, value: input.value, text })),
    };
  }

  async function fetchEditForm(editUrl) {
    const response = await fetch(editUrl, {
      credentials: 'same-origin',
      cache: 'no-store',
      headers: { Accept: 'text/html,application/xhtml+xml' },
    });
    const text = await response.text();
    if (!response.ok) throw new Error(`GET ${editUrl} returned HTTP ${response.status}`);
    if (isLoginResponse(response, text)) throw new Error('MissionChief session is not logged in or has expired.');
    const documentNode = new DOMParser().parseFromString(text, 'text/html');
    return classifyForm(documentNode, editUrl);
  }

  function collectLiveSlots() {
    const candidates = [...document.querySelectorAll(`a[href*="/vehicle_graphics/${PACK_ID}/vehicle_graphic_images/"][href*="/edit"]`)];
    const byIndex = new Map();

    for (const link of candidates) {
      const url = new URL(link.href, window.location.origin);
      const match = `${url.pathname}${url.search}${url.hash}`.match(EDIT_LINK_RE);
      if (!match) continue;
      const editIndex = Number(match[1]);
      const row = link.closest('tr');
      const label = row?.querySelector('td:first-child')?.textContent?.trim() || `Slot ${editIndex + 1}`;
      byIndex.set(editIndex, {
        slot: editIndex + 1,
        editIndex,
        label,
        editUrl: url.href,
      });
    }

    const result = [...byIndex.values()].sort((a, b) => a.editIndex - b.editIndex);
    if (result.length !== EXPECTED_SLOTS) {
      throw new Error(`Expected ${EXPECTED_SLOTS} live edit links; found ${result.length}.`);
    }

    const sequence = result.map((item) => item.editIndex);
    for (let index = 0; index < EXPECTED_SLOTS; index += 1) {
      if (sequence[index] !== index) throw new Error(`Live edit-index sequence is incomplete at ${index}.`);
    }
    return result;
  }

  function collectSelectedFiles(fileList) {
    const staticFiles = new Map();
    const animatedFiles = new Map();

    for (const file of [...fileList]) {
      const path = normalisePath(file.webkitRelativePath || file.name);
      const slot = slotFromFilename(file.name);
      if (!slot) continue;

      if (/(^|\/)01\s+-\s+Static\//i.test(path)) staticFiles.set(slot, file);
      if (/(^|\/)02\s+-\s+Animated\//i.test(path)) animatedFiles.set(slot, file);
    }

    const missing = [];
    for (let slot = 1; slot <= EXPECTED_SLOTS; slot += 1) {
      if (!staticFiles.has(slot)) missing.push(`static ${String(slot).padStart(3, '0')}`);
      if (!animatedFiles.has(slot)) missing.push(`animated ${String(slot).padStart(3, '0')}`);
    }

    if (missing.length) {
      throw new Error(`Selected folder is incomplete. Missing: ${missing.slice(0, 12).join(', ')}${missing.length > 12 ? '…' : ''}`);
    }

    if (staticFiles.size !== EXPECTED_SLOTS || animatedFiles.size !== EXPECTED_SLOTS) {
      throw new Error(`Expected ${EXPECTED_SLOTS} static and ${EXPECTED_SLOTS} animated files.`);
    }

    return { staticFiles, animatedFiles };
  }

  function setStatus(message, tone = 'neutral') {
    ui.status.textContent = message;
    ui.status.dataset.tone = tone;
  }

  function log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.className = `tkb-log-${type}`;
    line.textContent = `[${timestamp}] ${message}`;
    ui.log.append(line);
    ui.log.scrollTop = ui.log.scrollHeight;
    console[type === 'error' ? 'error' : type === 'warn' ? 'warn' : 'log'](`[TKB uploader] ${message}`);
  }

  function updateProgress(slot, message) {
    const bounded = Math.max(0, Math.min(EXPECTED_SLOTS, slot));
    ui.progress.value = bounded;
    ui.progressText.textContent = `${bounded} / ${EXPECTED_SLOTS}${message ? ` — ${message}` : ''}`;
  }

  function resetPreflight() {
    formProfile = null;
    ui.start.disabled = true;
    ui.preflight.disabled = !selectedFiles;
  }

  async function runPreflight() {
    if (!selectedFiles) throw new Error('Select the extracted numbered upload package first.');
    ui.preflight.disabled = true;
    ui.start.disabled = true;
    setStatus('Running live preflight…');
    log('Checking the current MissionChief pack editor and first upload form.');

    liveSlots = collectLiveSlots();
    const first = liveSlots[0];
    formProfile = await fetchEditForm(first.editUrl);

    if (formProfile.normalField === formProfile.animatedField) {
      throw new Error('Preflight could not distinguish the normal and response image fields.');
    }

    log(`Live slot mapping confirmed: edit indices 0–${EXPECTED_SLOTS - 1}.`);
    log(`Normal field: ${formProfile.normalField}`);
    log(`Response field: ${formProfile.animatedField}`);
    if (formProfile.animatedApngField) log(`Response APNG flag: ${formProfile.animatedApngField}`);
    else log('No APNG checkbox was found; MissionChief may auto-detect APNG on this form.', 'warn');

    ui.start.disabled = false;
    ui.preflight.disabled = false;
    setStatus('Preflight passed. Ready to upload.', 'success');
  }

  function checkboxValue(profile, fieldName) {
    const match = profile.apngFieldSummary.find((field) => field.name === fieldName);
    return match?.value || '1';
  }

  function makeSubmission(profile, staticFile, animatedFile) {
    const formData = new FormData(profile.form);

    formData.set(profile.normalField, staticFile, staticFile.name);
    formData.set(profile.animatedField, animatedFile, animatedFile.name);

    if (profile.normalApngField) formData.delete(profile.normalApngField);
    if (profile.animatedApngField) {
      formData.delete(profile.animatedApngField);
      formData.set(profile.animatedApngField, checkboxValue(profile, profile.animatedApngField));
    }

    return formData;
  }

  async function submitSlot(liveSlot, staticFile, animatedFile, attempt = 1) {
    try {
      const profile = await fetchEditForm(liveSlot.editUrl);
      const formData = makeSubmission(profile, staticFile, animatedFile);
      const csrfToken = profile.form.querySelector('input[name="authenticity_token"]')?.value ||
        document.querySelector('meta[name="csrf-token"]')?.content || '';

      const headers = { Accept: 'text/html,application/xhtml+xml' };
      if (csrfToken) headers['X-CSRF-Token'] = csrfToken;

      const response = await fetch(profile.action, {
        method: profile.method,
        body: formData,
        credentials: 'same-origin',
        redirect: 'follow',
        cache: 'no-store',
        headers,
      });
      const text = await response.text();

      if (isLoginResponse(response, text)) throw new Error('MissionChief session expired during upload.');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const responseDocument = new DOMParser().parseFromString(text, 'text/html');
      const validationErrors = [
        ...responseDocument.querySelectorAll('.alert-danger, .alert-error, .field_with_errors, .has-error'),
      ]
        .map((element) => element.textContent.trim())
        .filter(Boolean)
        .join(' | ');

      if (validationErrors) throw new Error(`MissionChief validation error: ${validationErrors.slice(0, 500)}`);
      return;
    } catch (error) {
      if (attempt < 3 && !stopRequested) {
        log(`Slot ${String(liveSlot.slot).padStart(3, '0')} failed (${error.message}); retrying ${attempt + 1}/3.`, 'warn');
        await delay(1500 * attempt);
        return submitSlot(liveSlot, staticFile, animatedFile, attempt + 1);
      }
      throw error;
    }
  }

  async function startUpload() {
    if (running) return;
    if (!selectedFiles || !formProfile || liveSlots.length !== EXPECTED_SLOTS) {
      await runPreflight();
    }

    const requestedStart = Number(ui.startSlot.value);
    if (!Number.isInteger(requestedStart) || requestedStart < 1 || requestedStart > EXPECTED_SLOTS) {
      throw new Error(`Start slot must be between 1 and ${EXPECTED_SLOTS}.`);
    }

    running = true;
    stopRequested = false;
    ui.start.disabled = true;
    ui.preflight.disabled = true;
    ui.folder.disabled = true;
    ui.stop.disabled = false;
    setStatus('Uploading…');

    try {
      for (let slot = requestedStart; slot <= EXPECTED_SLOTS; slot += 1) {
        if (stopRequested) {
          setStatus(`Paused before slot ${String(slot).padStart(3, '0')}.`, 'warn');
          log(`Paused. Resume from slot ${String(slot).padStart(3, '0')}.`, 'warn');
          state.nextSlot = slot;
          saveState();
          ui.startSlot.value = String(slot);
          return;
        }

        const liveSlot = liveSlots[slot - 1];
        const staticFile = selectedFiles.staticFiles.get(slot);
        const animatedFile = selectedFiles.animatedFiles.get(slot);
        const display = `${String(slot).padStart(3, '0')} — ${liveSlot.label}`;
        updateProgress(slot - 1, `uploading ${display}`);
        log(`Uploading ${display}.`);

        await submitSlot(liveSlot, staticFile, animatedFile);

        if (!state.completed.includes(slot)) state.completed.push(slot);
        state.nextSlot = slot + 1;
        saveState();
        ui.startSlot.value = String(Math.min(EXPECTED_SLOTS, slot + 1));
        updateProgress(slot, `completed ${display}`);
        log(`Completed ${display}.`, 'success');
        await delay(650);
      }

      state.nextSlot = EXPECTED_SLOTS + 1;
      saveState();
      setStatus('All 117 slots uploaded successfully.', 'success');
      updateProgress(EXPECTED_SLOTS, 'complete');
      log('All 117 static and animated vehicle pairs were submitted.', 'success');
    } finally {
      running = false;
      ui.start.disabled = false;
      ui.preflight.disabled = false;
      ui.folder.disabled = false;
      ui.stop.disabled = true;
    }
  }

  function resetProgress() {
    if (running) return;
    state.nextSlot = 1;
    state.completed = [];
    saveState();
    ui.startSlot.value = '1';
    updateProgress(0, 'reset');
    setStatus(selectedFiles ? 'Package selected; run preflight.' : 'Select the extracted numbered package.');
    log('Saved upload progress reset.');
  }

  function installStyles() {
    const style = document.createElement('style');
    style.textContent = `
      #tkb-mc-uploader { position: fixed; right: 18px; bottom: 18px; z-index: 2147483647; width: min(440px, calc(100vw - 36px)); background: #11131a; color: #f5f7fb; border: 1px solid #714cff; border-radius: 14px; box-shadow: 0 18px 55px rgba(0,0,0,.45); font: 13px/1.4 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; overflow: hidden; }
      #tkb-mc-uploader * { box-sizing: border-box; }
      #tkb-mc-uploader header { padding: 12px 14px; background: linear-gradient(135deg,#311b68,#171424); display:flex; justify-content:space-between; align-items:center; }
      #tkb-mc-uploader header strong { font-size: 14px; }
      #tkb-mc-uploader .tkb-body { padding: 12px; display:grid; gap:10px; }
      #tkb-mc-uploader button, #tkb-mc-uploader input[type="number"] { border: 1px solid #4c5265; background:#202430; color:#fff; border-radius:8px; min-height:34px; padding:6px 10px; }
      #tkb-mc-uploader button { cursor:pointer; font-weight:650; }
      #tkb-mc-uploader button:hover:not(:disabled) { border-color:#9b82ff; background:#292e3e; }
      #tkb-mc-uploader button:disabled { opacity:.42; cursor:not-allowed; }
      #tkb-mc-uploader .tkb-primary { background:#6c4cff; border-color:#8c76ff; }
      #tkb-mc-uploader .tkb-danger { background:#5b2630; border-color:#a94b5c; }
      #tkb-mc-uploader .tkb-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
      #tkb-mc-uploader .tkb-inline { display:flex; gap:8px; align-items:center; }
      #tkb-mc-uploader .tkb-inline label { white-space:nowrap; }
      #tkb-mc-uploader #tkb-start-slot { width:76px; }
      #tkb-mc-uploader #tkb-status { padding:8px 10px; border-radius:8px; background:#1d212c; border-left:3px solid #6d7385; }
      #tkb-mc-uploader #tkb-status[data-tone="success"] { border-left-color:#3ddc97; }
      #tkb-mc-uploader #tkb-status[data-tone="warn"] { border-left-color:#ffb84d; }
      #tkb-mc-uploader #tkb-status[data-tone="error"] { border-left-color:#ff6377; }
      #tkb-mc-uploader progress { width:100%; height:14px; accent-color:#7658ff; }
      #tkb-mc-uploader #tkb-progress-text { color:#c7ccda; font-size:12px; }
      #tkb-mc-uploader #tkb-log { height:150px; overflow:auto; padding:8px; border-radius:8px; background:#090b10; color:#c7ccda; font:11px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace; }
      #tkb-mc-uploader #tkb-log div { margin-bottom:3px; overflow-wrap:anywhere; }
      #tkb-mc-uploader .tkb-log-success { color:#6de7ad; }
      #tkb-mc-uploader .tkb-log-warn { color:#ffc466; }
      #tkb-mc-uploader .tkb-log-error { color:#ff8292; }
      #tkb-mc-uploader .tkb-muted { color:#aeb4c4; font-size:11px; }
      #tkb-mc-uploader details summary { cursor:pointer; color:#c4b8ff; }
    `;
    document.head.append(style);
  }

  function buildUi() {
    installStyles();
    const panel = document.createElement('section');
    panel.id = 'tkb-mc-uploader';
    panel.innerHTML = `
      <header><strong>TKB Graphics Bulk Uploader</strong><span>Pack ${PACK_ID}</span></header>
      <div class="tkb-body">
        <div id="tkb-status">Select the extracted numbered package.</div>
        <input id="tkb-folder-input" type="file" accept=".png,image/png" webkitdirectory multiple hidden>
        <button id="tkb-folder" type="button">1. Select numbered package folder</button>
        <div class="tkb-grid">
          <button id="tkb-preflight" type="button" disabled>2. Run live preflight</button>
          <button id="tkb-start" class="tkb-primary" type="button" disabled>3. Start upload</button>
        </div>
        <div class="tkb-inline">
          <label for="tkb-start-slot">Start/resume at slot</label>
          <input id="tkb-start-slot" type="number" min="1" max="${EXPECTED_SLOTS}" value="${Math.min(EXPECTED_SLOTS, Math.max(1, state.nextSlot || 1))}">
          <button id="tkb-stop" class="tkb-danger" type="button" disabled>Pause</button>
          <button id="tkb-reset" type="button">Reset</button>
        </div>
        <progress id="tkb-progress" max="${EXPECTED_SLOTS}" value="${Math.min(EXPECTED_SLOTS, state.completed.length)}"></progress>
        <div id="tkb-progress-text">${Math.min(EXPECTED_SLOTS, state.completed.length)} / ${EXPECTED_SLOTS}</div>
        <details>
          <summary>Activity log</summary>
          <div id="tkb-log"></div>
        </details>
        <div class="tkb-muted">Runs only on the authenticated pack 5897 edit page. Images remain in your browser and are sent directly to MissionChief.</div>
      </div>
    `;
    document.body.append(panel);

    const refs = {
      panel,
      status: panel.querySelector('#tkb-status'),
      fileInput: panel.querySelector('#tkb-folder-input'),
      folder: panel.querySelector('#tkb-folder'),
      preflight: panel.querySelector('#tkb-preflight'),
      start: panel.querySelector('#tkb-start'),
      stop: panel.querySelector('#tkb-stop'),
      reset: panel.querySelector('#tkb-reset'),
      startSlot: panel.querySelector('#tkb-start-slot'),
      progress: panel.querySelector('#tkb-progress'),
      progressText: panel.querySelector('#tkb-progress-text'),
      log: panel.querySelector('#tkb-log'),
    };

    refs.folder.addEventListener('click', () => refs.fileInput.click());
    refs.fileInput.addEventListener('change', () => {
      try {
        selectedFiles = collectSelectedFiles(refs.fileInput.files);
        resetPreflight();
        refs.preflight.disabled = false;
        setStatus(`Package selected: ${EXPECTED_SLOTS} static and ${EXPECTED_SLOTS} animated files.`, 'success');
        log(`Selected and validated ${EXPECTED_SLOTS * 2} numbered PNG/APNG files.`);
      } catch (error) {
        selectedFiles = null;
        resetPreflight();
        setStatus(error.message, 'error');
        log(error.message, 'error');
      }
    });
    refs.preflight.addEventListener('click', () => runPreflight().catch((error) => {
      refs.preflight.disabled = false;
      setStatus(error.message, 'error');
      log(error.message, 'error');
    }));
    refs.start.addEventListener('click', () => startUpload().catch((error) => {
      running = false;
      refs.start.disabled = false;
      refs.preflight.disabled = false;
      refs.folder.disabled = false;
      refs.stop.disabled = true;
      setStatus(error.message, 'error');
      log(error.message, 'error');
    }));
    refs.stop.addEventListener('click', () => {
      stopRequested = true;
      refs.stop.disabled = true;
      setStatus('Pause requested; finishing the current slot…', 'warn');
    });
    refs.reset.addEventListener('click', resetProgress);
    return refs;
  }

  if (window.location.pathname !== `/vehicle_graphics/${PACK_ID}/edit`) return;
  const ui = buildUi();
  log('Uploader loaded. Select the extracted numbered package folder.');
})();
