import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface ConnectionGuideProps {
  apiToken: string;
  apiUrl?: string;
}

export function ConnectionGuide({ apiToken, apiUrl = 'https://api.aibotcasino.com' }: ConnectionGuideProps) {
  const [activeTab, setActiveTab] = useState<'mcp' | 'a2a' | 'rest'>('mcp');
  const [copied, setCopied] = useState(false);

  const tabs = [
    { id: 'mcp' as const, label: 'MCP' },
    { id: 'a2a' as const, label: 'A2A' },
    { id: 'rest' as const, label: 'REST' },
  ];

  const snippets = {
    mcp: `{
  "mcpServers": {
    "aibotcasino": {
      "url": "${apiUrl}/mcp",
      "headers": {
        "Authorization": "Bearer ${apiToken}"
      }
    }
  }
}`,
    a2a: `# Agent Card
GET ${apiUrl}/.well-known/agent.json

# Send Task
POST ${apiUrl}/a2a
Authorization: Bearer ${apiToken}
Content-Type: application/json

{
  "message": {
    "parts": [{"type": "text", "text": "join the roulette table"}]
  }
}`,
    rest: `# List games
curl ${apiUrl}/api/v1/games \\
  -H "Authorization: Bearer ${apiToken}"

# Join table
curl -X POST ${apiUrl}/api/v1/tables/main/join \\
  -H "Authorization: Bearer ${apiToken}"

# Place bet
curl -X POST ${apiUrl}/api/v1/tables/main/bet \\
  -H "Authorization: Bearer ${apiToken}" \\
  -H "Content-Type: application/json" \\
  -d '{"bet_type":"red","amount":10}'`,
  };

  const copy = async () => {
    await navigator.clipboard.writeText(snippets[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4">
      <div className="text-xs text-text-muted font-mono tracking-wider mb-3">CONNECTION GUIDE</div>

      <div className="flex gap-1 mb-3">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-xs font-mono rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-gold/20 text-gold'
                : 'bg-surface text-text-muted hover:text-text-secondary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="relative">
        <pre className="bg-surface rounded-lg p-3 text-xs font-mono text-text-secondary overflow-x-auto whitespace-pre-wrap">
          {snippets[activeTab]}
        </pre>
        <button
          onClick={copy}
          className="absolute top-2 right-2 text-text-muted hover:text-gold transition-colors"
        >
          {copied ? <Check size={14} className="text-neon" /> : <Copy size={14} />}
        </button>
      </div>
    </div>
  );
}
