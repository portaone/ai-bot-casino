import { useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useGameStore } from '@/store/gameStore';
import { spectatorApi } from '@/api/spectator';
import { PhaseIndicator } from '@/components/PhaseIndicator';
import { RouletteWheel } from '@/components/RouletteWheel';
import { ResultHistory } from '@/components/ResultHistory';
import { TableInfo } from '@/components/TableInfo';
import { BetFeed } from '@/components/BetFeed';
import { Leaderboard } from '@/components/Leaderboard';

export function SpectatorDashboard() {
  const { connected } = useWebSocket();
  const { phase, latestResult, setLeaderboard } = useGameStore();

  useEffect(() => {
    // Fetch initial leaderboard data
    const fetchLeaderboard = async () => {
      try {
        const response = await spectatorApi.getLeaderboard();
        if (response.data.leaderboard) {
          setLeaderboard(response.data.leaderboard);
        }
      } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
      }
    };

    fetchLeaderboard();
  }, [setLeaderboard]);

  return (
    <div className="min-h-screen bg-void">
      {/* Connection Status Bar */}
      <div className="border-b border-white/5 bg-surface">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-display font-bold text-text-primary">
              Live Roulette Table
            </h1>
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  connected ? 'bg-neon animate-pulse' : 'bg-accent-red'
                }`}
              ></div>
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">
                {connected ? 'LIVE' : 'CONNECTING...'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left Column - Game View */}
          <div className="lg:w-[360px] flex-shrink-0 space-y-6">
            <PhaseIndicator />
            <RouletteWheel
              spinning={phase === 'spinning'}
              resultNumber={latestResult?.result_number ?? null}
            />
            <ResultHistory />
            <TableInfo />
          </div>

          {/* Right Column - Activity Feed */}
          <div className="flex-1 space-y-6">
            <BetFeed />
            <Leaderboard />
          </div>
        </div>
      </div>
    </div>
  );
}
