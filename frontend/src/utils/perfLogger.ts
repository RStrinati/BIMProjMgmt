import type { ProfilerOnRenderCallback } from 'react';

const isProduction = import.meta.env?.MODE === 'production';

const formatMs = (value: number) => `${value.toFixed(2)}ms`;

type ProfilerStats = {
  count: number;
  totalActual: number;
  totalBase: number;
  maxActual: number;
  lastActual: number;
  lastPhase: string;
  lastCommitDelay: number;
};

type NetworkStats = {
  count: number;
  totalDuration: number;
  maxDuration: number;
  lastDuration: number;
  lastStatus?: number;
  lastPhase: 'success' | 'error';
  phaseBreakdown: Record<'success' | 'error', number>;
};

type PerfStoreSnapshot = {
  profiler: Record<string, ProfilerStats>;
  network: Record<string, NetworkStats>;
};

type PerfStore = PerfStoreSnapshot & {
  checkpoints: Record<string, PerfStoreSnapshot>;
};

const ensureStore = (): PerfStore => {
  const globalObj = globalThis as unknown as { __UI_PERF_STORE__?: PerfStore };
  if (!globalObj.__UI_PERF_STORE__) {
    globalObj.__UI_PERF_STORE__ = {
      profiler: {},
      network: {},
      checkpoints: {},
    };
  }
  return globalObj.__UI_PERF_STORE__!;
};

const cloneStats = <T>(value: T): T => JSON.parse(JSON.stringify(value));

const normaliseNetworkKey = (method?: string, url?: string) =>
  `${(method ?? 'GET').toUpperCase()} ${url ?? ''}`.trim();

const toNumberOr = (value: unknown, fallback = 0) => {
  const numeric = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
};

export const profilerLog: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime,
) => {
  if (isProduction) {
    return;
  }

  const commitDelay = commitTime - startTime;

  const store = ensureStore();
  const metrics =
    store.profiler[id] ??
    ({
      count: 0,
      totalActual: 0,
      totalBase: 0,
      maxActual: 0,
      lastActual: 0,
      lastPhase: phase,
      lastCommitDelay: 0,
    } satisfies ProfilerStats);

  metrics.count += 1;
  metrics.totalActual += actualDuration;
  metrics.totalBase += baseDuration;
  metrics.maxActual = Math.max(metrics.maxActual, actualDuration);
  metrics.lastActual = actualDuration;
  metrics.lastPhase = phase;
  metrics.lastCommitDelay = commitDelay;

  store.profiler[id] = metrics;

  // eslint-disable-next-line no-console -- explicit instrumentation logging
  console.info(
    `[perf][profiler] id=${id} phase=${phase} actual=${formatMs(actualDuration)} base=${formatMs(
      baseDuration,
    )} commitDelay=${formatMs(commitDelay)}`,
  );
};

export const logNetworkTiming = (info: {
  method?: string;
  url?: string;
  status?: number;
  durationMs: number;
  phase: 'success' | 'error';
}) => {
  if (isProduction) {
    return;
  }

  const { method, url, status, durationMs, phase } = info;

  const key = normaliseNetworkKey(method, url);
  const store = ensureStore();
  const metrics =
    store.network[key] ??
    ({
      count: 0,
      totalDuration: 0,
      maxDuration: 0,
      lastDuration: 0,
      phaseBreakdown: { success: 0, error: 0 },
      lastPhase: phase,
    } satisfies NetworkStats);

  metrics.count += 1;
  metrics.totalDuration += durationMs;
  metrics.maxDuration = Math.max(metrics.maxDuration, durationMs);
  metrics.lastDuration = durationMs;
  metrics.lastStatus = typeof status === 'number' ? status : undefined;
  metrics.lastPhase = phase;
  metrics.phaseBreakdown[phase] += 1;

  store.network[key] = metrics;

  // eslint-disable-next-line no-console -- explicit instrumentation logging
  console.info(
    `[perf][network] phase=${phase} method=${(method ?? '').toUpperCase()} url=${url} status=${
      status ?? '—'
    } duration=${formatMs(durationMs)}`,
  );
};

export const getPerfMetrics = () => (isProduction ? undefined : ensureStore());

export const resetPerfMetrics = () => {
  if (isProduction) {
    return;
  }
  const store = ensureStore();
  store.profiler = {};
  store.network = {};
  store.checkpoints = {};
};

export const recordPerfCheckpoint = (label: string) => {
  if (isProduction) {
    return;
  }
  const store = ensureStore();
  store.checkpoints[label] = {
    profiler: cloneStats(store.profiler),
    network: cloneStats(store.network),
  };
};

const ensureCheckpoint = (label: string) => {
  const store = ensureStore();
  const snapshot = store.checkpoints[label];
  if (!snapshot) {
    // eslint-disable-next-line no-console -- developer guidance
    console.warn(`[perf] checkpoint "${label}" not found. Call recordPerfCheckpoint('${label}') first.`);
    return null;
  }
  return snapshot;
};

export const printPerfSummary = () => {
  if (isProduction) {
    return;
  }
  const store = ensureStore();

  const profilerRows = Object.entries(store.profiler).map(([id, stats]) => ({
    component: id,
    renders: stats.count,
    'avg actual': stats.count ? formatMs(stats.totalActual / stats.count) : '0ms',
    'max actual': formatMs(stats.maxActual),
    'last actual': formatMs(stats.lastActual),
    'last phase': stats.lastPhase,
    'commit delay': formatMs(stats.lastCommitDelay),
  }));

  const networkRows = Object.entries(store.network).map(([key, stats]) => ({
    request: key,
    calls: stats.count,
    'avg duration': stats.count ? formatMs(stats.totalDuration / stats.count) : '0ms',
    'max duration': formatMs(stats.maxDuration),
    'last status': stats.lastStatus ?? '—',
    'success calls': stats.phaseBreakdown.success,
    'error calls': stats.phaseBreakdown.error,
  }));

  console.groupCollapsed('[perf] summary');
  if (profilerRows.length) {
    console.table(profilerRows);
  } else {
    console.info('No profiler metrics recorded yet.');
  }
  if (networkRows.length) {
    console.table(networkRows);
  } else {
    console.info('No network timing metrics recorded yet.');
  }
  console.groupEnd();
};

const diffProfilerStats = (
  current: ProfilerStats | undefined,
  baseline: ProfilerStats | undefined,
): ProfilerStats | null => {
  if (!current) {
    return null;
  }
  const countDiff = current.count - (baseline?.count ?? 0);
  if (countDiff <= 0) {
    return null;
  }
  const totalActualDiff = current.totalActual - (baseline?.totalActual ?? 0);
  const totalBaseDiff = current.totalBase - (baseline?.totalBase ?? 0);
  const maxActual = Math.max(current.maxActual, baseline?.maxActual ?? 0);
  return {
    count: countDiff,
    totalActual: totalActualDiff,
    totalBase: totalBaseDiff,
    maxActual,
    lastActual: current.lastActual,
    lastPhase: current.lastPhase,
    lastCommitDelay: current.lastCommitDelay,
  };
};

const diffNetworkStats = (
  current: NetworkStats | undefined,
  baseline: NetworkStats | undefined,
): NetworkStats | null => {
  if (!current) {
    return null;
  }
  const countDiff = current.count - (baseline?.count ?? 0);
  if (countDiff <= 0) {
    return null;
  }
  const totalDurationDiff = current.totalDuration - (baseline?.totalDuration ?? 0);
  return {
    count: countDiff,
    totalDuration: totalDurationDiff,
    maxDuration: Math.max(current.maxDuration, baseline?.maxDuration ?? 0),
    lastDuration: current.lastDuration,
    lastStatus: current.lastStatus,
    lastPhase: current.lastPhase,
    phaseBreakdown: {
      success: toNumberOr(current.phaseBreakdown.success) - toNumberOr(baseline?.phaseBreakdown.success),
      error: toNumberOr(current.phaseBreakdown.error) - toNumberOr(baseline?.phaseBreakdown.error),
    },
  };
};

export const printPerfDelta = (fromLabel: string, toLabel: string) => {
  if (isProduction) {
    return;
  }
  const baseline = ensureCheckpoint(fromLabel);
  const target = ensureCheckpoint(toLabel);

  if (!baseline || !target) {
    return;
  }

  const profilerRows = Object.keys(target.profiler)
    .map((id) => ({
      id,
      stats: diffProfilerStats(target.profiler[id], baseline.profiler[id]),
    }))
    .filter((entry) => entry.stats !== null)
    .map((entry) => {
      const stats = entry.stats as ProfilerStats;
      return {
        component: entry.id,
        renders: stats.count,
        'avg actual': formatMs(stats.totalActual / stats.count),
        'max actual': formatMs(stats.maxActual),
        'last actual': formatMs(stats.lastActual),
        'last phase': stats.lastPhase,
      };
    });

  const networkRows = Object.keys(target.network)
    .map((key) => ({
      key,
      stats: diffNetworkStats(target.network[key], baseline.network[key]),
    }))
    .filter((entry) => entry.stats !== null)
    .map((entry) => {
      const stats = entry.stats as NetworkStats;
      return {
        request: entry.key,
        calls: stats.count,
        'avg duration': formatMs(stats.totalDuration / stats.count),
        'max duration': formatMs(stats.maxDuration),
        'last status': stats.lastStatus ?? '—',
        'success Δ': stats.phaseBreakdown.success,
        'error Δ': stats.phaseBreakdown.error,
      };
    });

  console.groupCollapsed(`[perf] delta "${fromLabel}" → "${toLabel}"`);
  if (profilerRows.length) {
    console.table(profilerRows);
  } else {
    console.info('No profiler deltas recorded for the selected checkpoints.');
  }
  if (networkRows.length) {
    console.table(networkRows);
  } else {
    console.info('No network timing deltas recorded for the selected checkpoints.');
  }
  console.groupEnd();
};

if (!isProduction && typeof window !== 'undefined') {
  const win = window as Window & {
    __UI_PERF_HELP_PRINTED__?: boolean;
  };
  if (!win.__UI_PERF_HELP_PRINTED__) {
    win.__UI_PERF_HELP_PRINTED__ = true;
    // eslint-disable-next-line no-console -- developer guidance
    console.info(
      '[perf] Dev helpers available: printPerfSummary(), recordPerfCheckpoint(label), printPerfDelta(fromLabel, toLabel), resetPerfMetrics()',
    );
  }
  win.getPerfMetrics = getPerfMetrics;
  win.resetPerfMetrics = resetPerfMetrics;
  win.printPerfSummary = printPerfSummary;
  win.recordPerfCheckpoint = recordPerfCheckpoint;
  win.printPerfDelta = printPerfDelta;
}

declare global {
  interface Window {
    __UI_PERF_STORE__?: PerfStore;
    __UI_PERF_HELP_PRINTED__?: boolean;
    getPerfMetrics?: typeof getPerfMetrics;
    resetPerfMetrics?: typeof resetPerfMetrics;
    printPerfSummary?: typeof printPerfSummary;
    recordPerfCheckpoint?: typeof recordPerfCheckpoint;
    printPerfDelta?: typeof printPerfDelta;
  }
}

