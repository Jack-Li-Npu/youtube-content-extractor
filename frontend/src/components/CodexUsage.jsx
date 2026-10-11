import { useEffect, useRef, useState } from 'react';

export default function CodexUsage({ data, enabled = true }) {
  const [estimate, setEstimate] = useState(null);
  const completed = useRef(null);
  useEffect(() => {
    // A restored transcript in a hidden channel should not load the tokenizer.
    if (!enabled || completed.current?.data === data) return;
    let active = true;
    let worker;
    new Promise((resolve, reject) => {
      worker = new Worker(new URL('../lib/token-estimate.worker.js', import.meta.url), { type: 'module' });
      worker.onmessage = ({ data: result }) => result.error ? reject(new Error('Estimate failed')) : resolve(result);
      worker.onerror = (event) => { event.preventDefault(); reject(new Error('Estimate failed')); };
      worker.postMessage(data);
    }).then((value) => {
      if (active) { completed.current = { data, value }; setEstimate(completed.current); }
    }).catch(() => {
      if (active) { completed.current = { data, value: null }; setEstimate(completed.current); }
    }).finally(() => worker?.terminate());
    return () => { active = false; worker?.terminate(); };
  }, [data, enabled]);

  const value = estimate?.data === data ? estimate.value : undefined;
  return (
    <div className="handoff-usage" aria-label="Estimated Codex token usage">
      <p className="usage-count" role="status">
        <span>Estimated Codex input</span>
        <strong>{value === undefined ? 'Counting tokens…' : value === null ? 'Estimate unavailable' : `≈ ${value.input.toLocaleString()} tokens`}</strong>
      </p>
      {value && <p className="usage-breakdown">Transcript & timestamps: ≈ {value.transcript.toLocaleString()} · Prompt: ≈ {value.prompt.toLocaleString()}</p>}
      <p className="usage-note">Screenshots, reasoning, tool results, and the AI reply add usage. Your model and existing chat also affect the total.</p>
      <details className="handoff-details usage-details">
        <summary>About token usage</summary>
        <p>Tokens are units of text an AI reads and writes. This local estimate covers the complete copied or downloaded text; your selected model may count it differently. Extraction makes no AI-service requests; optional Douyin speech recognition runs locally.</p>
        <p>For a lighter analysis, add “Give me a caption-only brief; skip screenshots.” Attaching the download instead of pasting includes the same text and does not reduce its token count.</p>
        <a href="https://learn.chatgpt.com/docs/pricing" target="_blank" rel="noopener noreferrer">Check Codex usage and plan guidance</a>
      </details>
    </div>
  );
}
