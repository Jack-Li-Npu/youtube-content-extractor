import { Check, Circle, ExternalLink } from 'lucide-react';
import { isRunning, progressSteps } from '../lib/douyin-flow';

export default function DouyinProgress({ job, onShowBrowser, onCancel, busy }) {
  const waiting = job.state === 'waiting_verification';
  const failed = job.state === 'failed';
  return (
    <div className="douyin-progress" aria-label="Douyin extraction progress">
      <p className="eyebrow">One video. One flow.</p>
      <h3>{waiting ? 'Verify on Douyin, then return here.' : failed ? 'The next step needs attention.' : job.state === 'cancelled' ? 'Extraction cancelled.' : 'Your transcript is on its way.'}</h3>
      <p className={failed ? 'progress-error' : ''} role="status">{job.message}</p>
      <ol className="progress-steps">
        {progressSteps(job).map((step, index) => <li key={step.label} className={step.done ? 'is-done' : step.current ? 'is-current' : ''} aria-current={step.current ? 'step' : undefined}>
          <span className="progress-symbol">{step.done ? <Check size={15} /> : step.current ? <Circle size={13} /> : String(index + 1).padStart(2, '0')}</span>
          <span>{step.label}</span>
        </li>)}
      </ol>
      {waiting && <div className="progress-guidance"><p>Complete any login or identity check yourself on Douyin’s official page. When the video plays, click <strong>Verified — extract transcript</strong> on the left. Acquisition, speech recognition, and the Codex file will follow automatically.</p><button className="button button-outline" disabled={busy} onClick={onShowBrowser}><ExternalLink size={15} />Show Douyin window</button></div>}
      {failed && <p className="progress-guidance">{job.can_retry_speech ? 'Click Retry speech recognition on the left. The acquired video is kept, so no new login or download is needed.' : 'Follow the instruction above, then click Retry extraction on the left.'}</p>}
      {job.diagnostic && <details className="progress-diagnostic"><summary>Error details</summary><p>Code: {job.diagnostic.code}{job.diagnostic.worker_exit_code != null && ` · Worker exit: ${job.diagnostic.worker_exit_code}`}</p></details>}
      {isRunning(job) && <button className="text-button cancel-extraction" disabled={busy} onClick={onCancel}>Cancel extraction</button>}
      <p className="progress-footnote">You can reload this page and return to the current job while the extractor stays running.</p>
    </div>
  );
}
