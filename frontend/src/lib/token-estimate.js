import { Tiktoken } from 'js-tiktoken/lite';
import o200kBase from 'js-tiktoken/ranks/o200k_base';
import { buildCodexHandoff, CODEX_PROMPT } from './transcript.js';

let encoder;

export function countTextTokens(text) {
  encoder ??= new Tiktoken(o200kBase);
  // Caption text that resembles model control tokens is still ordinary source text.
  return encoder.encode(text, [], []).length;
}

export function estimateCodexInput(data) {
  const { content } = buildCodexHandoff(data);
  return {
    input: countTextTokens(content),
    prompt: countTextTokens(CODEX_PROMPT),
    transcript: countTextTokens(content.slice(CODEX_PROMPT.length + 2)),
  };
}
