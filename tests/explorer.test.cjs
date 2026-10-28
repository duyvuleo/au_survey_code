const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const core = require('../site/core.js');
const context = {window: {}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../site/data.js'), 'utf8'), context);
const data = JSON.parse(JSON.stringify(context.window.SURVEY_DATA));
const filter = patch => core.filterPapers(data, core.normalize(patch, data));

test('search recognizes names, original IDs, and setting evidence', () => {
  assert.deepEqual(filter({q: 'sCaRe'}).map(p => p.id), ['S14']);
  assert.deepEqual(filter({q: 'S14'}).map(p => p.id), ['S14']);
  assert.deepEqual(filter({q: 'NaLIR'}).map(p => p.id), ['A01']);
  assert.ok(filter({q: 'clarity spider'}).some(p => p.id === 'M05'));
});
test('composed filters intersect, and a genuine empty result stays empty', () => {
  assert.equal(filter({group: 'Interpretation', year: '2026'}).length, 5);
  assert.equal(filter({group: 'Interpretation', year: '2014'}).length, 0);
  assert.equal(filter({q: 'definitely-no-such-work'}).length, 0);
});
test('scope separates 62 fixed-corpus papers, two additions, and five surveys', () => {
  assert.equal(filter({scope: 'analysis'}).length, 62);
  assert.equal(filter({scope: 'literature'}).length, 2);
  assert.equal(filter({scope: 'survey'}).length, 5);
});
test('perspective filters use present judgments, not reading group or uncertainty', () => {
  assert.equal(filter({perspective: 'C'}).length, 8);
  assert.ok(!filter({perspective: 'C'}).some(p => p.id === 'M07'));
  assert.ok(filter({perspective: 'B'}).some(p => p.id === 'M05'));
  assert.ok(!filter({perspective: 'A'}).some(p => p.id === 'M05'));
  assert.equal(filter({perspective: 'I', scope: 'literature'}).length, 0);
});
test('URL state round-trips punctuation, filters, selected paper, and view', () => {
  const state = core.normalize({q: 'ambiguity & clarification / +', year: '2026', view: 'audit', paper: 'S14', perspective: 'B', sort: 'title'}, data);
  assert.deepEqual(core.decode('#' + core.encode(state), data), state);
});
test('unknown URL values cannot create invalid selection or render modes', () => {
  const state = core.decode('#group=wrong&year=0000&scope=bad&view=bad&paper=bad&sort=bad&perspective=__proto__', data);
  assert.deepEqual(state, core.defaults);
});
test('ordering supports newest, oldest, and title', () => {
  assert.equal(filter({sort: 'newest'})[0].year, 2026);
  assert.equal(filter({sort: 'oldest'})[0].year, 2014);
  const titles = filter({sort: 'title'}).map(p => p.title);
  assert.deepEqual(titles, [...titles].sort((a, b) => a.localeCompare(b)));
});
test('audit selection retains null findings and excludes context-only comparisons', () => {
  assert.equal(filter({}).flatMap(p => p.audits).length, 12);
  const clarity = filter({q: 'CLARITY'})[0];
  assert.equal(clarity.audits[0].distinct_gold_results, null);
  assert.equal(filter({q: 'BIRD-History'})[0].audits.length, 0);
});
