// Round times are measured in milliseconds. In the other modes the speed metric is WPM.
export const ROUND_WINDOWS = [1, 3, 5, 10, 20];
export const DEFAULT_ROUND_WINDOW = 3;
export const MAX_RECENT_ROUNDS = Math.max(...ROUND_WINDOWS);

function best(values, lowerWins = false) {
  const known = values.filter(Number.isFinite);
  return known.length ? (lowerWins ? Math.min(...known) : Math.max(...known)) : null;
}

function average(values) {
  const known = values.filter(Number.isFinite);
  return known.length ? known.reduce((a, b) => a + b, 0) / known.length : null;
}

export function recentStats(record, window, timed) {
  const rounds = (record?.recentRounds ?? []).slice(-window);
  const scores = rounds.map(r => r.score);
  const accuracies = rounds.map(r => r.accuracy);
  return {
    count: rounds.length, rounds, bestScore: best(scores, timed), meanScore: average(scores),
    bestAccuracy: best(accuracies), meanAccuracy: average(accuracies),
  };
}

export function scoreRound(previous, score, accuracy, timed, window) {
  const speedKey = timed ? 'bestMs' : 'bestWpm';
  const speedMetric = timed ? 'time' : 'pace';
  const priorSpeed = previous?.[speedKey] ?? null;
  const priorAccuracy = previous?.bestAccuracy ?? null;
  const recent = recentStats(previous, window, timed);
  const last = recent.rounds.at(-1);
  const faster = target => Number.isFinite(score) && Number.isFinite(target)
    && (timed ? score < target : score > target);
  const moreAccurate = target => Number.isFinite(target) && accuracy > target;
  let tier = 'complete', metric = speedMetric, target = null;
  if (priorSpeed === null && priorAccuracy === null) {
    tier = 'baseline';
  } else if (faster(priorSpeed)) {
    tier = 'all-time'; target = priorSpeed;
  } else if (moreAccurate(priorAccuracy)) {
    tier = 'all-time'; metric = 'accuracy'; target = priorAccuracy;
  } else if (faster(recent.bestScore)) {
    tier = 'recent'; target = recent.bestScore;
  } else if (moreAccurate(recent.bestAccuracy)) {
    tier = 'recent'; metric = 'accuracy'; target = recent.bestAccuracy;
  } else if (faster(last?.score)) {
    tier = 'improved'; target = last.score;
  } else if (moreAccurate(last?.accuracy)) {
    tier = 'improved'; metric = 'accuracy'; target = last.accuracy;
  } else if (score !== null && score === priorSpeed) {
    tier = 'matched';
  } else if (accuracy === 100) {
    tier = 'clean'; metric = 'accuracy';
  }
  const count = (previous?.count ?? previous?.recentRounds?.length ?? 0) + 1;
  return {
    record: {
      ...previous, count,
      [speedKey]: best([priorSpeed, score], timed),
      bestAccuracy: best([priorAccuracy, accuracy]),
      recentRounds: [...(previous?.recentRounds ?? []), { score, accuracy }].slice(-MAX_RECENT_ROUNDS),
    },
    reward: { tier, metric, score, accuracy, target, count: recent.count, milestone: count % 5 === 0 ? count : null },
  };
}
