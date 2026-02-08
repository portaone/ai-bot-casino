import { useGameStore } from '@/store/gameStore';
import { BotAvatar } from './BotAvatar';
import { Trophy, X, MessageCircle } from 'lucide-react';
import { getColor } from '@/tokens';

interface RoundResultData {
  round_number: number;
  result_number: number;
  result_color: string;
  bets: Array<{
    bot_id: string;
    bot_name: string;
    bot_avatar_seed: string;
    bet_type: string;
    bet_value?: number;
    amount: number;
    payout: number;
    is_winner: boolean;
  }>;
  total_wagered: number;
  total_payout: number;
}

function RoundResultView({ result, onClose }: { result: RoundResultData; onClose?: () => void }) {
  const bets = result.bets;
  const winners = bets.filter((b) => b.is_winner);
  const losers = bets.filter((b) => !b.is_winner);

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="text-xs text-text-muted font-mono tracking-wider">
            ROUND #{result.round_number} RESULTS
          </div>
          <div
            className="w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold text-white font-mono"
            style={{ background: getColor(result.result_number) }}
          >
            {result.result_number}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors p-1"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      <div className="space-y-2 overflow-y-auto max-h-[400px]">
        {bets.length === 0 ? (
          <div className="text-text-muted text-sm py-4 text-center">
            No bets were placed this round
          </div>
        ) : (
          <>
            {winners.map((bet, i) => {
              const net = bet.payout - bet.amount;
              return (
                <div key={`w-${i}`} className="flex items-center gap-3 bg-neon/5 border border-neon/20 rounded-lg px-3 py-2">
                  <BotAvatar seed={bet.bot_avatar_seed} size={28} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-text-primary truncate flex items-center gap-1.5">
                      {bet.bot_name}
                      <Trophy className="w-3.5 h-3.5 text-gold" />
                    </div>
                  </div>
                  <div className="text-right flex items-baseline gap-2">
                    <span className={`text-xs font-medium ${getBetColor(bet.bet_type)}`}>
                      {formatBetType(bet.bet_type, bet.bet_value)}
                    </span>
                    <span className="text-sm font-bold text-neon font-mono">
                      +{net} BC
                    </span>
                  </div>
                </div>
              );
            })}
            {losers.map((bet, i) => (
              <div key={`l-${i}`} className="flex items-center gap-3 bg-surface/50 rounded-lg px-3 py-2 opacity-70">
                <BotAvatar seed={bet.bot_avatar_seed} size={28} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-text-secondary truncate">{bet.bot_name}</div>
                </div>
                <div className="text-right flex items-baseline gap-2">
                  <span className={`text-xs font-medium ${getBetColor(bet.bet_type)}`}>
                    {formatBetType(bet.bet_type, bet.bet_value)}
                  </span>
                  <span className="text-sm font-bold text-accent-red font-mono">
                    -{bet.amount} BC
                  </span>
                </div>
              </div>
            ))}
          </>
        )}
        {/* Summary line */}
        <div className="pt-2 mt-2 border-t border-white/5 flex justify-between text-xs font-mono text-text-muted">
          <span>Wagered: {result.total_wagered} BC</span>
          <span>Paid out: {result.total_payout} BC</span>
        </div>
      </div>
    </div>
  );
}

export function BetFeed() {
  const phase = useGameStore((s) => s.phase);
  const currentBets = useGameStore((s) => s.currentBets);
  const chatMessages = useGameStore((s) => s.chatMessages);
  const latestResult = useGameStore((s) => s.latestResult);
  const selectedRound = useGameStore((s) => s.selectedRound);
  const selectRound = useGameStore((s) => s.selectRound);

  // If a past round is selected from ResultHistory, show it
  if (selectedRound) {
    return <RoundResultView result={selectedRound} onClose={() => selectRound(null)} />;
  }

  // During settlement/pause, show latest round results
  const showResults = (phase === 'settlement' || phase === 'pause') && latestResult && latestResult.bets.length > 0;

  if (showResults) {
    return <RoundResultView result={latestResult} />;
  }

  // Build a combined feed of bets and chat messages, most recent first
  type FeedItem =
    | { kind: 'bet'; data: typeof currentBets[0]; ts: number }
    | { kind: 'chat'; data: typeof chatMessages[0]; ts: number };

  const feedItems: FeedItem[] = [
    ...currentBets.map((b, i) => ({ kind: 'bet' as const, data: b, ts: i })),
    ...chatMessages.slice(-15).map((m) => ({ kind: 'chat' as const, data: m, ts: m.timestamp })),
  ];

  // Sort: bets first (by order), then interleave chats by timestamp
  // For display: reverse so newest is at top, limit to 15
  const displayItems = feedItems.slice(-15).reverse();

  const emptyMessage = phase === 'betting'
    ? 'Waiting for bets...'
    : phase === 'spinning'
      ? 'No bets this round'
      : 'Waiting for next round...';

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
      <div className="flex items-center gap-2 mb-3">
        <div className="text-xs text-text-muted font-mono tracking-wider">LIVE BETS</div>
        {chatMessages.length > 0 && (
          <>
            <span className="text-text-muted text-xs">&</span>
            <div className="flex items-center gap-1 text-xs text-text-muted font-mono tracking-wider">
              <MessageCircle className="w-3 h-3" />
              CHAT
            </div>
          </>
        )}
      </div>
      <div className="space-y-2 overflow-y-auto max-h-[400px]">
        {displayItems.length === 0 ? (
          <div className="text-text-muted text-sm py-4 text-center">
            {emptyMessage}
          </div>
        ) : (
          displayItems.map((item, i) => {
            if (item.kind === 'bet') {
              const bet = item.data;
              return (
                <div key={`bet-${i}`} className="flex items-center gap-3 bg-surface/50 rounded-lg px-3 py-2 animate-slide-in">
                  <BotAvatar seed={bet.bot_avatar_seed} size={28} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-text-primary truncate">{bet.bot_name}</div>
                  </div>
                  <div className="text-right flex items-baseline gap-2">
                    <span className={`text-xs font-medium ${getBetColor(bet.bet_type)}`}>
                      {formatBetType(bet.bet_type, bet.bet_value)}
                    </span>
                    <span className="text-sm font-bold text-gold font-mono">
                      {bet.amount} BC
                    </span>
                  </div>
                </div>
              );
            } else {
              const msg = item.data;
              return (
                <div key={`chat-${i}`} className="flex items-start gap-3 px-3 py-1.5 animate-slide-in">
                  <BotAvatar seed={msg.bot_avatar_seed} size={22} />
                  <div className="flex-1 min-w-0">
                    <span className="text-xs text-text-muted font-mono">{msg.bot_name}:</span>
                    <span className="text-xs text-text-secondary ml-1.5">{msg.message}</span>
                  </div>
                </div>
              );
            }
          })
        )}
      </div>
    </div>
  );
}

function formatBetType(type: string, value?: number): string {
  if (type === 'straight' && value !== undefined) return `Straight ${value}`;
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getBetColor(type: string): string {
  switch (type) {
    case 'red': return 'text-roulette-red';
    case 'black': return 'text-text-primary';
    case 'even':
    case 'odd': return 'text-accent-blue';
    case 'dozen_1':
    case 'dozen_2':
    case 'dozen_3': return 'text-neon';
    case 'straight': return 'text-gold';
    default: return 'text-text-muted';
  }
}
