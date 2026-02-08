import { create } from 'zustand';

interface BetRecord {
  bot_id: string;
  bot_name: string;
  bot_avatar_seed: string;
  bet_type: string;
  bet_value?: number;
  amount: number;
  payout: number;
  is_winner: boolean;
}

interface RoundResult {
  round_id: string;
  round_number: number;
  result_number: number;
  result_color: string;
  bets: BetRecord[];
  total_wagered: number;
  total_payout: number;
}

interface LeaderboardEntry {
  bot_id: string;
  name: string;
  avatar_seed: string;
  avatar_style: string;
  balance: number;
  total_wagered: number;
  total_won: number;
  rounds_played: number;
  trend: string;
}

interface GameState {
  phase: 'idle' | 'betting' | 'spinning' | 'settlement' | 'pause';
  timeRemaining: number;
  roundNumber: number;
  tableId: string;
  seatedBots: Array<{ bot_id: string; name: string; avatar_seed: string; avatar_style: string }>;
  currentBets: BetRecord[];
  latestResult: RoundResult | null;
  resultHistory: number[];
  leaderboard: LeaderboardEntry[];
  connected: boolean;

  setPhase: (phase: GameState['phase'], timeRemaining: number) => void;
  setTableState: (data: any) => void;
  addBet: (bet: BetRecord) => void;
  setResult: (result: RoundResult) => void;
  setLeaderboard: (entries: LeaderboardEntry[]) => void;
  setConnected: (connected: boolean) => void;
  addToHistory: (number: number) => void;
}

export const useGameStore = create<GameState>()((set) => ({
  phase: 'idle',
  timeRemaining: 0,
  roundNumber: 0,
  tableId: 'main',
  seatedBots: [],
  currentBets: [],
  latestResult: null,
  resultHistory: [],
  leaderboard: [],
  connected: false,

  setPhase: (phase, timeRemaining) => set({ phase, timeRemaining }),

  setTableState: (data) => set((state) => {
    const incomingBets = data.current_bets || [];
    const phase = data.phase || 'idle';
    // During spinning/settlement, preserve existing bets if server sends empty list
    // (bets placed during betting phase should remain visible)
    const shouldPreserveBets = (phase === 'spinning' || phase === 'settlement')
      && incomingBets.length === 0 && state.currentBets.length > 0;

    return {
      phase,
      timeRemaining: data.time_remaining || 0,
      roundNumber: data.round_number || 0,
      seatedBots: data.seated_bots || [],
      currentBets: shouldPreserveBets ? state.currentBets : incomingBets,
    };
  }),

  addBet: (bet) => set((state) => {
    // Deduplicate: skip if identical bet already exists (same bot, type, value, amount)
    const isDuplicate = state.currentBets.some(
      (b) => b.bot_id === bet.bot_id && b.bet_type === bet.bet_type
        && b.bet_value === bet.bet_value && b.amount === bet.amount
    );
    if (isDuplicate) return state;
    return { currentBets: [...state.currentBets, bet] };
  }),

  setResult: (result) => set((state) => {
    // Deduplicate: skip if this round was already recorded
    if (state.latestResult?.round_number === result.round_number) return state;
    return {
      latestResult: result,
      resultHistory: [result.result_number, ...state.resultHistory].slice(0, 20),
      currentBets: [],
    };
  }),

  setLeaderboard: (entries) => set({ leaderboard: entries }),
  setConnected: (connected) => set({ connected }),
  addToHistory: (number) => set((state) => ({
    resultHistory: [number, ...state.resultHistory].slice(0, 20),
  })),
}));
