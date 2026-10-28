/* The explorer is deliberately self-contained: local data, native SVG and DOM. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!window.SURVEY_DATA || !window.SurveyExplorer) {
    $('error').hidden = false;
    $('error').textContent = 'The explorer data could not load. Run python3 scripts/build_explorer.py and reload this page.';
    return;
  }
  const data = window.SURVEY_DATA;
  const core = window.SurveyExplorer;
  const repo = 'https://github.com/duyvuleo/au_survey_code/blob/main/';
  const questions = {I: 'What does the request mean?', B: 'Can each meaning be answered?', C: 'Do the answers differ?', A: 'What should happen next?'};
  const statuses = {P: 'Present', N: 'Absent in inspected setting', U: 'Unclear'};
  const auditFields = {clarification: 'Clarification', coverage_risk: 'Coverage / risk', distinct_gold_results: 'Reference outputs', meaning_recovery: 'Recovery scoring'};
  const groupLabels = ['Interpretation', 'Answerability', 'Consequence & verification', 'Action & interaction', 'Context & adaptation', 'Related surveys'];
  let state = core.decode(location.hash, data);
  let shown = [];
  let toastTimer;
  let lastTrigger;

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function button(text, action, className) {
    const node = el('button', text, className);
    node.type = 'button';
    node.addEventListener('click', action);
    return node;
  }
  function link(text, url) {
    const node = el('a', text);
    // Source files are repository-owned, but only web links are navigable.
    const parsed = new URL(url);
    if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('Invalid source link');
    node.href = parsed.href;
    node.target = '_blank';
    node.rel = 'noopener noreferrer';
    return node;
  }
  function sourceLink(text, path) { return link(text, repo + path); }
  function setState(patch) {
    state = core.normalize({...state, ...patch}, data);
    // Query state remains local, even on a published static site.
    const hash = core.encode(state);
    try { history.replaceState(null, '', location.pathname + location.search + (hash ? '#' + hash : '')); }
    catch { location.hash = hash; }
    render();
  }
  function toast(message) {
    clearTimeout(toastTimer);
    $('toast').textContent = message;
    $('toast').hidden = false;
    toastTimer = setTimeout(() => { $('toast').hidden = true; }, 5000);
  }
  function reset() { setState({...core.defaults, view: state.view}); }
  function openPaper(id, trigger) { lastTrigger = trigger || document.activeElement; setState({paper: id}); }
  function closePaper() {
    if (!state.paper) return;
    const closedId = state.paper;
    setState({paper: ''});
    const replacement = [...$(state.view + '-panel').querySelectorAll('[data-paper]')].find(node => node.dataset.paper === closedId);
    if (replacement) replacement.focus();
    else if (lastTrigger?.isConnected) lastTrigger.focus();
    else $('tab-' + state.view).focus();
  }
  function svgNode(tag, attrs, text) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function accessibleSvgAction(node, action) {
    node.setAttribute('role', 'button');
    node.setAttribute('tabindex', '0');
    node.addEventListener('click', action);
    node.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); action(); }
    });
  }

  function renderMap() {
    const clusters = [];
    data.groups.forEach((group, index) => {
      const papers = shown.filter(p => p.group === group);
      if (!papers.length) return;
      const cluster = el('section', undefined, 'map-cluster');
      cluster.style.setProperty('--node-color', `var(--g${index})`);
      const heading = el('h3');
      const filter = button(groupLabels[index], () => setState({group: state.group === group ? '' : group}));
      filter.setAttribute('aria-label', `Filter reading group: ${group}`);
      filter.setAttribute('aria-pressed', String(state.group === group));
      heading.append(filter, el('span', String(papers.length), 'cluster-count'));
      const height = papers.length * 33 + 16;
      const cy = height / 2;
      const svg = svgNode('svg', {viewBox: `0 0 380 ${height}`, role: 'group', 'aria-label': `${group}: ${papers.length} papers`});
      const edges = svgNode('g', {});
      const nodes = svgNode('g', {});
      papers.forEach((paper, i) => {
        const y = i * 33 + 24;
        edges.append(svgNode('path', {d: `M 16 ${cy} C 40 ${cy}, 36 ${y}, 57 ${y}`, class: 'edge', fill: 'none'}));
        const node = svgNode('g', {class: `node ${paper.scope}`, 'data-paper': paper.id, 'aria-label': `${paper.name}, ${paper.year}. Inspect evidence.`});
        node.append(svgNode('title', {}, `${paper.name} · ${paper.title} (${paper.year})`));
        node.append(svgNode('rect', {x: 46, y: y - 15, width: 330, height: 31, rx: 5, class: 'node-target'}));
        node.append(svgNode('circle', {cx: 57, cy: y, r: 5}));
        node.append(svgNode('text', {x: 71, y: y + 4}, paper.name));
        node.append(svgNode('text', {x: 370, y: y + 4, 'text-anchor': 'end', class: 'node-year'}, String(paper.year)));
        accessibleSvgAction(node, () => openPaper(paper.id, node));
        nodes.append(node);
      });
      svg.append(edges, svgNode('circle', {cx: 16, cy, r: 6, fill: 'var(--node-color)'}), nodes);
      cluster.append(heading, svg);
      clusters.push(cluster);
    });
    $('map').replaceChildren(...clusters);
  }

  function renderList() {
    $('reading-list').replaceChildren(...shown.map(paper => {
      const row = el('article', undefined, 'paper-row');
      const body = el('div');
      const title = button(paper.name, () => openPaper(paper.id, title), 'paper-title');
      title.dataset.paper = paper.id;
      const meta = el('div', undefined, 'paper-meta');
      meta.append(el('span', paper.group));
      body.append(title, el('p', paper.title, 'full-title'), meta);
      const tags = el('div', undefined, 'paper-tags');
      tags.append(el('span', core.scopeLabels[paper.scope], 'chip'), el('div', `${paper.settings.length} mapped settings`));
      const inspect = button('Inspect ↗', () => openPaper(paper.id, inspect), 'inspect');
      inspect.setAttribute('aria-label', `Inspect ${paper.title}`);
      row.append(el('span', paper.year, 'paper-year'), body, tags, inspect);
      return row;
    }));
  }

  function renderAudit() {
    const rows = shown.flatMap(p => p.audits.map(a => ({...a, paper: p})));
    $('audit-count').textContent = `${rows.length} of ${data.scope.benchmark_audit_settings} audited settings · ${new Set(rows.map(r => r.paper.id)).size} studies in the current selection`;
    $('audit-rows').replaceChildren(...rows.map(audit => {
      const row = el('tr');
      const name = el('td');
      const inspect = button(audit.setting, () => openPaper(audit.paper.id, inspect));
      name.append(inspect);
      row.append(name);
      for (const field of Object.keys(auditFields)) {
        const cell = el('td');
        if (audit[field] == null) cell.append(el('span', 'Not assessed', 'not-assessed'));
        else cell.append(button(audit[field], () => {
          const additions = [audit.coverage_risk_scope, ...(audit.source_locators || []), audit.grouping_reason].filter(Boolean);
          $('qualification').textContent = `${audit.setting} · ${auditFields[field]} — ${data.auditQualifications[audit[field]]} ${field === 'coverage_risk' ? additions.join(' ') : ''}`;
        }));
        row.append(cell);
      }
      return row;
    }));
    $('qualification').textContent = rows.length ? 'Choose a finding to read its scope and limitations.' : 'No audited settings match the selected papers. Clear a filter or switch to the reading list.';
  }

  function settingDetails(setting, paper) {
    const details = el('details', undefined, 'setting');
    const suffix = setting.setting_id.replace(setting.paper_id, '').replace(/^[:\-]+/, '').replaceAll('-', ' ').replaceAll('_', ' ');
    const summary = el('summary', `${paper.name} · ${suffix}`);
    const body = el('div', undefined, 'setting-body');
    const states = el('div', undefined, 'states');
    for (const [key, name] of Object.entries(core.perspectives)) {
      const status = setting.states[key];
      states.append(el('span', `${name}: ${statuses[status]}`, `state ${status === 'P' ? 'present' : status === 'U' ? 'unclear' : ''}`));
    }
    body.append(states);
    const dl = el('dl');
    const labels = {information_available: 'Available information', interaction_protocol: 'Interaction', dataset_sampling: 'Population', output_answer_contract: 'Output contract', metric: 'Metric', evaluation_description: 'Evaluation', validity_scope: 'Validity scope'};
    for (const [key, name] of Object.entries(labels)) if (setting.setting[key]) dl.append(el('dt', name), el('dd', setting.setting[key]));
    dl.append(el('dt', 'Source version'), el('dd', setting.source_version), el('dt', 'Source access'), el('dd', setting.source_access));
    body.append(dl, link('Recorded primary source ↗', setting.source_url));
    const rationale = el('details', undefined, 'rationale');
    rationale.append(el('summary', 'Perspective rationales and source locators'));
    rationale.append(el('p', `Original setting ID: ${setting.setting_id}`));
    for (const [key, name] of Object.entries(core.perspectives)) {
      const entry = setting.perspectives[key];
      rationale.append(el('p', `${name} — ${entry.rationale}`), el('code', `Locator IDs: ${entry.source_locators.join(', ')}`));
    }
    body.append(rationale);
    const verification = setting.verification;
    body.append(el('p', `Supporting verification: ${statuses[verification.status]}. Stage: ${verification.stage}. This role is separate from direct answer comparison (Consequence).`));
    const connections = el('details', undefined, 'rationale');
    connections.append(el('summary', 'Recorded relationship assignments'));
    connections.append(el('p', 'Information flow and empirical relationship evaluation are separate judgments. These are the strict assignments after review; presence does not imply causality or deployment.'));
    const list = el('ul');
    for (const [pair, values] of Object.entries(setting.connections)) {
      const pairName = [...pair].map(k => core.perspectives[k]).join(' ↔ ');
      list.append(el('li', `${pairName}: information flow — ${statuses[values.integration]}; relationship evaluation — ${statuses[values.relationship_evaluation]}.`));
    }
    connections.append(list, sourceLink('Review criteria ↗', 'analysis/data/overlap/relationships/reviews/criteria.md'), el('br'), sourceLink('Resolution decisions ↗', 'analysis/data/overlap/relationships/reviews/resolutions.json'));
    body.append(connections);
    details.append(summary, body);
    return details;
  }

  function renderDetail() {
    const dialog = $('detail');
    if (!state.paper) { if (dialog.open) dialog.close(); return; }
    if (dialog.open && dialog.dataset.paper === state.paper) return;
    const paper = data.papers.find(p => p.id === state.paper);
    dialog.dataset.paper = paper.id;
    const fragment = document.createDocumentFragment();
    fragment.append(el('p', `${paper.year} · ${paper.group}`, 'eyebrow'));
    const heading = el('h2', paper.name); heading.id = 'detail-title'; fragment.append(heading);
    fragment.append(el('p', paper.title, 'detail-full-title'));
    const links = el('div', undefined, 'detail-links');
    paper.links.forEach((item, index) => links.append(link(index === 0 ? 'Read paper ↗' : item.label + ' ↗', item.url)));
    links.append(sourceLink('Reading-list entry ↗', 'papers/README.md#' + paper.group.toLowerCase().replaceAll(' ', '-')));
    fragment.append(links);
    let scopeText = core.scopeLabels[paper.scope] + '. ';
    if (paper.exclusion) scopeText += paper.exclusion.reason;
    else if (paper.scope === 'survey') scopeText += 'Background reading; not included in the technical study counts or fixed quantitative analyses.';
    else scopeText += `${paper.settings.length} direct NL2SQL settings are available in this explorer. ` + (paper.settings.length ? 'Presence applies to a recorded setting, not automatically to every use of this system.' : 'This study belongs to the fixed corpus, but has no setting in the 88-setting direct NL2SQL map.');
    fragment.append(el('p', scopeText, 'scope-note'));
    fragment.append(el('h3', 'Mapped settings'), el('p', 'Present / absent / unclear describe the inspected setting. Open a setting to see its contract, evidence, and source version.'));
    if (!paper.settings.length) fragment.append(el('p', 'No direct NL2SQL setting records are included for this paper. This is not an absence judgment.'));
    paper.settings.forEach(setting => fragment.append(settingDetails(setting, paper)));
    if (paper.audits.length) {
      fragment.append(el('h3', 'Benchmark audit'));
      paper.audits.forEach(audit => {
        const section = el('div', undefined, 'detail-audit');
        section.append(el('strong', audit.setting));
        for (const [key, name] of Object.entries(auditFields)) {
          section.append(el('p', `${name}: ${audit[key] ?? 'Not assessed'}. ${audit[key] ? data.auditQualifications[audit[key]] : ''}`));
        }
        if (audit.grouping_reason) section.append(el('p', audit.grouping_reason));
        fragment.append(section);
      });
    }
    const sources = el('div', undefined, 'detail-links');
    sources.append(sourceLink('Setting source records ↗', 'analysis/data/overlap/relationships/source-records.json'), sourceLink('Strict assignments ↗', 'analysis/data/overlap/relationships/outputs/strict-analysis-records.json'));
    fragment.append(el('p', `Original paper ID: ${paper.id}. Retained for traceability to the fixed records.`), sources);
    $('detail-content').replaceChildren(fragment);
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
  }

  function render() {
    shown = core.filterPapers(data, state);
    for (const [key, id] of Object.entries({q: 'search', group: 'group', year: 'year', scope: 'scope', sort: 'sort'})) $(id).value = state[key];
    const settings = shown.reduce((n, p) => n + p.settings.length, 0);
    $('count').textContent = `${shown.length} of ${data.papers.length} papers · ${settings} mapped settings in this selection`;
    $('active-filter').replaceChildren();
    if (state.perspective) $('active-filter').append(button(`${core.perspectives[state.perspective]}: present ×`, () => setState({perspective: ''})));
    document.querySelectorAll('[data-perspective]').forEach(node => node.setAttribute('aria-pressed', String(node.dataset.perspective === state.perspective)));
    for (const view of ['map', 'list', 'audit']) {
      $('tab-' + view).setAttribute('aria-selected', String(view === state.view));
      $('tab-' + view).tabIndex = view === state.view ? 0 : -1;
      $(view + '-panel').hidden = view !== state.view || !shown.length;
    }
    $('empty').hidden = Boolean(shown.length);
    $('export').disabled = !shown.length;
    if (state.view === 'map') renderMap();
    if (state.view === 'list') renderList();
    if (state.view === 'audit') renderAudit();
    renderDetail();
  }

  const counts = [[data.papers.filter(p => p.scope !== 'survey').length, 'technical studies'], [data.papers.filter(p => p.scope === 'survey').length, 'related surveys'], [data.scope.direct_nl2sql_settings, 'mapped settings'], [data.scope.benchmark_audit_settings, 'audited settings']];
  counts.forEach(([count, label]) => { const item = el('div', undefined, 'stat'); item.append(el('strong', count), el('span', label)); $('stats').append(item); });
  Object.entries(core.perspectives).forEach(([key, name], index) => {
    const count = data.papers.filter(p => p.settings.some(s => s.states[key] === 'P')).length;
    const card = button('', () => setState({perspective: state.perspective === key ? '' : key}), 'perspective');
    card.dataset.perspective = key;
    card.setAttribute('aria-pressed', 'false');
    const top = el('span', undefined, 'perspective-top');
    top.append(el('span', `0${index + 1}`, 'perspective-index'), el('span', `${count} studies with presence`));
    card.append(top, el('h3', name), el('p', questions[key]));
    $('perspectives').append(card);
  });
  data.groups.forEach((group, index) => {
    const option = el('option', group); option.value = group; $('group').append(option);
    const item = button(groupLabels[index], () => setState({group: state.group === group ? '' : group}));
    const dot = el('span', undefined, 'legend-dot'); dot.style.setProperty('--node-color', `var(--g${index})`); item.prepend(dot); $('legend').append(item);
  });
  $('legend').append(el('span', '○ Hollow dots: literature-only additions', 'muted'));
  [...new Set(data.papers.map(p => p.year))].sort((a, b) => b - a).forEach(year => { const option = el('option', year); option.value = year; $('year').append(option); });
  $('provenance').append(el('p', data.annotationProvenance.procedure), el('p', data.annotationProvenance.reproducibility));
  const sourceList = el('ul');
  data.provenance.forEach(source => { const item = el('li'); item.append(sourceLink(source.path, source.path), el('code', `SHA-256 ${source.sha256}`)); sourceList.append(item); });
  $('provenance').append(sourceList);
  $('filters').addEventListener('submit', event => event.preventDefault());
  document.querySelectorAll('a[href="#explore"]').forEach(anchor => anchor.addEventListener('click', event => {
    event.preventDefault();
    $('explore').tabIndex = -1;
    $('explore').focus({preventScroll: true});
    $('explore').scrollIntoView();
  }));
  $('search').addEventListener('input', event => setState({q: event.target.value}));
  for (const key of ['group', 'year', 'scope', 'sort']) $(key).addEventListener('change', event => setState({[key]: event.target.value}));
  $('reset').addEventListener('click', reset); $('empty-reset').addEventListener('click', reset);
  document.querySelectorAll('[data-view]').forEach(tab => {
    tab.addEventListener('click', () => setState({view: tab.dataset.view}));
    tab.addEventListener('keydown', event => {
      const views = ['map', 'list', 'audit']; let index = views.indexOf(state.view);
      if (event.key === 'ArrowRight') index = (index + 1) % views.length;
      else if (event.key === 'ArrowLeft') index = (index + views.length - 1) % views.length;
      else if (event.key === 'Home') index = 0;
      else if (event.key === 'End') index = views.length - 1;
      else return;
      event.preventDefault(); setState({view: views[index]}); $('tab-' + views[index]).focus();
    });
  });
  $('close-detail').addEventListener('click', closePaper);
  $('detail').addEventListener('cancel', event => { event.preventDefault(); closePaper(); });
  $('detail').addEventListener('click', event => { if (event.target === $('detail') && event.clientX < $('detail').getBoundingClientRect().left) closePaper(); });
  window.addEventListener('hashchange', () => { if (location.hash !== '#explore') { state = core.decode(location.hash, data); render(); } });
  $('share').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); toast('View link copied. Filters and the selected paper are included.'); }
    catch { toast('Copy the address from your browser to share this view.'); }
  });
  $('export').addEventListener('click', () => {
    const payload = {schemaVersion: data.schemaVersion, filters: state, scope: data.scope, annotationProvenance: data.annotationProvenance, auditQualifications: data.auditQualifications, provenance: data.provenance, papers: shown};
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2) + '\n'], {type: 'application/json'}));
    const download = el('a'); download.href = url; download.download = 'ambiguity-survey-selection.json'; download.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Exported ${shown.length} papers with source provenance.`);
  });
  let savedTheme;
  try { savedTheme = localStorage.getItem('survey-explorer-theme'); } catch { /* Storage can be unavailable for local files. */ }
  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
  function applyTheme(theme) { document.documentElement.dataset.theme = theme; $('theme').setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`); }
  applyTheme(['light', 'dark'].includes(savedTheme) ? savedTheme : systemTheme.matches ? 'dark' : 'light');
  $('theme').addEventListener('click', () => { const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; applyTheme(theme); savedTheme = theme; try { localStorage.setItem('survey-explorer-theme', theme); } catch { /* Optional preference only. */ } });
  systemTheme.addEventListener('change', event => { if (!savedTheme) applyTheme(event.matches ? 'dark' : 'light'); });
  render();
})();
