import {
  KEY_ORDER, WINDOW_SIZES, PASSAGES, currentExpected, elapsedMs, finishEarly,
  newSession, pause, passageFingerprint, passageFor, progressOf, start, summaryOf,
  typeCharacter, unlockedKeys, accuracyOf,
} from './core.js';
import { loadData, saveData, serializeData, parseExport } from './storage.js';

const $ = id => document.getElementById(id);
const dom = {
  modeKeys: $('mode-keys'), modeText: $('mode-text'), keysControls: $('keys-controls'),
  textControls: $('text-controls'), levelDown: $('level-down'), levelUp: $('level-up'),
  levelLabel: $('level-label'), levelHint: $('level-hint'), goal: $('goal-select'),
  adaptive: $('adaptive-checkbox'), passage: $('passage-select'), customBlock: $('custom-block'),
  customText: $('custom-text'), phaseDot: $('phase-dot'), phaseText: $('phase-text'),
  prompt: $('prompt-surface'), keyStage: $('key-stage'), textStage: $('text-stage'),
  targetKey: $('target-key'), targetText: $('target-text'), keyOrder: $('key-order-display'),
  stageHint: $('stage-hint'), capture: $('type-capture'),
  progressCount: $('progress-count'), progressBar: $('progress-track'), progressFill: $('progress-fill'),
  primary: $('primary-button'), primaryLabel: $('primary-label'), primaryIcon: $('primary-icon'),
  newSession: $('new-session'), keyboardTip: $('keyboard-tip'), feedback: $('feedback'),
  statAccuracy: $('stat-accuracy'), statWpm: $('stat-wpm'), statResponse: $('stat-response'),
  statErrors: $('stat-errors'), elapsed: $('elapsed'), rhythm: $('rhythm-bars'),
  rhythmCaption: $('rhythm-caption'), windowControl: $('window-control'),
  recordWindow: $('record-window'), recordsTitle: $('records-title'),
  recordsGrid: $('records-grid'), recordsNote: $('records-note'),
  keyInsights: $('key-insights'), keysCountLabel: $('keys-count-label'),
  insightsNote: $('insights-note'), history: $('history-list'),
  saveIndicator: $('save-indicator'), saveLabel: $('save-label'),
  export: $('export-btn'), import: $('import-btn'), importFile: $('import-file'),
};

const initial = loadData();
let session = initial.session;
let profile = initial.profile;
let saveError = initial.error;
let notice = '';
let noticeKind = '';
let selectedWindow = 10;
let lastFeedback = '';
const now = () => performance.now();

function element(tag, className = '', text = '') {
  const e = document.createElement(tag);
  if (className) e.className = className;
  e.textContent = text;
  return e;
}
function formatInt(n) { return Math.round(n).toLocaleString('en-US'); }
function formatMs(n) {
  if (!Number.isFinite(n)) return '—';
  return n >= 1000 ? (n / 1000).toFixed(2) + ' s' : Math.round(n) + ' ms';
}
function timeLabel(ms) {
  const seconds = Math.floor(ms / 1000);
  return String(Math.floor(seconds / 60)).padStart(2, '0') + ':' + String(seconds % 60).padStart(2, '0');
}
function percent(n) { return n === null || !Number.isFinite(n) ? '—' : n.toFixed(n === 100 ? 0 : 1) + '%'; }
function keyName(key) { return key === ' ' ? 'Space' : key === '\n' ? 'Enter' : key.toUpperCase(); }
function focusTyping() {
  try { dom.capture.focus({ preventScroll: true }); } catch { dom.capture.focus(); }
}
function persist() {
  saveError = saveData(session, profile, now());
  renderSaveState();
}
function renderSaveState() {
  dom.saveIndicator.classList.toggle('failed', Boolean(saveError));
  dom.saveLabel.textContent = saveError || 'Saved on this device';
}
function hasPartial() { return session.correct > 0 || session.errors > 0; }
function abandonPrompt() {
  if (!['running', 'paused'].includes(session.phase) || !hasPartial()) return true;
  return window.confirm('Start a new session? Your completed keystrokes will remain in Recent sessions, but this round will end.');
}
function updateConfiguration(patch) {
  if (!abandonPrompt()) { render(); return false; }
  finishEarly(session, profile, now());
  session = newSession({ ...session, ...patch });
  lastFeedback = '';
  notice = '';
  persist();
  render();
  return true;
}
function beginPractice() {
  if (session.phase === 'complete') session = newSession(session);
  if (session.phase === 'running') {
    pausePractice();
    return;
  }
  if (session.mode === 'text' && !passageFor(session).trim()) {
    notice = 'Enter some practice text before starting.';
    noticeKind = 'error';
    render();
    dom.customText.focus();
    return;
  }
  if (start(session, profile, now())) {
    notice = '';
    lastFeedback = '';
    focusTyping();
    persist();
    render();
  }
}
function pausePractice(message = '') {
  if (!pause(session, now())) return;
  notice = message;
  noticeKind = '';
  persist();
  render();
}
function newPractice() {
  if (!abandonPrompt()) return;
  finishEarly(session, profile, now());
  session = newSession(session);
  notice = '';
  lastFeedback = '';
  persist();
  render();
}
function handleCharacter(char) {
  const result = typeCharacter(session, profile, char, now());
  if (result.kind === 'ignored') return;
  lastFeedback = result.kind;
  notice = '';
  if (result.kind === 'complete') {
    noticeKind = 'success';
    notice = 'Session complete. Your results and personal records are saved.';
  } else if (result.kind === 'incorrect') {
    noticeKind = 'error';
  } else if (result.records?.length) {
    noticeKind = 'success';
    const size = result.records[result.records.length - 1].windowSize;
    notice = 'New personal best over ' + size + ' keys.';
  }
  persist();
  render();
}
function isEditing(target) {
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest('textarea, select, [contenteditable="true"]'));
}
document.addEventListener('keydown', e => {
  if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing || e.key === 'Dead') return;
  if (isEditing(e.target)) {
    if (e.key === 'Escape' && session.phase === 'running') pausePractice();
    return;
  }
  if (e.key === 'Escape') {
    if (session.phase === 'running') { e.preventDefault(); pausePractice(); }
    return;
  }
  if (session.mode === 'keys' && session.phase !== 'running' && (e.key === '+' || e.key === '-')) {
    e.preventDefault();
    updateConfiguration({ level: session.level + (e.key === '+' ? 1 : -1) });
    return;
  }
  if (e.key === ' ' && session.phase !== 'running') {
    e.preventDefault();
    beginPractice();
    return;
  }
  if (e.key === ' ' && session.mode === 'keys') {
    e.preventDefault();
    pausePractice();
    return;
  }
  if (session.phase !== 'running') return;
  if (e.repeat) { if (e.key.length === 1) e.preventDefault(); return; }
  let key = e.key;
  if (key === 'Enter' && session.mode === 'text') key = '\n';
  if (Array.from(key).length !== 1) return;
  e.preventDefault();
  handleCharacter(key);
});
dom.capture.addEventListener('input', e => {
  // Some mobile keyboards emit input events without physical keydown events.
  if (e.inputType === 'insertFromPaste' || e.inputType === 'insertFromDrop') {
    dom.capture.value = '';
    return;
  }
  const value = dom.capture.value;
  dom.capture.value = '';
  if (session.phase !== 'running') return;
  for (const c of value) {
    if (session.phase !== 'running') break;
    handleCharacter(c);
  }
});
dom.capture.addEventListener('paste', e => e.preventDefault());
dom.prompt.addEventListener('click', focusTyping);
dom.prompt.addEventListener('keydown', e => {
  if ((e.key === 'Enter') && session.phase !== 'running') {
    e.preventDefault();
    beginPractice();
  }
});

dom.primary.addEventListener('click', beginPractice);
dom.newSession.addEventListener('click', newPractice);
dom.modeKeys.addEventListener('click', () => { if (session.mode !== 'keys') updateConfiguration({ mode: 'keys' }); });
dom.modeText.addEventListener('click', () => { if (session.mode !== 'text') updateConfiguration({ mode: 'text' }); });
dom.levelDown.addEventListener('click', () => updateConfiguration({ level: session.level - 1 }));
dom.levelUp.addEventListener('click', () => updateConfiguration({ level: session.level + 1 }));
dom.goal.addEventListener('change', () => updateConfiguration({ goal: Number(dom.goal.value) }));
dom.adaptive.addEventListener('change', () => {
  session.adaptive = dom.adaptive.checked;
  persist();
  render();
});
dom.passage.addEventListener('change', () => updateConfiguration({ passageId: dom.passage.value }));
dom.customText.addEventListener('input', () => {
  if (dom.customText.value === session.customText) return;
  updateConfiguration({ customText: dom.customText.value });
});

for (const passage of PASSAGES) {
  const option = element('option', '', passage.name + ' · ' + passage.language);
  option.value = passage.id;
  dom.passage.append(option);
}
const customOption = element('option', '', 'My own text');
customOption.value = 'custom';
dom.passage.append(customOption);
for (const size of WINDOW_SIZES) {
  const option = element('option', '', String(size));
  option.value = String(size);
  dom.recordWindow.append(option);
}
dom.recordWindow.addEventListener('change', () => {
  selectedWindow = Number(dom.recordWindow.value);
  renderRecords();
});

dom.export.addEventListener('click', () => {
  try {
    const data = serializeData(session, profile, now());
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = element('a');
    anchor.href = url;
    anchor.download = 'typewriter-backup-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
    notice = 'Backup exported.';
    noticeKind = 'success';
  } catch {
    notice = 'The backup could not be generated.';
    noticeKind = 'error';
  }
  renderFeedback();
});
dom.import.addEventListener('click', () => dom.importFile.click());
dom.importFile.addEventListener('change', async () => {
  const file = dom.importFile.files?.[0];
  if (!file) return;
  try {
    if (file.size > 1000000) throw new Error('The file is too large.');
    const imported = parseExport(await file.text());
    if (!window.confirm('Replace all current Typewriter progress with this backup? Export your current data first if you need it.')) return;
    profile = imported.profile;
    session = imported.session;
    lastFeedback = '';
    notice = 'Backup imported. Practice remains paused until you resume.';
    noticeKind = 'success';
    persist();
  } catch (e) {
    notice = e.message || 'The backup could not be imported.';
    noticeKind = 'error';
  } finally {
    dom.importFile.value = '';
    render();
  }
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden) pausePractice('Paused automatically while the page was hidden.');
});
window.addEventListener('pagehide', () => {
  if (session.phase === 'running') pause(session, now());
  persist();
});

function renderStage() {
  const isKeys = session.mode === 'keys';
  dom.keyStage.hidden = !isKeys;
  dom.textStage.hidden = isKeys;
  dom.prompt.classList.toggle('wrong', lastFeedback === 'incorrect' && session.phase === 'running');
  if (isKeys) {
    const keys = unlockedKeys(session);
    dom.targetKey.textContent = session.phase === 'idle' ? keys.slice(0, 2).map(keyName).join(' / ')
      : session.phase === 'complete' ? '✓' : keyName(session.target);
    dom.keyOrder.textContent = keys.map(keyName).join(' · ');
  } else {
    const text = session.target || passageFor(session);
    const typedLen = Array.from(session.typed).length;
    const fragment = document.createDocumentFragment();
    Array.from(text).forEach((char, i) => {
      const cls = i < typedLen ? 'typed' : i === typedLen
        ? (lastFeedback === 'incorrect' ? 'current wrong-current' : 'current') : 'pending';
      fragment.append(element('span', cls, char));
    });
    dom.targetText.replaceChildren(fragment);
  }
  if (session.phase === 'idle') {
    dom.stageHint.textContent = session.mode === 'keys' ? 'Press Space to begin, or select Start practice.'
      : 'Press Start practice, then type the passage exactly as shown.';
  } else if (session.phase === 'paused') {
    dom.stageHint.textContent = 'Paused. Your timer is stopped. Select Resume to continue.';
  } else if (session.phase === 'complete') {
    dom.stageHint.textContent = 'Round complete. Start another to keep improving.';
  } else if (lastFeedback === 'incorrect') {
    dom.stageHint.textContent = 'Not quite. Try ' + keyName(currentExpected(session)) + ' again.';
  } else {
    dom.stageHint.textContent = session.mode === 'keys'
      ? 'Type the highlighted key. Space pauses the exercise.'
      : 'Type every character, including spaces and punctuation. Esc pauses.';
  }
}
function renderStats() {
  const sum = summaryOf(session, now());
  dom.statAccuracy.textContent = percent(accuracyOf(session.correct, session.errors));
  dom.statWpm.textContent = sum.wpm === null ? '—' : formatInt(sum.wpm);
  dom.statResponse.textContent = formatMs(sum.avgMs);
  dom.statErrors.textContent = formatInt(session.errors);
  dom.elapsed.textContent = timeLabel(elapsedMs(session, now()));
}
function renderRhythm() {
  dom.rhythm.replaceChildren();
  const recent = session.trials.slice(-24);
  if (!recent.length) {
    dom.rhythm.append(element('div', 'rhythm-empty', 'Timing will appear here'));
    dom.rhythmCaption.textContent = 'Your timing appears as you type.';
    return;
  }
  const max = Math.max(350, ...recent.map(t => t.ms));
  for (const t of recent) {
    const bar = element('div', 'rhythm-bar');
    bar.style.height = Math.max(5, (t.ms / max) * 100) + '%';
    bar.title = keyName(t.key) + ': ' + formatMs(t.ms);
    bar.setAttribute('aria-label', bar.title);
    dom.rhythm.append(bar);
  }
  const average = recent.reduce((a, t) => a + t.ms, 0) / recent.length;
  dom.rhythmCaption.textContent = 'Average across the last ' + recent.length + ' correct keys: ' + formatMs(average) + '. Lower bars are faster.';
}
function addRecordCell(label, value, sub, isNew = false) {
  const cell = element('div', 'record-cell');
  cell.append(element('span', '', label), element('strong', isNew ? 'record-new' : '', value), element('small', '', sub));
  dom.recordsGrid.append(cell);
}
function renderRecords() {
  dom.recordsGrid.replaceChildren();
  const keys = session.mode === 'keys';
  dom.windowControl.hidden = !keys;
  if (keys) {
    dom.recordsTitle.textContent = 'Level ' + session.level + ' records';
    const row = profile.records[String(session.level)]?.[String(selectedWindow)] ?? {};
    const specs = [
      ['FASTEST', 'fastestMs', 'Best single response'],
      ['BEST AVERAGE', 'avgMs', 'Average over ' + selectedWindow + ' keys'],
      ['BEST WORST CASE', 'slowestMs', 'Slowest key in the window'],
      ['BEST ACCURACY', 'accuracy', 'Includes incorrect attempts'],
    ];
    for (const [label, key, sub] of specs) {
      const result = row[key];
      const fresh = session.latestRecords.some(r => r.metric === key && r.windowSize === selectedWindow);
      addRecordCell(label, result ? (key === 'accuracy' ? percent(result.value) : formatMs(result.value)) : '—', sub, fresh);
    }
    dom.recordsNote.textContent = 'Personal bests for ' + selectedWindow + ' consecutive correct keys at this level. Timing includes time spent correcting mistakes.';
  } else {
    dom.recordsTitle.textContent = 'Passage records';
    const id = session.passageId === 'custom' ? 'custom:' + passageFingerprint(passageFor(session)) : session.passageId;
    const best = profile.textRecords[id] || {};
    addRecordCell('BEST PACE', best.bestWpm === undefined || best.bestWpm === null ? '—' : formatInt(best.bestWpm) + ' WPM', 'For this passage');
    addRecordCell('BEST ACCURACY', best.bestAccuracy === undefined || best.bestAccuracy === null ? '—' : percent(best.bestAccuracy), 'For this passage');
    dom.recordsNote.textContent = 'Passages are scored separately. Your custom passage is compared only against the same text.';
  }
}
function renderInsights() {
  const keys = unlockedKeys(session);
  dom.keysCountLabel.textContent = keys.length + ' UNLOCKED';
  dom.keyInsights.replaceChildren();
  const known = keys.map(k => profile.keyStats[k]).filter(s => s && s.count).map(s => s.emaMs);
  const baseline = known.length ? known.reduce((a, b) => a + b, 0) / known.length : null;
  keys.forEach(key => {
    const s = profile.keyStats[key];
    const slow = baseline !== null && s?.count && s.emaMs > baseline * 1.2;
    const chip = element('div', 'key-chip' + (slow ? ' slow' : '') + (!s?.count ? ' unseen' : ''));
    chip.append(element('strong', '', key.toUpperCase()), element('small', '', s?.count ? formatMs(s.emaMs) : 'NEW'));
    chip.title = s?.count ? key.toUpperCase() + ': ' + s.count + ' correct, ' + s.errors + ' errors, ' + formatMs(s.emaMs) + ' moving average'
      : key.toUpperCase() + ': no measurements yet';
    dom.keyInsights.append(chip);
  });
  dom.insightsNote.textContent = session.adaptive
    ? 'Amber keys have slower responses than your current average. Adaptive training gives these keys extra practice.'
    : 'Adaptive focus is off. Every unlocked key has equal probability.';
}
function renderHistory() {
  dom.history.replaceChildren();
  const latest = profile.history.slice(0, 5);
  if (!latest.length) {
    dom.history.append(element('div', 'history-empty', 'Finish or end a practice round to build a session history.'));
    return;
  }
  for (const h of latest) {
    const date = Date.parse(h.at);
    const item = element('div', 'history-item');
    item.append(element('strong', '', h.mode === 'keys' ? 'Key trainer · L' + h.level : 'Text practice'));
    item.append(element('span', 'history-meta', h.status === 'completed' ? 'Completed' : 'Ended early'));
    item.append(element('span', 'history-result', percent(h.accuracy) + ' · ' + (h.wpm === null ? '—' : Math.round(h.wpm) + ' WPM')));
    item.append(element('span', 'history-meta', (Number.isNaN(date) ? 'Earlier' : new Date(date).toLocaleDateString()) + ' · ' + h.correct + ' keys'));
    dom.history.append(item);
  }
}
function renderFeedback() {
  dom.feedback.className = 'feedback';
  if (notice) {
    dom.feedback.textContent = notice;
    if (noticeKind) dom.feedback.classList.add(noticeKind);
  } else if (lastFeedback === 'incorrect' && session.phase === 'running') {
    dom.feedback.textContent = 'Mistake recorded. The target remains until you type it correctly.';
    dom.feedback.classList.add('error');
  } else if (session.phase === 'complete') {
    dom.feedback.textContent = 'Your progress is saved automatically. You can export a backup above.';
    dom.feedback.classList.add('success');
  } else {
    dom.feedback.textContent = session.mode === 'keys' ? 'Shortcuts: + / − changes level between rounds.' : 'Text must match exactly. Paste is disabled during practice.';
  }
}
function render() {
  const keys = session.mode === 'keys';
  dom.modeKeys.classList.toggle('active', keys);
  dom.modeText.classList.toggle('active', !keys);
  dom.modeKeys.setAttribute('aria-selected', String(keys));
  dom.modeText.setAttribute('aria-selected', String(!keys));
  dom.keysControls.hidden = !keys;
  dom.textControls.hidden = keys;
  dom.levelLabel.textContent = String(session.level).padStart(2, '0');
  dom.levelHint.textContent = unlockedKeys(session).length + ' keys';
  dom.levelDown.disabled = session.level <= 1;
  dom.levelUp.disabled = session.level >= KEY_ORDER.length - 1;
  dom.goal.value = String(session.goal);
  dom.adaptive.checked = session.adaptive;
  dom.passage.value = session.passageId;
  dom.customBlock.hidden = session.passageId !== 'custom';
  if (dom.customText.value !== session.customText) dom.customText.value = session.customText;
  dom.capture.setAttribute('autocapitalize', keys ? 'off' : 'sentences');
  const phase = { idle: 'READY', running: 'ACTIVE', paused: 'PAUSED', complete: 'COMPLETED' }[session.phase];
  dom.phaseText.textContent = phase;
  dom.phaseDot.className = 'phase-dot' + (session.phase === 'running' ? ' running' : session.phase === 'complete' ? ' complete' : '');
  dom.primaryLabel.textContent = { idle: 'Start practice', running: 'Pause', paused: 'Resume practice', complete: 'Practice again' }[session.phase];
  dom.primaryIcon.textContent = session.phase === 'running' ? 'Ⅱ' : session.phase === 'complete' ? '↻' : '▶';
  dom.primary.disabled = !keys && !passageFor(session).trim() && session.phase === 'idle';
  dom.keyboardTip.textContent = keys ? 'Space = start / pause · Esc = pause' : 'Space = type a space · Esc = pause';
  const progress = progressOf(session);
  const ratio = progress.total ? Math.min(100, progress.done / progress.total * 100) : 0;
  dom.progressCount.textContent = formatInt(progress.done) + ' / ' + formatInt(progress.total);
  dom.progressBar.setAttribute('aria-valuemax', String(progress.total));
  dom.progressBar.setAttribute('aria-valuenow', String(progress.done));
  dom.progressFill.style.width = ratio + '%';
  renderStage();
  renderStats();
  renderRhythm();
  renderRecords();
  renderInsights();
  renderHistory();
  renderFeedback();
  renderSaveState();
}

render();
setInterval(() => { if (session.phase === 'running') renderStats(); }, 300);
