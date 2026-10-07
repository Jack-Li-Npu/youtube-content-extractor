import test from 'node:test';
import assert from 'node:assert/strict';
import { countTextTokens, estimateCodexInput } from '../src/lib/token-estimate.js';
import { buildCodexHandoff, CODEX_PROMPT } from '../src/lib/transcript.js';

const data = {
  title: 'A multilingual talk', video_id: 'Hrbq66XqtCo', language: 'en',
  source: 'uploaded', track_id: 'uploaded:en', duration: 3610,
  transcript_lines: [
    { start: 0.125, duration: 3.75, text: 'Hello, 世界 👋' },
    { start: 3601.25, duration: 5.125, text: 'A literal <|endoftext|> stays in the caption.' },
  ],
};

test('reference tokenizer handles ordinary text, Unicode, and literal control-token strings', () => {
  assert.equal(countTextTokens(''), 0);
  assert.equal(countTextTokens('hello world'), 2);
  assert.ok(countTextTokens('世界 👋') > 0);
  assert.ok(countTextTokens('<|endoftext|>') > 1, 'source text is not counted as a model control token');
});

test('input estimate covers the exact complete handoff, including formatting and setup prompt', () => {
  const estimate = estimateCodexInput(data);
  const content = buildCodexHandoff(data).content;
  assert.equal(estimate.input, countTextTokens(content));
  assert.equal(estimate.prompt, countTextTokens(CODEX_PROMPT));
  assert.equal(estimate.transcript, countTextTokens(content.slice(CODEX_PROMPT.length + 2)));
  assert.ok(estimate.transcript > countTextTokens(data.transcript_lines.map((line) => line.text).join('\n')));
  assert.ok(estimate.input > estimate.transcript);
});

test('each extraction receives a new estimate, including long and automatic caption tracks', () => {
  const long = { ...data, source: 'automatic', transcript_lines: Array.from({ length: 1104 }, (_, i) => ({ start: i * 6, duration: 5.12, text: `Caption ${i + 1}: original source text.` })) };
  const estimate = estimateCodexInput(long);
  assert.equal(estimate.input, countTextTokens(buildCodexHandoff(long).content));
  assert.ok(estimate.input > estimateCodexInput(data).input);
  assert.throws(() => estimateCodexInput({ ...data, transcript_lines: [] }), /empty/);
});
