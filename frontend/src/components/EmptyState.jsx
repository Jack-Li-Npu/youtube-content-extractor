import { ArrowUpRight, Captions, Clock3, FileText, Monitor } from 'lucide-react';

export default function EmptyState({ platform, hasVideo, onExample }) {
  const douyin = platform === 'douyin';
  return (
    <div className="empty-state">
      <span className="empty-icon" aria-hidden="true">{douyin ? <Monitor size={27} /> : <Captions size={27} />}</span>
      <h3>{hasVideo ? 'Choose a caption track.' : douyin ? 'Your Douyin transcript starts here.' : 'Start with the captions.'}</h3>
      <p className="empty-description">{hasVideo ? 'Select a language in the source panel, then click Get transcript.' : douyin ? 'Open a public video in your local browser. If a check appears, complete it there and return here.' : 'Paste a YouTube link to read its available captions, then copy the full transcript into Codex.'}</p>
      {!douyin && !hasVideo && <button className="text-button" onClick={onExample}>Try an example<ArrowUpRight size={16} /></button>}
      <div className="empty-features">
        <span>{douyin ? <Monitor size={16} /> : <Captions size={16} />}{douyin ? 'Official browser access' : 'Original caption text'}</span>
        <span><Clock3 size={16} />Clickable timestamps</span>
        <span><FileText size={16} />One file for Codex</span>
      </div>
    </div>
  );
}
