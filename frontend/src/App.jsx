import { useCallback, useState } from 'react';
import { Captions } from 'lucide-react';
import Hero from './components/Hero';
import Footer from './components/Footer';
import ChannelTabs from './components/ChannelTabs';
import TranscriptWorkspace from './TranscriptWorkspace';
import { CHANNELS } from './lib/channels';

export default function App() {
  const [platform, setPlatform] = useState('youtube');
  const [statuses, setStatuses] = useState({ youtube: '', douyin: '' });
  const updateStatus = useCallback((channel, status) => {
    setStatuses((current) => current[channel] === status ? current : { ...current, [channel]: status });
  }, []);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      <header className="app-header">
        <div className="brand"><span className="brand-mark"><Captions size={23} /></span><span>Transcript<span className="brand-period">.</span></span></div>
        <span className="local-label">Local workspace</span>
      </header>
      <main id="workspace" tabIndex={-1}>
        <Hero />
        <ChannelTabs platform={platform} onSelect={setPlatform} statuses={statuses} />
        {Object.keys(CHANNELS).map((channel) => (
          <div key={channel} id={`${channel}-panel`} role="tabpanel" aria-labelledby={`${channel}-tab`} hidden={platform !== channel}>
            <TranscriptWorkspace platform={channel} active={platform === channel} onStatus={updateStatus} />
          </div>
        ))}
      </main>
      <Footer />
    </div>
  );
}
