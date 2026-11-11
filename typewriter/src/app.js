import { ROUND_WINDOWS } from './rounds.js';
import { renderRoundBoard, showRoundReward, showKeyWindowReward, clearReward } from './reward_view.js';
import {
  KEY_ORDER, WINDOW_SIZES, PASSAGES, currentExpected, elapsedMs, finishEarly,
  newSession, pause, passageFingerprint, passageFor, progressOf, start, summaryOf,
  typeCharacter, unlockedKeys, accuracyOf, reshuffleSequence, sequenceRecordKey,
  deleteCharacter, levelTextValid, textRecordKey, LEVEL_PASSAGES, isLevelPassage,
} from './core.js';
import { loadData, saveData, serializeData, parseExport, MAX_BACKUP_LENGTH } from './storage.js';
import { invalidTextKeys, normalizedPreset, keyCoverage, MIN_KEY_OCCURRENCES } from './training_text.js';

const $ = id => document.getElementById(id);
const dom = {
  modeKeys: $('mode-keys'), modeSequence: $('mode-sequence'), modeText: $('mode-text'), keysControls: $('keys-controls'),
  sequenceOptions: $('sequence-options'), sequenceLength: $('sequence-length'),
  sequenceMinimum: $('sequence-minimum'), sequenceRounds: $('sequence-rounds'),
  shuffleSequence: $('shuffle-sequence'), keyGoalBlock: $('key-goal-block'),
  adaptiveBlock: $('adaptive-block'), textControls: $('text-controls'), levelDown: $('level-down'), levelUp: $('level-up'),
  levelLabel: $('level-label'), levelHint: $('level-hint'), levelKeys: $('unlocked-key-list'), goal: $('goal-select'),
  adaptive: $('adaptive-checkbox'), passage: $('passage-select'), customBlock: $('custom-block'),
  textGenerationNote: $('text-generation-note'), textCoverageNote: $('text-coverage-note'),
  customValidation: $('custom-text-validation'),
  customText: $('custom-text'), phaseDot: $('phase-dot'), phaseText: $('phase-text'),
  prompt: $('prompt-surface'), keyStage: $('key-stage'), textStage: $('text-stage'),
  targetKey: $('target-key'), targetText: $('target-text'), keyOrder: $('key-order-display'),
  textStageLabel: $('text-stage-label'), stageHint: $('stage-hint'), capture: $('type-capture'),
  sequenceRoundLog: $('sequence-round-log'),
  roundLogItems: $('round-log-items'),
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
  clearReward();
  finishEarly(session, profile, now());
  // Existing saved profiles defaulted to a full passage even at level one.
  // When entering Text Practice, prefer the new level-aware trainer.
  if (patch.mode === 'text' && session.mode !== 'text'
      && PASSAGES.some(item => item.id === session.passageId)) {
    patch = { ...patch, passageId: 'level-mixed' };
  }
  session = newSession({ ...session, ...patch });
  if (session.mode === 'sequence' && !session.sequence) reshuffleSequence(session);
  lastFeedback = '';
  notice = '';
  persist();
  render();
  return true;
}
function beginPractice() {
  if (session.phase === 'complete') {
    clearReward();
    session = newSession(session);
  }
  if (session.phase === 'running') {
    pausePractice();
    return;
  }
  if (session.mode === 'text' && !session.legacyResume
      && !levelTextValid(session, session.target || passageFor(session))) {
    const invalid = invalidTextKeys(session.target || passageFor(session), unlockedKeys(session));
    notice = invalid.length
      ? 'Unavailable at this level. Unlock these letters first: ' + invalid.join(', ') + '.'
      : 'Enter a passage using the unlocked letters before starting.';
    noticeKind = 'error';
    render();
    (session.passageId === 'custom' ? dom.customText : dom.passage).focus();
    return;
  }
  if (start(session, profile, now())) {
    notice = '';
    lastFeedback = session.feedback;
    focusTyping();
    persist();
    render();
  }
}
function pausePractice(message = '') {
  if (!pause(session, now())) return;
  lastFeedback = '';
  notice = message;
  noticeKind = '';
  persist();
  render();
}
function newPractice() {
  if (!abandonPrompt()) return;
  clearReward();
  finishEarly(session, profile, now());
  session = newSession(session);
  if (session.mode === 'sequence' && !session.sequence) reshuffleSequence(session);
  notice = '';
  lastFeedback = '';
  persist();
  render();
}
function shufflePractice() {
  if (!abandonPrompt()) return;
  clearReward();
  finishEarly(session, profile, now());
  session = newSession(session);
  reshuffleSequence(session);
  lastFeedback = '';
  noticeKind = 'success';
  notice = 'New sequence shuffled. Every unlocked key is included.';
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
    notice = session.mode === 'sequence'
      ? 'All rounds complete. Start again to beat the same sequence record.'
      : 'Session complete. Your results and personal records are saved.';
  } else if (result.kind === 'round-complete') {
    noticeKind = 'success';
    notice = 'Round ' + result.round.number + ' complete · ' + percent(result.round.accuracy) + ' accuracy.';
  } else if (result.kind === 'incorrect') {
    noticeKind = 'error';
  } else if (result.records?.length) {
    noticeKind = 'success';
    const size = result.records[result.records.length - 1].windowSize;
    notice = result.records.some(r => r.windowSize === size && r.previous !== null)
      ? 'New personal best over ' + size + ' keys.' : 'First ' + size + '-key measurement saved.';
  }
  if (result.reward) showRoundReward(result.reward);
  if (session.mode === 'keys' && result.reward?.tier !== 'all-time' && result.records?.length) {
    showKeyWindowReward(result.records, selectedWindow);
  }
  persist();
  render();
}
function handleDelete() {
  const result = deleteCharacter(session, now());
  if (result.kind === 'ignored') return;
  lastFeedback = '';
  noticeKind = '';
  notice = result.kind === 'moved-back'
    ? 'Moved back one character. Continue typing from the highlighted cursor.'
    : result.kind === 'cleared' ? 'Mistake highlight cleared. Try the key again.' : '';
  persist();
  render();
}
function isEditing(target) {
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest('textarea, select, input:not(#type-capture), [contenteditable="true"]'));
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
  if (e.key === 'Backspace' || e.key === 'Delete') {
    if (session.phase === 'running' || session.phase === 'paused') {
      e.preventDefault();
      handleDelete();
    }
    return;
  }
  if (session.mode !== 'text' && session.phase !== 'running' && (e.key === '+' || e.key === '-')) {
    e.preventDefault();
    changeLevel(session.level + (e.key === '+' ? 1 : -1));
    return;
  }
  if (e.key === ' ' && session.phase !== 'running') {
    e.preventDefault();
    beginPractice();
    return;
  }
  if (e.key === ' ' && session.mode !== 'text') {
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
// Virtual keyboards may emit an input deletion with no physical keydown.
// Preventing beforeinput avoids double-handling on keyboards that emit both.
dom.capture.addEventListener('beforeinput', e => {
  if (!e.cancelable) return; // The ensuing input event handles this deletion.
  if (e.inputType === 'deleteContentBackward' || e.inputType === 'deleteContentForward') {
    e.preventDefault();
    handleDelete();
  }
});
dom.capture.addEventListener('input', e => {
  if (e.inputType === 'deleteContentBackward' || e.inputType === 'deleteContentForward') {
    dom.capture.value = '';
    handleDelete();
    return;
  }
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

const roundWindow = $('round-window');
for (const n of ROUND_WINDOWS) roundWindow.add(new Option(n, n));
roundWindow.addEventListener('change', () => {
  const n = Number(roundWindow.value);
  if (!ROUND_WINDOWS.includes(n)) return;
  profile.roundWindow = n;
  renderRoundBoard(session, profile);
  persist();
  if (session.phase === 'running') focusTyping();
});

dom.primary.addEventListener('click', beginPractice);
dom.newSession.addEventListener('click', newPractice);
dom.modeKeys.addEventListener('click', () => { if (session.mode !== 'keys') updateConfiguration({ mode: 'keys' }); });
dom.modeSequence.addEventListener('click', () => { if (session.mode !== 'sequence') updateConfiguration({ mode: 'sequence' }); });
dom.modeText.addEventListener('click', () => { if (session.mode !== 'text') updateConfiguration({ mode: 'text' }); });
function changeLevel(requested) {
  const level = Math.max(1, Math.min(KEY_ORDER.length - 1, requested));
  if (level === session.level) return;
  const sequenceLength = session.sequenceLength === session.level + 1
    ? level + 1 : Math.max(level + 1, session.sequenceLength);
  updateConfiguration({ level, sequenceLength });
}
dom.levelDown.addEventListener('click', () => changeLevel(session.level - 1));
dom.levelUp.addEventListener('click', () => changeLevel(session.level + 1));
dom.goal.addEventListener('change', () => updateConfiguration({ goal: Number(dom.goal.value) }));
dom.sequenceLength.addEventListener('change', () => updateConfiguration({ sequenceLength: Number(dom.sequenceLength.value) }));
dom.sequenceRounds.addEventListener('change', () => updateConfiguration({ sequenceRounds: Number(dom.sequenceRounds.value) }));
dom.shuffleSequence.addEventListener('click', shufflePractice);
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

for (const passage of LEVEL_PASSAGES) {
  const option = element('option', '', passage.name);
  option.value = passage.id;
  dom.passage.append(option);
}
for (const passage of PASSAGES) {
  const option = element('option', '', passage.name + ' · ' + passage.language + ' (full alphabet)');
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
    if (file.size > MAX_BACKUP_LENGTH) throw new Error('The file is too large.');
    const imported = parseExport(await file.text());
    if (!window.confirm('Replace all current Typewriter progress with this backup? Export your current data first if you need it.')) return;
    profile = imported.profile;
    session = imported.session;
    clearReward();
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
  const isSequence = session.mode === 'sequence';
  dom.keyStage.hidden = !isKeys;
  dom.textStage.hidden = isKeys;
  dom.textStageLabel.textContent = isSequence ? 'TYPE THIS SAME SEQUENCE EACH ROUND'
    : session.textKind === 'key-groups' ? 'PRACTICE THESE UNLOCKED KEY GROUPS'
    : session.textKind === 'words' ? 'PRACTICE REAL WORDS WITH YOUR UNLOCKED KEYS'
    : session.textKind === 'sentences+words' ? 'TYPE PHRASES AND FOCUS WORDS'
    : session.textKind === 'sentences+drills' ? 'TYPE PHRASES AND FOCUS KEY DRILLS'
    : session.textKind === 'words+drills' ? 'PRACTICE WORDS AND FOCUS KEY DRILLS'
    : session.textKind === 'sentences' ? 'TYPE SHORT PHRASES USING YOUR UNLOCKED KEYS'
    : 'TYPE THE PASSAGE BELOW';
  dom.prompt.classList.toggle('wrong', lastFeedback === 'incorrect' && session.phase === 'running');
  if (isKeys) {
    const keys = unlockedKeys(session);
    dom.targetKey.textContent = session.phase === 'idle' ? keys.slice(0, 2).map(keyName).join(' / ')
      : session.phase === 'complete' ? '✓' : keyName(session.target);
    dom.keyOrder.textContent = keys.map(keyName).join(' · ');
  } else {
    const text = isSequence ? session.sequence : (session.target || passageFor(session));
    const typedLen = Array.from(session.typed).length;
    const fragment = document.createDocumentFragment();
    Array.from(text).forEach((char, i) => {
      const cls = i < typedLen ? 'typed' : i === typedLen
        ? (lastFeedback === 'incorrect' ? 'current wrong-current' : 'current') : 'pending';
      fragment.append(element('span', cls, char));
    });
    dom.targetText.replaceChildren(fragment);
    const cursor = dom.targetText.querySelector('.current');
    if (cursor) {
      const parent = dom.targetText.getBoundingClientRect();
      const marker = cursor.getBoundingClientRect();
      if (marker.bottom > parent.bottom - 7) dom.targetText.scrollTop += marker.bottom - parent.bottom + 18;
      else if (marker.top < parent.top + 7) dom.targetText.scrollTop -= parent.top - marker.top + 18;
    }
  }
  if (session.phase === 'idle') {
    dom.stageHint.textContent = session.mode === 'keys' ? 'Press Space to begin, or select Start practice.'
      : isSequence ? 'Press Start. Repeat this exact order each round; only Shuffle changes it.'
      : session.textKind === 'key-groups'
        ? 'Few real words are possible yet. Practice these letter groups, then unlock more letters.'
        : 'Type only the unlocked letters. Use Backspace or Delete to correct a typo.';
  } else if (session.phase === 'paused') {
    dom.stageHint.textContent = 'Paused. Your timer is stopped. Select Resume to continue.';
  } else if (session.phase === 'complete') {
    dom.stageHint.textContent = isSequence ? 'Challenge complete. Start again with the same sequence to improve your best.'
      : 'Round complete. Start another to keep improving.';
  } else if (lastFeedback === 'incorrect') {
    dom.stageHint.textContent = 'Not quite. Try ' + keyName(currentExpected(session)) + ' again.';
  } else {
    dom.stageHint.textContent = session.mode === 'keys'
      ? 'Type the highlighted key. Space pauses the exercise.'
      : isSequence ? 'Complete the sequence as fast as you can. It will repeat without reshuffling.'
      : 'Type the text including spaces. Escape pauses the exercise.';
  }
}
function renderRoundLog() {
  dom.sequenceRoundLog.hidden = session.mode !== 'sequence';
  if (session.mode !== 'sequence') return;
  dom.roundLogItems.replaceChildren();
  if (!session.rounds.length) {
    dom.roundLogItems.append(element('p', 'muted-note', 'Your first completed sequence will set a time to beat.'));
    return;
  }
  for (const r of session.rounds.slice(-10).reverse()) {
    const row = element('div', 'round-log-row' + (r.newRecord ? ' is-record' : ''));
    row.append(element('span', 'round-label', 'Round ' + r.number), element('strong', 'round-time', formatMs(r.ms)));
    if (r.newRecord) row.append(element('span', 'round-crown', '★ BEST'));
    row.append(element('span', 'round-errors', r.errors ? r.errors + ' mistakes' : 'Perfect'));
    dom.roundLogItems.append(row);
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
  } else if (session.mode === 'sequence') {
    dom.recordsTitle.textContent = 'Sequence challenge';
    const record = profile.sequenceRecords[sequenceRecordKey(session)];
    const last = session.rounds.at(-1);
    addRecordCell('FASTEST ROUND', record ? formatMs(record.bestMs) : '—', 'Personal best for this exact sequence', !!session.lastAchievement);
    addRecordCell('LAST ROUND', last ? formatMs(last.ms) : '—', last ? 'Round ' + last.number + ' · ' + percent(last.accuracy) + ' accurate' : 'Complete a round to get a time');
    addRecordCell('ROUNDS COMPLETED', String(session.rounds.length), 'Of ' + session.sequenceRounds + ' planned rounds');
    addRecordCell('BEST ACCURACY', record ? percent(record.bestAccuracy) : '—', 'For this exact sequence');
    dom.recordsNote.textContent = 'Each round repeats the identical shuffled sequence. A faster full round sets a new record, even after starting a new session.';
  } else {
    dom.recordsTitle.textContent = 'Passage records';
    const id = textRecordKey(session);
    const best = profile.textRecords[id] || {};
    addRecordCell('BEST PACE', best.bestWpm === undefined || best.bestWpm === null ? '—' : formatInt(best.bestWpm) + ' WPM', 'For this passage');
    addRecordCell('BEST ACCURACY', best.bestAccuracy === undefined || best.bestAccuracy === null ? '—' : percent(best.bestAccuracy), 'For this passage');
    dom.recordsNote.textContent = isLevelPassage(session.passageId)
      ? 'Your best results are saved for this level and language setting, across different generated exercises.'
      : 'Preset passages are scored separately. Custom text records depend on the exact text.';
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
  dom.insightsNote.textContent = session.mode === 'sequence'
    ? 'Every unlocked key appears in the shuffled sequence. Key timings here come from single-key training, not sequence rounds.'
    : session.adaptive
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
    item.append(element('strong', '', h.mode === 'keys' ? 'Key trainer · L' + h.level
      : h.mode === 'sequence' ? 'Sequence · L' + h.level : 'Text practice'));
    item.append(element('span', 'history-meta', h.status === 'completed' ? 'Completed' : 'Ended early'));
    item.append(element('span', 'history-result', h.mode === 'sequence'
      ? (h.bestRoundMs === null ? 'No full round' : 'Best ' + formatMs(h.bestRoundMs))
      + ' · ' + (h.roundsCompleted ?? 0) + ' rounds'
      : percent(h.accuracy) + ' · ' + (h.wpm === null ? '—' : Math.round(h.wpm) + ' WPM')));
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
    dom.feedback.textContent = session.mode === 'keys' ? 'Shortcuts: + / − changes level between rounds; Delete clears an error.'
      : session.mode === 'sequence' ? 'Use + or − to change level between sessions. Delete clears a typo or removes the last correct letter.'
      : 'Backspace or Delete clears a typo. With no typo highlighted, it removes the last correct letter.';
  }
}
function render() {
  const keys = session.mode === 'keys';
  const sequence = session.mode === 'sequence';
  const text = session.mode === 'text';
  dom.modeKeys.classList.toggle('active', keys);
  dom.modeSequence.classList.toggle('active', sequence);
  dom.modeText.classList.toggle('active', text);
  dom.modeKeys.setAttribute('aria-selected', String(keys));
  dom.modeSequence.setAttribute('aria-selected', String(sequence));
  dom.modeText.setAttribute('aria-selected', String(text));
  dom.keysControls.hidden = !keys;
  dom.keyGoalBlock.hidden = !keys;
  dom.adaptiveBlock.hidden = !keys;
  dom.sequenceOptions.hidden = !sequence;
  dom.textControls.hidden = !text;
  dom.sequenceLength.min = String(unlockedKeys(session).length);
  dom.sequenceMinimum.textContent = 'Minimum ' + unlockedKeys(session).length + ' — includes every unlocked key';
  dom.sequenceLength.value = String(session.sequenceLength);
  dom.sequenceRounds.value = String(session.sequenceRounds);
  dom.levelLabel.textContent = String(session.level).padStart(2, '0');
  dom.levelHint.textContent = unlockedKeys(session).length + ' keys';
  dom.levelKeys.replaceChildren(...unlockedKeys(session).map(key => element('span', 'key-sample', key.toUpperCase())));
  dom.levelDown.disabled = session.level <= 1;
  dom.levelUp.disabled = session.level >= KEY_ORDER.length - 1;
  dom.goal.value = String(session.goal);
  dom.adaptive.checked = session.adaptive;
  dom.passage.value = session.passageId;
  dom.customBlock.hidden = !text || session.passageId !== 'custom';
  const unlocked = unlockedKeys(session);
  const exerciseText = text ? (session.target || passageFor(session)) : '';
  const illegal = invalidTextKeys(exerciseText, unlocked);
  const coverage = keyCoverage(exerciseText, unlocked);
  const isGenerated = isLevelPassage(session.passageId);
  dom.textCoverageNote.hidden = !text;
  if (text) {
    const latest = unlocked.at(-1);
    const minimum = isGenerated && !coverage.missing.length && coverage.weakest >= MIN_KEY_OCCURRENCES
      && coverage.counts[latest] >= 5;
    dom.textCoverageNote.classList.toggle('incomplete', !minimum);
    dom.textCoverageNote.textContent = isGenerated && minimum
      ? 'All ' + unlocked.length + ' unlocked keys included · at least ' + MIN_KEY_OCCURRENCES
        + ' times each · newest key ' + latest.toUpperCase() + ' appears '
        + coverage.counts[latest] + ' times'
      : coverage.covered + ' of ' + coverage.total + ' unlocked keys used'
        + (isGenerated ? ' · Start a new exercise to practise all keys.' : ' · Custom passages may omit some letters.');
  }
  dom.textGenerationNote.textContent = session.textKind === 'key-groups'
    ? 'At this level there are not enough real words; letter groups use only unlocked keys.'
    : session.textKind === 'words' ? 'Real German or English words using only unlocked keys.'
    : session.textKind.includes('drills') ? 'Real phrases where available, plus key drills for letters without usable words in this language.'
    : session.textKind === 'sentences+words' ? 'Real phrases and extra focus words include every unlocked key.'
    : isLevelPassage(session.passageId)
      ? 'Generated ' + (session.textLanguage === 'de' ? 'German' : session.textLanguage === 'en' ? 'English' : 'level-based')
        + ' practice using only unlocked letters.'
      : 'Full passages and your custom text are available only when their letters are unlocked.';
  dom.customValidation.textContent = illegal.length
    ? 'Not unlocked yet: ' + illegal.join(', ') + '. Change the level or edit the text.'
    : session.customText.trim() ? 'All entered letters are available at this level.'
    : 'Enter text using only the unlocked letters and spaces.';
  dom.customValidation.classList.toggle('invalid', illegal.length > 0);
  if (dom.customText.value !== session.customText) dom.customText.value = session.customText;
  dom.capture.setAttribute('autocapitalize', 'off');
  const phase = { idle: 'READY', running: 'ACTIVE', paused: 'PAUSED', complete: 'COMPLETED' }[session.phase];
  dom.phaseText.textContent = phase;
  dom.phaseDot.className = 'phase-dot' + (session.phase === 'running' ? ' running' : session.phase === 'complete' ? ' complete' : '');
  dom.primaryLabel.textContent = { idle: 'Start practice', running: 'Pause', paused: 'Resume practice', complete: 'Practice again' }[session.phase];
  dom.primaryIcon.textContent = session.phase === 'running' ? 'Ⅱ' : session.phase === 'complete' ? '↻' : '▶';
  dom.primary.disabled = text && !session.legacyResume
    && !levelTextValid(session, session.target || passageFor(session)) && session.phase === 'idle';
  dom.keyboardTip.textContent = text ? 'Backspace / Delete = correct typing · Esc = pause'
    : 'Space = start / pause · Backspace / Delete = clear or move back';
  const progress = progressOf(session);
  const ratio = progress.total ? Math.min(100, progress.done / progress.total * 100) : 0;
  dom.progressCount.textContent = formatInt(progress.done) + ' / ' + formatInt(progress.total);
  dom.progressBar.setAttribute('aria-valuemax', String(progress.total));
  dom.progressBar.setAttribute('aria-valuenow', String(progress.done));
  dom.progressFill.style.width = ratio + '%';
  renderStage();
  renderRoundBoard(session, profile);
  renderStats();
  renderRhythm();
  renderRecords();
  renderRoundLog();
  renderInsights();
  renderHistory();
  renderFeedback();
  renderSaveState();
}

render();
setInterval(() => { if (session.phase === 'running') renderStats(); }, 300);
