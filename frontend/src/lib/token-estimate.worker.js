import { estimateCodexInput } from './token-estimate.js';

self.onmessage = ({ data }) => {
  try {
    self.postMessage(estimateCodexInput(data));
  } catch {
    self.postMessage({ error: true });
  }
};
