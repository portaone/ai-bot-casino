import { useEffect, useRef, useCallback } from 'react';
import { config } from '@/config';
import { useGameStore } from '@/store/gameStore';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const mountedRef = useRef(true);
  const { setTableState, addBet, addChatMessage, setResult, setLeaderboard, setConnected, setPhase } = useGameStore();

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    // Close any existing connection first to prevent duplicates
    if (wsRef.current) {
      const existing = wsRef.current;
      wsRef.current = null;
      existing.onclose = null; // prevent reconnect from old close handler
      existing.close();
    }

    const wsUrl = `${config.wsUrl}/ws/spectator`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'initial_state':
            if (data.table_status) {
              setTableState(data.table_status);
            }
            if (data.leaderboard) {
              setLeaderboard(data.leaderboard);
            }
            break;

          case 'phase_change':
            setPhase(data.phase, data.time_remaining || 0);
            setTableState(data);
            break;

          case 'new_bet':
            if (data.bet) {
              addBet(data.bet);
            }
            break;

          case 'chat_message':
            addChatMessage({
              bot_id: data.bot_id,
              bot_name: data.bot_name,
              bot_avatar_seed: data.bot_avatar_seed,
              message: data.message,
              timestamp: Date.now(),
            });
            break;

          case 'round_result':
            // Settlement phase — backend doesn't send a separate phase_change for this,
            // so we set the phase here to ensure BetFeed shows results instead of empty bets
            setPhase('settlement', 0);
            setResult({
              round_id: data.round_id,
              round_number: data.round_number,
              result_number: data.result_number,
              result_color: data.result_color,
              bets: data.bets || [],
              total_wagered: data.total_wagered || 0,
              total_payout: data.total_payout || 0,
            });
            if (data.leaderboard) {
              setLeaderboard(data.leaderboard);
            }
            break;
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // Only reconnect if still mounted and this is still the active connection
      if (mountedRef.current && wsRef.current === ws) {
        reconnectTimerRef.current = setTimeout(connect, 3000);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [setTableState, addBet, addChatMessage, setResult, setLeaderboard, setConnected, setPhase]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on cleanup close
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { connected: useGameStore((s) => s.connected) };
}
