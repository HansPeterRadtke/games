import { CHARACTERS_PER_WORD, charactersPerMinute } from './rounds.js';

// A round occupies the same horizontal position for speed and accuracy, including missing values.
const svgNS = 'http://www.w3.org/2000/svg';
const byId = id => document.getElementById(id);
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 });

function svgNode(name, attributes) {
  const node = document.createElementNS(svgNS, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  return node;
}

function scaleFor(values, accuracy) {
  const min = Math.min(...values), max = Math.max(...values);
  const span = Math.max(max - min, accuracy ? 10 : max * 0.1, 0.001);
  const step = 10 ** Math.floor(Math.log10(span));
  let low = Math.max(0, Math.floor((min - span * 0.1) / step) * step);
  let high = Math.ceil((max + span * 0.1) / step) * step;
  if (accuracy) high = Math.min(100, high);
  if (high === low) low = Math.max(0, high - step);
  return [low, high];
}

export function renderRoundChart(record, rounds, timed, formatScore, sequenceLength) {
  const metric = byId('chart-metric').value, accuracy = metric === 'accuracy';
  const seconds = timed && metric === 'score';
  const cpm = metric === 'cpm';
  const unit = accuracy ? '%' : cpm ? 'chars/min' : seconds ? 's' : 'WPM';
  const rates = rounds.map(r => timed ? charactersPerMinute(sequenceLength, r.score)
    : Number.isFinite(r.score) ? r.score * CHARACTERS_PER_WORD : null);
  const values = rounds.map((r, i) => {
    if (accuracy) return r.accuracy;
    if (cpm) return rates[i];
    return seconds && Number.isFinite(r.score) ? r.score / 1000 : r.score;
  });
  const valid = values.filter(Number.isFinite);
  const plot = byId('round-plot');
  const n = rounds.length, end = record?.count ?? n, start = end - n + 1;
  byId('round-chart').hidden = !n;
  if (!n) return;
  byId('chart-unit').textContent = accuracy ? 'Accuracy (%) · higher is better'
    : cpm ? 'Characters/min · faster at top' : seconds ? 'Round time (s) · faster at top' : 'Pace (WPM) · faster at top';
  byId('round-axis-start').textContent = n === 1 ? '' : 'Round ' + start;
  byId('round-axis-start').parentElement.classList.toggle('single-round', n === 1);
  byId('round-axis-end').textContent = 'Round ' + end;
  byId('round-score-heading').textContent = timed ? 'Round time' : 'Pace';
  const rows = rounds.map((r, i) => {
    const tr = document.createElement('tr');
    for (const text of [String(start + i), formatScore(r.score, timed ? 'time' : 'wpm'),
      Number.isFinite(rates[i]) ? String(Math.round(rates[i])) : '—', formatScore(r.accuracy, 'accuracy')]) {
      const td = document.createElement('td');
      td.textContent = text;
      tr.append(td);
    }
    return tr;
  });
  byId('round-values').querySelector('tbody').replaceChildren(...rows);
  byId('chart-missing').hidden = Boolean(valid.length);
  plot.parentElement.hidden = !valid.length;
  byId('round-axis-start').parentElement.hidden = !valid.length;
  if (!valid.length) { plot.replaceChildren(); return; }
  const [low, high] = scaleFor(valid, accuracy);
  const top = seconds ? low : high, bottom = seconds ? high : low;
  byId('scale-top').textContent = number.format(top);
  byId('scale-bottom').textContent = number.format(bottom);
  const marks = [];
  let path = '', connected = false;
  values.forEach((v, i) => {
    if (!Number.isFinite(v)) { connected = false; return; }
    const x = n === 1 ? 160 : 5 + 310 * i / (n - 1);
    const y = 6 + 78 * (v - top) / (bottom - top);
    path += (connected ? ' L ' : ' M ') + x + ' ' + y;
    connected = true;
    const dot = svgNode('circle', { cx: x, cy: y, r: i === n - 1 ? 4 : 2.6 });
    const title = svgNode('title', {});
    title.textContent = 'Round ' + (start + i) + ' · ' + number.format(v) + ' ' + unit;
    dot.append(title);
    marks.push(dot);
  });
  plot.replaceChildren(svgNode('path', { d: path }), ...marks);
  const summary = 'Rounds ' + start + ' to ' + end + '. First measured ' + number.format(valid[0])
    + ', latest measured ' + number.format(valid.at(-1)) + ' ' + unit + '.';
  plot.setAttribute('aria-label', byId('chart-unit').textContent + '. ' + summary);
}
