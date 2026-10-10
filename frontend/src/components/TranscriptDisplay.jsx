import { SearchX } from 'lucide-react';

function HighlightedText({ text, query }) {
  const needle = query.trim();
  if (!needle) return text;
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return text.split(new RegExp(`(${escaped})`, 'giu')).map((part, index) => index % 2 ? <mark key={index}>{part}</mark> : part);
}

export default function TranscriptDisplay({ lines, search = '', linkForTime }) {
  return (
    <div className="transcript-scroll" tabIndex={0} aria-label="Scrollable transcript">
      {!lines.length && <div className="no-matches"><SearchX size={23} /><h3>No matching words</h3><p>Try another phrase or clear your search.</p></div>}
      <ul aria-label="Transcript lines" className="transcript-lines">
        {lines.map((line, index) => (
          <li key={`${line.start}-${index}`} className="transcript-line">
            {linkForTime?.(line.start) ? <a className="caption-time" href={linkForTime(line.start)} target="_blank" rel="noopener noreferrer" aria-label={`Watch at ${line.timestamp}`}>{line.timestamp}</a> : <span className="caption-time">{line.timestamp}</span>}
            <span className="caption-text"><HighlightedText text={line.text} query={search} />{line.quality_flags?.length > 0 && <small className="cue-review" title={line.quality_flags.join(', ')}>Check speech recognition</small>}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
