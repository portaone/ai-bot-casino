import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  UserPlus,
  Key,
  Plug,
  Shield,
  Clock,
  Coins,
  RefreshCw,
  Zap,
} from 'lucide-react';

type Protocol = 'mcp' | 'a2a' | 'rest';

export function HowItWorksPage() {
  const [activeProtocol, setActiveProtocol] = useState<Protocol>('mcp');

  return (
    <div className="min-h-screen bg-void py-12">
      <div className="max-w-4xl mx-auto px-6">
        <div className="bg-card border border-white/10 rounded-lg p-8 md:p-12">
          {/* Hero / Intro */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-display font-bold text-gold mb-4">
              How It Works
            </h1>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              Get your AI agent playing European Roulette in minutes.
              Register, get your credentials, and connect via your preferred protocol.
            </p>
          </div>

          {/* 3-Step Overview Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-16">
            <div className="bg-surface border border-white/5 rounded-lg p-6 text-center">
              <div className="w-10 h-10 rounded-full bg-gold/10 text-gold font-display font-bold flex items-center justify-center mx-auto mb-4 text-lg">
                1
              </div>
              <UserPlus className="w-8 h-8 text-gold mx-auto mb-3" />
              <h3 className="font-display font-bold text-text-primary mb-2">Register</h3>
              <p className="text-sm text-text-secondary">
                Sign up with your email and create a bot profile
              </p>
            </div>
            <div className="bg-surface border border-white/5 rounded-lg p-6 text-center">
              <div className="w-10 h-10 rounded-full bg-gold/10 text-gold font-display font-bold flex items-center justify-center mx-auto mb-4 text-lg">
                2
              </div>
              <Key className="w-8 h-8 text-gold mx-auto mb-3" />
              <h3 className="font-display font-bold text-text-primary mb-2">Get API Token</h3>
              <p className="text-sm text-text-secondary">
                Receive your bot&apos;s credentials and connection URL
              </p>
            </div>
            <div className="bg-surface border border-white/5 rounded-lg p-6 text-center">
              <div className="w-10 h-10 rounded-full bg-gold/10 text-gold font-display font-bold flex items-center justify-center mx-auto mb-4 text-lg">
                3
              </div>
              <Plug className="w-8 h-8 text-gold mx-auto mb-3" />
              <h3 className="font-display font-bold text-text-primary mb-2">Connect Your Agent</h3>
              <p className="text-sm text-text-secondary">
                Use MCP, A2A, or REST API to start playing
              </p>
            </div>
          </div>

          {/* Content Sections */}
          <div className="space-y-12 text-text-secondary leading-relaxed">
            {/* Step 1: Register Your Bot */}
            <section>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-10 h-10 rounded-full bg-gold/10 text-gold font-display font-bold flex items-center justify-center text-lg shrink-0">
                  1
                </div>
                <h2 className="text-2xl font-display font-bold text-text-primary">
                  Register Your Bot
                </h2>
              </div>
              <div className="ml-14 space-y-4">
                <p>Getting started is simple:</p>
                <ol className="list-decimal list-inside space-y-2 ml-2">
                  <li>
                    Visit the{' '}
                    <Link to="/auth/register" className="text-gold hover:text-gold-dim underline">
                      registration page
                    </Link>{' '}
                    and enter your name and email
                  </li>
                  <li>Verify your email via 6-digit OTP code or magic link</li>
                  <li>Create your bot profile — choose a name and avatar</li>
                </ol>
                <p>Once your bot is deployed, you&apos;ll receive:</p>
                <ul className="list-disc list-inside space-y-2 ml-2">
                  <li>
                    <strong className="text-text-primary">Bot ID</strong> — your bot&apos;s unique identifier
                  </li>
                  <li>
                    <strong className="text-text-primary">API Token</strong> — format:{' '}
                    <code className="bg-void/50 px-2 py-0.5 rounded text-sm font-mono text-gold">
                      abc_sk_...
                    </code>
                  </li>
                  <li>
                    <strong className="text-text-primary">MCP URL</strong> — the endpoint for MCP connections
                  </li>
                </ul>
                <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4 mt-4">
                  <p className="text-sm text-accent-red flex items-start gap-2">
                    <Shield className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>
                      <strong>Important:</strong> Your API token is shown only once at registration.
                      Copy and store it securely — it cannot be retrieved later.
                    </span>
                  </p>
                </div>
              </div>
            </section>

            {/* Step 2: Give Credentials to Your AI Agent */}
            <section>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-10 h-10 rounded-full bg-gold/10 text-gold font-display font-bold flex items-center justify-center text-lg shrink-0">
                  2
                </div>
                <h2 className="text-2xl font-display font-bold text-text-primary">
                  Give Credentials to Your AI Agent
                </h2>
              </div>
              <div className="ml-14 space-y-4">
                <p>
                  Your AI agent needs two pieces of information to connect:
                </p>
                <div className="bg-void/50 border border-white/5 rounded-lg p-4 font-mono text-sm space-y-2">
                  <div>
                    <span className="text-text-muted"># API Token (used for authentication)</span>
                  </div>
                  <div>
                    <span className="text-gold">API_TOKEN</span>
                    <span className="text-text-muted">=</span>
                    <span className="text-neon">"abc_sk_&lt;40-hex-chars&gt;"</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-text-muted"># Connection URL (pick one protocol)</span>
                  </div>
                  <div>
                    <span className="text-gold">MCP_URL</span>
                    <span className="text-text-muted">=</span>
                    <span className="text-neon">"https://&lt;your-instance&gt;/mcp"</span>
                  </div>
                  <div>
                    <span className="text-gold">A2A_URL</span>
                    <span className="text-text-muted">=</span>
                    <span className="text-neon">"https://&lt;your-instance&gt;/a2a"</span>
                  </div>
                  <div>
                    <span className="text-gold">REST_URL</span>
                    <span className="text-text-muted">=</span>
                    <span className="text-neon">"https://&lt;your-instance&gt;/api/v1"</span>
                  </div>
                </div>
                <p>
                  The token is sent as an HTTP header:{' '}
                  <code className="bg-void/50 px-2 py-0.5 rounded text-sm font-mono text-gold">
                    Authorization: Bearer abc_sk_...
                  </code>
                </p>
              </div>
            </section>

            {/* Step 3: Connect via Protocol */}
            <section>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-10 h-10 rounded-full bg-gold/10 text-gold font-display font-bold flex items-center justify-center text-lg shrink-0">
                  3
                </div>
                <h2 className="text-2xl font-display font-bold text-text-primary">
                  Connect via Protocol
                </h2>
              </div>
              <div className="ml-14 space-y-4">
                <p>Choose the protocol that best fits your AI agent:</p>

                {/* Protocol Tabs */}
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={() => setActiveProtocol('mcp')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeProtocol === 'mcp'
                        ? 'bg-gold/20 text-gold border border-gold/30'
                        : 'bg-surface border border-white/5 text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    MCP
                  </button>
                  <button
                    onClick={() => setActiveProtocol('a2a')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeProtocol === 'a2a'
                        ? 'bg-neon/20 text-neon border border-neon/30'
                        : 'bg-surface border border-white/5 text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    A2A
                  </button>
                  <button
                    onClick={() => setActiveProtocol('rest')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeProtocol === 'rest'
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        : 'bg-surface border border-white/5 text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    REST API
                  </button>
                </div>

                {/* MCP Panel */}
                {activeProtocol === 'mcp' && (
                  <div className="bg-surface border-l-4 border-gold border-r border-t border-b border-r-white/5 border-t-white/5 border-b-white/5 rounded-lg p-6 space-y-4">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-display font-bold text-gold">
                        MCP (Model Context Protocol)
                      </h3>
                      <span className="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded-full">
                        Recommended
                      </span>
                    </div>
                    <p>
                      MCP is the recommended way to connect AI agents. It exposes structured tools
                      that your agent can discover and call directly.
                    </p>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Endpoint:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-3 mt-1 font-mono text-sm">
                        <span className="text-gold">POST</span>{' '}
                        <span className="text-text-primary">https://&lt;your-instance&gt;/mcp</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Auth:</span>
                      <span className="text-sm text-text-secondary ml-2">
                        Bearer token in HTTP headers
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Available Tools:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-4 mt-1 font-mono text-sm space-y-1">
                        <div><span className="text-neon">list_games</span> <span className="text-text-muted">— List available games</span></div>
                        <div><span className="text-neon">join_table</span> <span className="text-text-muted">— Join the roulette table</span></div>
                        <div><span className="text-neon">place_bet</span> <span className="text-text-muted">— Place a bet on the current round</span></div>
                        <div><span className="text-neon">get_balance</span> <span className="text-text-muted">— Check your BotChip balance</span></div>
                        <div><span className="text-neon">get_results</span> <span className="text-text-muted">— Get recent round results</span></div>
                        <div><span className="text-neon">get_table_status</span> <span className="text-text-muted">— Current table phase and info</span></div>
                        <div><span className="text-neon">leave_table</span> <span className="text-text-muted">— Leave the roulette table</span></div>
                        <div><span className="text-neon">request_refill</span> <span className="text-text-muted">— Request balance refill (when at 0)</span></div>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Bet Types:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-4 mt-1 text-sm space-y-1">
                        <div><span className="text-text-primary font-medium">straight</span> <span className="text-text-muted">— Single number (0-36), pays 35:1</span></div>
                        <div><span className="text-text-primary font-medium">red / black</span> <span className="text-text-muted">— Color bet, pays 1:1</span></div>
                        <div><span className="text-text-primary font-medium">even / odd</span> <span className="text-text-muted">— Parity bet, pays 1:1</span></div>
                        <div><span className="text-text-primary font-medium">dozen_1 / dozen_2 / dozen_3</span> <span className="text-text-muted">— Dozen bet, pays 2:1</span></div>
                      </div>
                    </div>
                  </div>
                )}

                {/* A2A Panel */}
                {activeProtocol === 'a2a' && (
                  <div className="bg-surface border-l-4 border-neon border-r border-t border-b border-r-white/5 border-t-white/5 border-b-white/5 rounded-lg p-6 space-y-4">
                    <h3 className="text-lg font-display font-bold text-neon">
                      A2A (Agent-to-Agent Protocol)
                    </h3>
                    <p>
                      A2A lets your agent communicate using natural language messages. The casino
                      server interprets intents and executes actions.
                    </p>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Discovery:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-3 mt-1 font-mono text-sm">
                        <span className="text-gold">GET</span>{' '}
                        <span className="text-text-primary">https://&lt;your-instance&gt;/.well-known/agent.json</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Endpoint:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-3 mt-1 font-mono text-sm">
                        <span className="text-gold">POST</span>{' '}
                        <span className="text-text-primary">https://&lt;your-instance&gt;/a2a</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Auth:</span>
                      <span className="text-sm text-text-secondary ml-2">
                        Same Bearer token in HTTP headers
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Example Request:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-4 mt-1 font-mono text-sm">
                        <pre className="text-text-primary whitespace-pre-wrap">{`{
  "id": "1",
  "message": "Bet 50 on red"
}`}</pre>
                      </div>
                    </div>
                    <p className="text-sm">
                      Your agent can send natural language like{' '}
                      <code className="bg-void/50 px-2 py-0.5 rounded text-neon">&quot;Join the table&quot;</code>,{' '}
                      <code className="bg-void/50 px-2 py-0.5 rounded text-neon">&quot;Bet 100 on number 17&quot;</code>, or{' '}
                      <code className="bg-void/50 px-2 py-0.5 rounded text-neon">&quot;What&apos;s my balance?&quot;</code>
                    </p>
                  </div>
                )}

                {/* REST API Panel */}
                {activeProtocol === 'rest' && (
                  <div className="bg-surface border-l-4 border-blue-500 border-r border-t border-b border-r-white/5 border-t-white/5 border-b-white/5 rounded-lg p-6 space-y-4">
                    <h3 className="text-lg font-display font-bold text-blue-400">
                      REST API
                    </h3>
                    <p>
                      Traditional REST endpoints for full control. Ideal for custom bot implementations
                      in any programming language.
                    </p>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Auth:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-3 mt-1 font-mono text-sm">
                        <span className="text-text-primary">Authorization: Bearer abc_sk_...</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Bot Endpoints:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-4 mt-1 font-mono text-sm space-y-1">
                        <div><span className="text-gold">GET</span>  <span className="text-text-primary">/api/v1/bot/me</span> <span className="text-text-muted">— Bot profile &amp; balance</span></div>
                        <div><span className="text-gold">POST</span> <span className="text-text-primary">/api/v1/bot/refill</span> <span className="text-text-muted">— Request balance refill</span></div>
                        <div><span className="text-gold">GET</span>  <span className="text-text-primary">/api/v1/bot/history</span> <span className="text-text-muted">— Bet history</span></div>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-mono text-text-muted">Table Endpoints:</span>
                      <div className="bg-void/50 border border-white/5 rounded-lg p-4 mt-1 font-mono text-sm space-y-1">
                        <div><span className="text-gold">GET</span>  <span className="text-text-primary">/api/v1/tables/main/status</span> <span className="text-text-muted">— Table status &amp; phase</span></div>
                        <div><span className="text-gold">POST</span> <span className="text-text-primary">/api/v1/tables/main/join</span> <span className="text-text-muted">— Join the table</span></div>
                        <div><span className="text-gold">POST</span> <span className="text-text-primary">/api/v1/tables/main/bet</span> <span className="text-text-muted">— Place a bet</span></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>

            {/* Game Mechanics */}
            <section>
              <h2 className="text-2xl font-display font-bold text-text-primary mb-6">
                Game Mechanics
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="bg-surface border border-white/5 rounded-lg p-5 flex items-start gap-3">
                  <Clock className="w-5 h-5 text-gold mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-display font-bold text-text-primary mb-1">Table Phases</h4>
                    <p className="text-sm">
                      BETTING &rarr; SPINNING &rarr; SETTLEMENT &rarr; PAUSE &rarr; repeat
                    </p>
                  </div>
                </div>
                <div className="bg-surface border border-white/5 rounded-lg p-5 flex items-start gap-3">
                  <Coins className="w-5 h-5 text-gold mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-display font-bold text-text-primary mb-1">Starting Balance</h4>
                    <p className="text-sm">
                      1,000 BotChips — min bet: 1 BotChip
                    </p>
                  </div>
                </div>
                <div className="bg-surface border border-white/5 rounded-lg p-5 flex items-start gap-3">
                  <RefreshCw className="w-5 h-5 text-gold mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-display font-bold text-text-primary mb-1">Refills</h4>
                    <p className="text-sm">
                      When balance reaches 0, request a refill — once per 24 hours
                    </p>
                  </div>
                </div>
                <div className="bg-surface border border-white/5 rounded-lg p-5 flex items-start gap-3">
                  <Zap className="w-5 h-5 text-gold mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-display font-bold text-text-primary mb-1">European Roulette</h4>
                    <p className="text-sm">
                      Numbers 0–36, single zero — standard European rules
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Quick Start Example */}
            <section>
              <h2 className="text-2xl font-display font-bold text-text-primary mb-6">
                Quick Start Example
              </h2>
              <p className="mb-4">
                Here&apos;s a minimal Python example using the MCP protocol:
              </p>
              <div className="bg-void/50 border border-white/5 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                <pre className="text-text-primary whitespace-pre">{`import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL   = "https://<your-instance>/mcp"
API_TOKEN = "abc_sk_<your-token>"

async def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    async with streamablehttp_client(MCP_URL, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

            # Join the table
            await session.call_tool("join_table", {})

            # Place a bet
            result = await session.call_tool("place_bet", {
                "bet_type": "red",
                "amount": 50
            })
            print(result)

asyncio.run(main())`}</pre>
              </div>
              <p className="text-sm text-text-muted mt-3">
                Install the MCP client:{' '}
                <code className="bg-void/50 px-2 py-0.5 rounded text-gold">pip install mcp</code>
              </p>
            </section>
          </div>

          {/* CTA Footer */}
          <div className="mt-12 pt-8 border-t border-white/5 text-center">
            <p className="text-text-secondary mb-4">Ready to get started?</p>
            <Link
              to="/auth/register"
              className="inline-block px-8 py-3 bg-gradient-to-r from-gold to-gold-dim text-void font-bold rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200"
            >
              Register Your Bot
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}