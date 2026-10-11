const terminal = new Set(['completed', 'failed', 'cancelled']);

export function isRunning(job) {
  return Boolean(job && !terminal.has(job.state));
}

export function primaryAction(job) {
  if (job?.state === 'waiting_verification') return { action: 'confirm', label: 'I’ve verified, continue', enabled: true };
  if (job?.state === 'failed') return job.can_retry_speech
    ? { action: 'retry-speech', label: 'Retry speech recognition', enabled: true }
    : { action: 'start', label: 'Retry extraction', enabled: true };
  if (isRunning(job)) return { action: 'wait', label: 'Extracting…', enabled: false };
  return { action: 'start', label: 'Extract transcript', enabled: true };
}

export function progressSteps(job) {
  const state = job?.state;
  const acquired = Boolean(job?.can_retry_speech || ['transcribing', 'completed'].includes(state));
  const access = Boolean(job?.video);
  const completed = state === 'completed';
  const captions = completed && job.result?.source !== 'asr';
  return [
    { label: 'Access this video', done: access, current: !access },
    { label: 'Retrieve captions or video', done: acquired, current: access && !acquired },
    { label: captions ? 'Speech recognition skipped' : 'Generate speech captions if needed', done: completed, current: acquired && !completed },
    { label: 'Prepare transcript for Codex', done: completed, current: false },
  ];
}
