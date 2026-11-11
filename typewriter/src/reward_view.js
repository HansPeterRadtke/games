import { renderRoundChart } from './round_chart.js';
import { LEVEL_PASSAGES, isLevelPassage, roundRecordFor } from './core.js';
import { recentStats } from './rounds.js';

const byId = id => document.getElementById(id);
const popup = byId('achievement-banner');
const decimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
let lastResult = '';
let hideTimer;
let goldUntil = 0;

function valueOf(value, metric) {
  if (!Number.isFinite(value)) return '—';
  if (metric === 'accuracy') return decimal.format(value) + '%';
  if (metric === 'pace') return decimal.format(value) + ' WPM';
  return value < 1000 ? decimal.format(value) + ' ms' : Number((value / 1000).toFixed(4)) + ' s';
}

function describe(reward) {
  const { tier, target, count } = reward;
  const metric = reward.score === null ? 'accuracy' : reward.metric;
  const value = metric === 'accuracy' ? reward.accuracy : reward.score;
  const score = valueOf(value, metric);
  const previous = valueOf(target, metric);
  const gap = metric === 'accuracy' ? decimal.format(value - target) + ' percentage points'
    : valueOf(Math.abs(value - target), metric);
  const unit = metric === 'accuracy' ? 'accuracy' : metric === 'time' ? 'round time' : 'pace';
  let title, detail;
  switch (tier) {
    case 'all-time':
      title = 'All-time best ' + unit;
      detail = 'Improved by ' + gap + ' from ' + previous + '.';
      break;
    case 'recent':
      title = 'New recent best ' + unit;
      detail = 'Beat the best of your previous ' + count + (count === 1 ? ' round' : ' rounds') + ' by ' + gap + '.';
      break;
    case 'improved':
      title = metric === 'accuracy' ? 'More accurate' : 'Faster round';
      detail = 'Improved by ' + gap + ' over your last round.';
      break;
    case 'baseline':
      title = 'First round recorded'; detail = 'Your first target is set.'; break;
    case 'matched':
      title = 'Matched your best ' + unit; detail = 'Equal to your all-time best.'; break;
    case 'clean':
      title = 'Clean round'; detail = 'Every letter correct.'; break;
    default:
      title = 'Round complete'; detail = valueOf(reward.accuracy, 'accuracy') + ' accuracy.';
  }
  if (reward.milestone) detail += ' ' + reward.milestone + ' rounds completed.';
  return { title, score, detail };
}

export function clearReward() {
  clearTimeout(hideTimer);
  popup.hidden = true;
  goldUntil = 0;
  lastResult = '';
  byId('reward-announcement').textContent = '';
}

function announce(tier, title, score, detail) {
  if (!byId('celebrations').checked) return;
  if (tier !== 'all-time' && performance.now() < goldUntil) return;
  clearTimeout(hideTimer);
  if (tier === 'all-time') goldUntil = performance.now() + 2400;
  popup.dataset.tier = tier;
  byId('achievement-title').textContent = title;
  byId('achievement-time').textContent = score;
  byId('achievement-detail').textContent = detail;
  popup.hidden = false;
  popup.classList.remove('arrive');
  void popup.offsetWidth;
  popup.classList.add('arrive');
  hideTimer = setTimeout(() => { popup.hidden = true; }, tier === 'all-time' ? 4800 : 2700);
}

export function showRoundReward(reward) {
  const { title, score, detail } = describe(reward);
  lastResult = title + ' · ' + score + '. ' + detail;
  byId('reward-announcement').textContent = lastResult;
  if (['all-time', 'recent', 'improved', 'baseline'].includes(reward.tier)) {
    announce(reward.tier, title, score, detail);
  } else if (reward.milestone) {
    announce('milestone', 'Practice milestone', reward.milestone + ' rounds', title + ' · ' + score);
  }
}

export function showKeyWindowReward(records, window) {
  const labels = { avgMs: 'average response', accuracy: 'accuracy', slowestMs: 'slowest response',
    fastestMs: 'single response', medianMs: 'median response' };
  for (const [metric, label] of Object.entries(labels)) {
    const improvement = records.find(r => r.windowSize === window && r.metric === metric && Number.isFinite(r.previous));
    if (!improvement) continue;
    const unit = metric === 'accuracy' ? 'accuracy' : 'time';
    const title = 'All-time ' + window + '-key best';
    const score = valueOf(improvement.value, unit);
    const detail = 'Best ' + label + ' over ' + window + ' keys. Previous best ' + valueOf(improvement.previous, unit) + '.';
    byId('reward-announcement').textContent = title + ' · ' + score + '. ' + detail;
    announce('all-time', title, score, detail);
    break;
  }
}

let lastChartRecord, lastChartWindow, lastChartMode, lastChartMetric;
export function renderRoundBoard(session, profile) {
  const timed = session.mode === 'sequence';
  const record = roundRecordFor(session, profile);
  const stats = recentStats(record, profile.roundWindow, timed);
  const speed = timed ? 'time' : 'pace';
  const metric = byId('chart-metric').value;
  if (lastChartRecord !== record || lastChartWindow !== profile.roundWindow || lastChartMode !== session.mode || lastChartMetric !== metric) {
    renderRoundChart(record, stats.rounds, timed, valueOf);
    lastChartRecord = record;
    lastChartWindow = profile.roundWindow;
    lastChartMode = session.mode;
    lastChartMetric = metric;
  }
  byId('round-empty').hidden = Boolean(stats.count);
  document.querySelector('.round-metrics').hidden = !record;
  byId('practice-target').textContent = stats.bestScore == null ? ''
    : 'Target · ' + valueOf(stats.bestScore, speed);
  byId('round-window').value = String(profile.roundWindow);
  const scope = timed ? 'This exact sequence'
    : session.mode === 'keys' ? 'Level ' + session.level + ' · ' + session.goal + ' keys'
    : isLevelPassage(session.passageId) ? 'Level ' + session.level + ' · ' + LEVEL_PASSAGES.find(p => p.id === session.passageId).language
    : 'This passage';
  byId('round-scope').textContent = scope + ' · ' + stats.count + (stats.count === 1 ? ' recent round' : ' recent rounds');
  byId('sequence-personal-best').textContent = valueOf(timed ? record?.bestMs : record?.bestWpm, speed);
  byId('lifetime-accuracy').textContent = valueOf(record?.bestAccuracy, 'accuracy') + ' accuracy';
  byId('recent-best').textContent = valueOf(stats.bestScore, speed);
  byId('recent-accuracy').textContent = valueOf(stats.bestAccuracy, 'accuracy') + ' accuracy';
  byId('recent-average').textContent = valueOf(stats.meanScore, speed);
  byId('average-accuracy').textContent = valueOf(stats.meanAccuracy, 'accuracy') + ' accuracy';
  byId('sequence-score').hidden = !timed;
  if (timed) {
    const finished = session.phase === 'complete';
    const number = finished ? session.rounds.length : Math.min(session.rounds.length + 1, session.sequenceRounds);
    byId('sequence-round-position').textContent = number + ' / ' + session.sequenceRounds + (finished ? ' finished' : '');
  }
  const last = stats.rounds.at(-1);
  byId('round-result').textContent = lastResult || (last
    ? 'Last round · ' + valueOf(last.score, speed) + (last.accuracy === null ? '' : ' · ' + valueOf(last.accuracy, 'accuracy') + ' accuracy')
    : 'Complete a round to set your recent target.');
  byId('round-board-title').title = 'Recent statistics use ' + stats.count + ' completed rounds. Speed and accuracy have independent bests.';
}
