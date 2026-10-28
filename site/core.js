/* Shared browser/Node logic. No dependencies or network requests. */
(function (root) {
  'use strict';
  const defaults = {q: '', group: '', year: '', scope: '', perspective: '', view: 'map', sort: 'newest', paper: ''};
  const perspectives = {I: 'Interpretation', B: 'Answerability', C: 'Consequence', A: 'Action'};
  const scopeLabels = {analysis: 'Fixed analysis corpus', literature: 'Literature only', survey: 'Related survey'};
  function normalize(input, data) {
    const state = {...defaults, ...input};
    for (const key of Object.keys(defaults)) state[key] = String(state[key] ?? '');
    if (!data.groups.includes(state.group)) state.group = '';
    if (!data.papers.some(p => String(p.year) === state.year)) state.year = '';
    if (!Object.hasOwn(scopeLabels, state.scope)) state.scope = '';
    if (!Object.hasOwn(perspectives, state.perspective)) state.perspective = '';
    if (!['map', 'list', 'audit'].includes(state.view)) state.view = 'map';
    if (!['newest', 'oldest', 'title'].includes(state.sort)) state.sort = 'newest';
    if (!data.papers.some(p => p.id === state.paper)) state.paper = '';
    return state;
  }
  function searchText(paper) {
    return [paper.id, paper.name, paper.title, paper.group, ...paper.audits.map(a => a.family),
      ...paper.settings.flatMap(s => [s.setting_id, ...Object.values(s.setting)])].join(' ').toLowerCase();
  }
  function filterPapers(data, state) {
    const words = state.q.toLowerCase().trim().split(/\s+/).filter(Boolean);
    return data.papers.filter(p => (!state.group || p.group === state.group)
      && (!state.year || String(p.year) === state.year)
      && (!state.scope || p.scope === state.scope)
      && (!state.perspective || p.settings.some(s => s.states[state.perspective] === 'P'))
      && words.every(word => searchText(p).includes(word)))
      .sort((a, b) => (state.sort === 'title' ? 0 : (state.sort === 'oldest' ? a.year - b.year : b.year - a.year))
        || a.title.localeCompare(b.title));
  }
  function encode(state) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(defaults)) if (state[key] && state[key] !== value) params.set(key, state[key]);
    return params.toString();
  }
  function decode(hash, data) {
    return normalize(Object.fromEntries(new URLSearchParams(hash.replace(/^#/, ''))), data);
  }
  const api = {defaults, perspectives, scopeLabels, normalize, filterPapers, encode, decode};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SurveyExplorer = api;
})(typeof window !== 'undefined' ? window : globalThis);
