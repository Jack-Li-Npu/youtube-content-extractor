import { useRef } from 'react';
import { Music2, Youtube } from 'lucide-react';
import { CHANNELS } from '../lib/channels';

const platforms = Object.keys(CHANNELS);

export default function ChannelTabs({ platform, onSelect, statuses }) {
  const tabs = useRef({});
  function navigate(event, current) {
    const index = platforms.indexOf(current);
    const next = event.key === 'ArrowRight' ? platforms[(index + 1) % platforms.length]
      : event.key === 'ArrowLeft' ? platforms[(index + platforms.length - 1) % platforms.length]
      : event.key === 'Home' ? platforms[0] : event.key === 'End' ? platforms.at(-1) : null;
    if (!next) return;
    event.preventDefault();
    onSelect(next);
    tabs.current[next]?.focus();
  }

  return (
    <div className="channel-tabs" role="tablist" aria-label="Video platform">
      {platforms.map((name) => {
        const Icon = name === 'youtube' ? Youtube : Music2;
        return <button key={name} id={`${name}-tab`} ref={(node) => { tabs.current[name] = node; }} role="tab" aria-controls={`${name}-panel`} aria-selected={platform === name} tabIndex={platform === name ? 0 : -1} className="channel-tab" onClick={() => onSelect(name)} onKeyDown={(event) => navigate(event, name)}>
          <Icon size={21} aria-hidden="true" />
          <span className="channel-tab-copy"><span className="channel-name">{CHANNELS[name].name}</span><span className="channel-summary">{CHANNELS[name].summary}</span></span>
          {statuses[name] && <span className={`channel-status ${statuses[name].startsWith('Needs') ? 'needs-action' : ''}`}>{statuses[name]}</span>}
        </button>;
      })}
    </div>
  );
}
