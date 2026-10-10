import test from 'node:test';
import assert from 'node:assert/strict';
import { isRunning, primaryAction, progressSteps } from '../src/lib/douyin-flow.js';

test('the same primary action resumes after manual verification, then becomes busy', () => {
  assert.equal(primaryAction(null).action, 'start');
  assert.deepEqual(primaryAction({ state: 'waiting_verification' }), { action: 'confirm', label: 'Verified — extract transcript', enabled: true });
  for (const state of ['opening_browser', 'reading_video', 'downloading_captions', 'downloading_media', 'transcribing']) {
    assert.equal(primaryAction({ state }).enabled, false);
    assert.equal(isRunning({ state }), true);
  }
});

test('a failed speech job retries without starting acquisition again', () => {
  assert.equal(primaryAction({ state: 'failed', can_retry_speech: true }).action, 'retry-speech');
  assert.equal(primaryAction({ state: 'failed', can_retry_speech: false }).action, 'start');
  for (const state of ['completed', 'failed', 'cancelled']) assert.equal(isRunning({ state }), false);
  const steps = progressSteps({ state: 'failed', can_retry_speech: true, video: {} });
  assert.deepEqual(steps.map((step) => step.done), [true, true, false, false]);
  assert.equal(steps[2].current, true);
});

test('caption-only completion skips speech and marks all stages done', () => {
  const steps = progressSteps({ state: 'completed', video: {}, result: { source: 'platform' } });
  assert.ok(steps.every((step) => step.done));
  assert.equal(steps[2].label, 'Speech recognition skipped');
});
