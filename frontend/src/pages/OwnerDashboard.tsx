import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/api/auth';
import { BotAvatar } from '@/components/BotAvatar';
import { AvatarPicker } from '@/components/AvatarPicker';
import { ApiCredentials } from '@/components/ApiCredentials';
import { ConnectionGuide } from '@/components/ConnectionGuide';
import { config } from '@/config';
import { TrendingUp, DollarSign, Trophy, Activity, Sparkles, CheckCircle, ArrowRight, RefreshCw, AlertTriangle } from 'lucide-react';

interface BotStats {
  rounds_played: number;
  win_rate: number;
  total_wagered: number;
  biggest_win: number;
}

export function OwnerDashboard() {
  const navigate = useNavigate();
  const { user, apiToken, mcpUrl, setAuth, accessToken } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [balance, setBalance] = useState<number | null>(null);
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

        // Update store with fresh user data (includes bot_id and mcp_url)
        if (accessToken) {
          setAuth(accessToken, response.data);
        }
        // Store mcp_url from backend (uses API_PUBLIC_URL setting)
        if (response.data.mcp_url) {
          useAuthStore.setState({ mcpUrl: response.data.mcp_url });
        }
        // Store bot balance
        if (response.data.balance !== undefined) {
          setBalance(response.data.balance);
        }

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

  // Inline bot setup state
  const [botSetupStep, setBotSetupStep] = useState<'form' | 'success'>('form');
  const [botName, setBotName] = useState('');
  const [avatarSeed, setAvatarSeed] = useState('');
  const [botSetupError, setBotSetupError] = useState('');
  const [botSetupLoading, setBotSetupLoading] = useState(false);
  const [newApiToken, setNewApiToken] = useState('');
  const [newMcpUrl, setNewMcpUrl] = useState('');

  // Regenerate token state
  const [regenLoading, setRegenLoading] = useState(false);
  const [regenError, setRegenError] = useState('');
  const [showRegenConfirm, setShowRegenConfirm] = useState(false);

  const handleBotSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setBotSetupError('');

    if (!botName.trim()) {
      setBotSetupError('Please enter a bot name');
      return;
    }
    if (!avatarSeed) {
      setBotSetupError('Please select an avatar');
      return;
    }

    setBotSetupLoading(true);
    try {
      const response = await authApi.setupBot({
        bot_name: botName.trim(),
        avatar_seed: avatarSeed,
      });

      const { setApiToken } = useAuthStore.getState();
      setApiToken(response.data.api_token, response.data.mcp_url);
      setNewApiToken(response.data.api_token);
      setNewMcpUrl(response.data.mcp_url);
      setBotSetupStep('success');

      // Refresh user data so dashboard renders the full view
      const meResponse = await authApi.getMe();
      if (accessToken) {
        setAuth(accessToken, meResponse.data);
      }
    } catch (err: any) {
      setBotSetupError(err.response?.data?.detail || 'Bot setup failed. Please try again.');
    } finally {
      setBotSetupLoading(false);
    }
  };

  const handleRegenerateToken = async () => {
    setRegenLoading(true);
    setRegenError('');
    try {
      const response = await authApi.regenerateToken();
      const { setApiToken } = useAuthStore.getState();
      setApiToken(response.data.api_token, response.data.mcp_url);
      setShowRegenConfirm(false);
    } catch (err: any) {
      setRegenError(err.response?.data?.detail || 'Failed to regenerate token. Please try again.');
    } finally {
      setRegenLoading(false);
    }
  };

  // If user has no bot, show inline setup
  if (!loading && user && !user.bot_id) {
    // Success step — show credentials then continue to dashboard
    if (botSetupStep === 'success') {
      return (
        <div className="min-h-screen bg-void flex items-center justify-center px-6">
          <div className="max-w-md w-full space-y-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-neon/10 rounded-full mb-4">
                <CheckCircle className="w-8 h-8 text-neon" />
              </div>
              <h2 className="text-3xl font-display font-bold text-text-primary mb-2">
                Bot Deployed!
              </h2>
              <p className="text-text-secondary">Your AI agent is ready to play</p>
            </div>

            <ApiCredentials apiToken={newApiToken} mcpUrl={newMcpUrl} />

            <button
              onClick={() => window.location.reload()}
              className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 flex items-center justify-center gap-2"
            >
              Go to Dashboard
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      );
    }

    // Bot setup form
    return (
      <div className="min-h-screen bg-void flex items-center justify-center px-6">
        <div className="max-w-md w-full bg-card border border-white/10 rounded-lg p-8">
          <form onSubmit={handleBotSetup} className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-display font-bold text-text-primary mb-2">
                Setup Your Bot
              </h2>
              <p className="text-text-secondary">Choose a name and avatar for your AI agent</p>
            </div>

            {botSetupError && (
              <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4">
                <p className="text-accent-red text-sm">{botSetupError}</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-mono text-text-secondary mb-2">Bot Name</label>
              <input
                type="text"
                value={botName}
                onChange={(e) => setBotName(e.target.value)}
                className="w-full bg-surface border border-white/10 rounded-lg px-4 py-3 text-text-primary placeholder-text-muted focus:outline-none focus:border-gold/50 transition-colors"
                placeholder="e.g., Lucky Bot"
                required
                disabled={botSetupLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-mono text-text-secondary mb-2">Bot Avatar</label>
              <AvatarPicker selected={avatarSeed} onSelect={setAvatarSeed} />
            </div>

            <button
              type="submit"
              disabled={botSetupLoading}
              className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Sparkles className="w-5 h-5" />
              {botSetupLoading ? 'Deploying...' : 'Deploy Bot'}
            </button>
          </form>
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
                  {balance !== null ? balance.toLocaleString() : '—'}
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
        <div>
          <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
            API Credentials
          </h2>

          {apiToken ? (
            <>
              <ApiCredentials apiToken={apiToken} mcpUrl={mcpUrl || `${config.apiUrl}/mcp`} />
              <p className="text-accent-red text-sm mt-3 font-mono">
                Save this token — it won't be shown again.
              </p>
            </>
          ) : (
            <div className="bg-card border border-white/10 rounded-lg p-6">
              <p className="text-text-secondary text-sm mb-4">
                Your API token is hidden for security. If you've lost it, you can generate a new one below. This will invalidate your current token.
              </p>
            </div>
          )}

          {/* Regenerate Token */}
          <div className="mt-4">
            {regenError && (
              <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4 mb-4">
                <p className="text-accent-red text-sm">{regenError}</p>
              </div>
            )}

            {showRegenConfirm ? (
              <div className="bg-surface border border-gold/20 rounded-lg p-6">
                <div className="flex items-start gap-3 mb-4">
                  <AlertTriangle className="w-5 h-5 text-gold flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-text-primary font-medium">Regenerate API Token?</p>
                    <p className="text-text-secondary text-sm mt-1">
                      This will invalidate your current token immediately. Any bots using the old token will stop working.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleRegenerateToken}
                    disabled={regenLoading}
                    className="bg-accent-red/80 hover:bg-accent-red text-white font-bold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <RefreshCw className={`w-4 h-4 ${regenLoading ? 'animate-spin' : ''}`} />
                    {regenLoading ? 'Regenerating...' : 'Yes, Regenerate'}
                  </button>
                  <button
                    onClick={() => setShowRegenConfirm(false)}
                    disabled={regenLoading}
                    className="bg-surface border border-white/10 hover:border-white/20 text-text-secondary font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowRegenConfirm(true)}
                className="flex items-center gap-2 bg-surface border border-white/10 hover:border-gold/30 text-text-secondary hover:text-text-primary font-medium py-2.5 px-4 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Regenerate Token
              </button>
            )}
          </div>
        </div>

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
