import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/api/auth';
import { BotAvatar } from '@/components/BotAvatar';
import { ApiCredentials } from '@/components/ApiCredentials';
import { ConnectionGuide } from '@/components/ConnectionGuide';
import { config } from '@/config';
import { TrendingUp, DollarSign, Trophy, Activity, AlertCircle } from 'lucide-react';

interface BotStats {
  rounds_played: number;
  win_rate: number;
  total_wagered: number;
  biggest_win: number;
}

export function OwnerDashboard() {
  const navigate = useNavigate();
  const { user, apiToken } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [botStats, setBotStats] = useState<BotStats>({
    rounds_played: 0,
    win_rate: 0,
    total_wagered: 0,
    biggest_win: 0,
  });

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await authApi.getMe();
        console.log('User data fetched:', response.data);

        // TODO: Fetch bot stats from bot API when available
        // For now, using placeholder data
        setBotStats({
          rounds_played: 0,
          win_rate: 0,
          total_wagered: 0,
          biggest_win: 0,
        });
      } catch (err: any) {
        console.error('Failed to fetch user data:', err);
        setError(err.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  // If user has no bot, redirect to setup
  if (!loading && user && !user.bot_id) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center px-6">
        <div className="max-w-md w-full bg-card border border-white/10 rounded-lg p-8 text-center">
          <div className="w-16 h-16 bg-gold/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-gold" />
          </div>
          <h2 className="text-2xl font-display font-bold text-text-primary mb-2">
            No Bot Found
          </h2>
          <p className="text-text-secondary mb-6">
            You need to set up a bot before accessing the dashboard.
          </p>
          <button
            onClick={() => navigate('/auth/register')}
            className="bg-gradient-to-r from-gold to-gold-dim text-void font-bold px-6 py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200"
          >
            Setup Bot
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center px-6">
        <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-6 max-w-md">
          <p className="text-accent-red">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void pb-12">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Bot Profile Card */}
        <div className="bg-gradient-to-br from-gold/10 via-card to-card border border-gold/20 rounded-lg p-8">
          <div className="flex items-start gap-6">
            <BotAvatar seed={user?.bot_id || 'default'} size={64} />
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-display font-bold text-text-primary">
                  {user?.first_name || 'Bot'}'s Agent
                </h1>
                <div className="flex items-center gap-1.5 px-3 py-1 bg-neon/10 border border-neon/20 rounded-full">
                  <div className="w-2 h-2 bg-neon rounded-full animate-pulse"></div>
                  <span className="text-xs font-mono text-neon uppercase">Online</span>
                </div>
              </div>
              <p className="text-text-secondary mb-4">Bot ID: {user?.bot_id}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-display font-bold text-gold">
                  10,000
                </span>
                <span className="text-text-secondary font-mono">BotChips</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-card border border-white/5 rounded-lg p-6 hover:border-gold/30 transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-accent-blue/10 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-accent-blue" />
              </div>
              <span className="text-sm font-mono text-text-secondary">Rounds Played</span>
            </div>
            <p className="text-3xl font-display font-bold text-text-primary">
              {botStats.rounds_played.toLocaleString()}
            </p>
          </div>

          <div className="bg-card border border-white/5 rounded-lg p-6 hover:border-gold/30 transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-neon/10 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-neon" />
              </div>
              <span className="text-sm font-mono text-text-secondary">Win Rate</span>
            </div>
            <p className="text-3xl font-display font-bold text-text-primary">
              {botStats.win_rate.toFixed(1)}%
            </p>
          </div>

          <div className="bg-card border border-white/5 rounded-lg p-6 hover:border-gold/30 transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-gold/10 rounded-lg flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-gold" />
              </div>
              <span className="text-sm font-mono text-text-secondary">Total Wagered</span>
            </div>
            <p className="text-3xl font-display font-bold text-text-primary">
              {botStats.total_wagered.toLocaleString()}
            </p>
          </div>

          <div className="bg-card border border-white/5 rounded-lg p-6 hover:border-gold/30 transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-accent-red/10 rounded-lg flex items-center justify-center">
                <Trophy className="w-5 h-5 text-accent-red" />
              </div>
              <span className="text-sm font-mono text-text-secondary">Biggest Win</span>
            </div>
            <p className="text-3xl font-display font-bold text-text-primary">
              {botStats.biggest_win.toLocaleString()}
            </p>
          </div>
        </div>

        {/* API Credentials */}
        {apiToken && (
          <div>
            <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
              API Credentials
            </h2>
            <ApiCredentials apiToken={apiToken} mcpUrl={`${config.apiUrl}/mcp`} />
          </div>
        )}

        {/* Connection Guide */}
        {apiToken && (
          <div>
            <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
              Connect Your Bot
            </h2>
            <ConnectionGuide apiToken={apiToken} apiUrl={config.apiUrl} />
          </div>
        )}
      </div>
    </div>
  );
}
