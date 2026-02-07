import apiClient from './client';

export interface LeaderboardEntry {
  bot_id: string;
  name: string;
  avatar_seed: string;
  avatar_style: string;
  balance: number;
  total_wagered: number;
  total_won: number;
  rounds_played: number;
  trend: 'up' | 'down' | 'neutral';
}

export interface TableStatus {
  table_id: string;
  phase: 'idle' | 'betting' | 'spinning' | 'settlement' | 'pause';
  time_remaining: number;
  round_number: number;
  seated_bots: Array<{
    bot_id: string;
    name: string;
    avatar_seed: string;
    avatar_style: string;
  }>;
  bot_count: number;
  max_bots: number;
  current_bets: Array<{
    bot_id: string;
    bot_name: string;
    bot_avatar_seed: string;
    bet_type: string;
    bet_value?: number;
    amount: number;
    payout: number;
    is_winner: boolean;
  }>;
  last_result?: {
    round_id: string;
    result_number: number;
    result_color: string;
    round_number: number;
    bets: Array<any>;
    total_wagered: number;
    total_payout: number;
  };
  total_rounds_today: number;
  total_wagered_today: number;
}

export const spectatorApi = {
  getLeaderboard: () =>
    apiClient.get<{ leaderboard: LeaderboardEntry[]; count: number }>('/api/v1/spectator/leaderboard'),

  getTableStatus: (tableId: string = 'main') =>
    apiClient.get<TableStatus>(`/api/v1/spectator/table/${tableId}/status`),
};
