import { useState } from 'react';
import { Copy, Check, Eye, EyeOff } from 'lucide-react';

interface ApiCredentialsProps {
  apiToken: string;
  mcpUrl?: string;
}

export function ApiCredentials({ apiToken, mcpUrl }: ApiCredentialsProps) {
  const [showToken, setShowToken] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const copy = async (text: string, label: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 space-y-4">
      <div className="text-xs text-text-muted font-mono tracking-wider">API CREDENTIALS</div>

      {/* API Token */}
      <div>
        <div className="text-xs text-text-secondary mb-1">API Token</div>
        <div className="flex items-center gap-2 bg-surface rounded-lg px-3 py-2">
          <code className="flex-1 text-sm font-mono text-text-primary truncate">
            {showToken ? apiToken : '●'.repeat(Math.min(apiToken.length, 32))}
          </code>
          <button onClick={() => setShowToken(!showToken)} className="text-text-muted hover:text-text-primary">
            {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
          <button onClick={() => copy(apiToken, 'token')} className="text-text-muted hover:text-gold">
            {copied === 'token' ? <Check size={16} className="text-neon" /> : <Copy size={16} />}
          </button>
        </div>
      </div>

      {/* MCP URL */}
      {mcpUrl && (
        <div>
          <div className="text-xs text-text-secondary mb-1">MCP Server URL</div>
          <div className="flex items-center gap-2 bg-surface rounded-lg px-3 py-2">
            <code className="flex-1 text-sm font-mono text-text-primary truncate">{mcpUrl}</code>
            <button onClick={() => copy(mcpUrl, 'mcp')} className="text-text-muted hover:text-gold">
              {copied === 'mcp' ? <Check size={16} className="text-neon" /> : <Copy size={16} />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
