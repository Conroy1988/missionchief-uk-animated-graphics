import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  currentAssetUrl,
  filterVehicles,
  historicalAssetUrl,
  normaliseQuery,
  parseViewState,
  serialiseViewState,
  sortVehicles,
} from '../gallery/app.mjs';

const root = new URL('../', import.meta.url);
const catalogue = JSON.parse(await readFile(new URL('gallery/vehicles.json', root), 'utf8'));
const defaults = {
  search: '',
  service: 'all',
  focus: 'all',
  mode: 'animated',
  map: 'satellite',
  scale: 100,
  compare: false,
  comparisonRelease: 'v1.3.0',
  sort: 'slot',
};

test('catalogue contains one ordered record for every live MissionChief slot', () => {
  assert.equal(catalogue.total, 117);
  assert.equal(catalogue.vehicles.length, 117);
  assert.deepEqual(catalogue.vehicles.map((vehicle) => vehicle.slot), Array.from({ length: 117 }, (_, index) => index + 1));
  assert.equal(new Set(catalogue.vehicles.map((vehicle) => vehicle.asset_id)).size, 117);
});

test('catalogue exposes every promised service and focus view', () => {
  const services = new Set(catalogue.services.map((service) => service.id));
  for (const service of ['fire', 'ambulance', 'police', 'coastguard', 'lifeboat', 'search-and-rescue', 'recovery', 'airfield', 'eod']) {
    assert.ok(services.has(service), `Missing service filter: ${service}`);
  }
  const focus = new Set(catalogue.focus_views.map((view) => view.id));
  for (const view of ['role-differentiation', 'specialist-equipment', 'lighting', 'grounding-shadow']) {
    assert.ok(focus.has(view), `Missing focus view: ${view}`);
  }
});

test('search accepts slot, role name and punctuation-insensitive multi-term queries', () => {
  assert.equal(normaliseQuery('  Light 4X4 (L4P) '), 'light 4x4 l4p');
  assert.equal(filterVehicles(catalogue.vehicles, { ...defaults, search: 'slot 70' }).length, 1);
  assert.equal(filterVehicles(catalogue.vehicles, { ...defaults, search: 'ALB' })[0].slot, 70);
  assert.equal(filterVehicles(catalogue.vehicles, { ...defaults, search: 'drone police' })[0].slot, 92);
});

test('service and focused-change filters compose', () => {
  const policeLighting = filterVehicles(catalogue.vehicles, {
    ...defaults,
    service: 'police',
    focus: 'lighting',
  });
  assert.ok(policeLighting.length > 0);
  assert.ok(policeLighting.every((vehicle) => vehicle.service === 'police' && vehicle.focus.includes('lighting')));
});

test('sorting remains stable and deterministic', () => {
  assert.equal(sortVehicles(catalogue.vehicles, 'slot')[0].slot, 1);
  assert.equal(sortVehicles(catalogue.vehicles, 'name')[0].label, '4x4 Vehicle');
  const descending = sortVehicles(catalogue.vehicles, 'size-desc');
  assert.ok(descending[0].width >= descending.at(-1).width);
});

test('asset URLs use the staged current root and immutable historical tags', () => {
  const vehicle = catalogue.vehicles[0];
  assert.equal(currentAssetUrl(vehicle, 'animated', 'assets/exports/command'), 'assets/exports/command/animated/fire-rescue-pump.png');
  assert.equal(
    historicalAssetUrl('v1.0.0', vehicle, 'static', catalogue.releases),
    'https://raw.githubusercontent.com/Conroy1988/missionchief-uk-animated-graphics/v1.0.0/assets/exports/standard/static/fire-rescue-pump.png',
  );
});

test('view state has a compact shareable URL round trip', () => {
  const source = {
    ...defaults,
    search: 'rescue pod',
    service: 'fire',
    focus: 'specialist-equipment',
    mode: 'static',
    map: 'dark',
    scale: 50,
    compare: true,
    comparisonRelease: 'v1.2.7',
    sort: 'name',
  };
  const query = serialiseViewState(source);
  const parsed = parseViewState(`?${query}`, defaults);
  assert.deepEqual(parsed, source);
});

