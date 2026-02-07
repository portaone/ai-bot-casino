import { useEffect, useRef, useCallback } from 'react';
import { config } from '@/config';
import { useGameStore } from '@/store/gameStore';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const { setTableState, addBet, setResult, setLeaderboard, setConnected, setPhase } = useGameStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

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

          case 'round_result':
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
      // Auto-reconnect after 3 seconds
      reconnectTimerRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [setTableState, addBet, setResult, setLeaderboard, setConnected, setPhase]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected: useGameStore((s) => s.connected) };
}
