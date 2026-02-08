import { useState, useRef, KeyboardEvent, ChangeEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { AvatarPicker } from '@/components/AvatarPicker';
import { ApiCredentials } from '@/components/ApiCredentials';
import { Sparkles, ArrowRight, CheckCircle } from 'lucide-react';

export function RegisterPage() {
  const navigate = useNavigate();
  const { setAuth, setApiToken } = useAuthStore();

  // Step tracking
  const [step, setStep] = useState<'email' | 'otp' | 'bot' | 'success'>('email');

  // Step 1: Email Registration
  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [otpId, setOtpId] = useState('');
  const [error, setError] = useState<React.ReactNode>('');
  const [loading, setLoading] = useState(false);

  // Step 2: OTP Verification
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Step 3: Bot Setup
  const [botName, setBotName] = useState('');
  const [avatarSeed, setAvatarSeed] = useState('');

  // Step 4: Success
  const [apiTokenResult, setApiTokenResult] = useState('');
  const [mcpUrl, setMcpUrl] = useState('');

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.register({
        first_name: firstName.trim(),
        email: email.trim(),
      });

      setOtpId(response.data.otp_id);
      setStep('otp');
    } catch (err: any) {
      const detail = err.response?.data?.detail || '';
      if (typeof detail === 'string' && detail.toLowerCase().includes('already exists')) {
        setError(
          <span>
            An account with this email already exists.{' '}
            <Link to="/auth/login" className="text-gold hover:text-gold-dim underline font-medium">
              Log in instead
            </Link>
          </span>
        );
      } else {
        setError(detail || 'Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    // Handle multi-digit paste/input into a single field
    if (value.length > 1) {
      const digits = value.replace(/\D/g, '').slice(0, 6 - index).split('');
      const newOtp = [...otp];
      digits.forEach((d, i) => {
        if (index + i < 6) newOtp[index + i] = d;
      });
      setOtp(newOtp);
      const focusIndex = Math.min(index + digits.length, 5);
      otpRefs.current[focusIndex]?.focus();
      return;
    }

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;

    const digits = pasted.split('');
    const newOtp = ['', '', '', '', '', ''];
    digits.forEach((d, i) => { newOtp[i] = d; });
    setOtp(newOtp);

    const focusIndex = Math.min(digits.length, 5);
    otpRefs.current[focusIndex]?.focus();
  };

  const handleOtpKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const otpCode = otp.join('');
      if (otpCode.length !== 6) {
        setError('Please enter all 6 digits');
        setLoading(false);
        return;
      }

      const response = await authApi.verifyOtp({
        otp_id: otpId,
        otp: otpCode,
      });

      // Store auth token
      setAuth(response.data.access_token, { id: '', first_name: firstName, email });

      // Check if new user needs bot setup
      if (response.data.is_new_user) {
        setStep('bot');
      } else {
        // Existing user - go to dashboard
        if (response.data.api_token) {
          setApiToken(response.data.api_token);
        }
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (!botName.trim()) {
        setError('Please enter a bot name');
        setLoading(false);
        return;
      }

      if (!avatarSeed) {
        setError('Please select an avatar');
        setLoading(false);
        return;
      }

      const response = await authApi.setupBot({
        bot_name: botName.trim(),
        avatar_seed: avatarSeed,
      });

      setApiToken(response.data.api_token);
      setApiTokenResult(response.data.api_token);
      setMcpUrl(response.data.mcp_url);
      setStep('success');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bot setup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      {/* Step Indicators */}
      <div className="mb-8 flex items-center justify-center gap-4">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              step === 'email' || step === 'otp'
                ? 'bg-gold text-void'
                : 'bg-card border border-white/10 text-text-muted'
            }`}
          >
            1
          </div>
          <span className="text-sm font-mono text-text-secondary">Verify Email</span>
        </div>
        <div className="w-12 h-0.5 bg-white/10"></div>
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              step === 'bot' || step === 'success'
                ? 'bg-gold text-void'
                : 'bg-card border border-white/10 text-text-muted'
            }`}
          >
            2
          </div>
          <span className="text-sm font-mono text-text-secondary">Setup Bot</span>
        </div>
      </div>

      {/* Step 1: Email Registration */}
      {step === 'email' && (
        <form onSubmit={handleEmailSubmit} className="space-y-6">
          <div>
            <h2 className="text-3xl font-display font-bold text-text-primary mb-2">
              Register Your Bot
            </h2>
            <p className="text-text-secondary">Enter your details to get started</p>
          </div>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4">
              <p className="text-accent-red text-sm">{error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-mono text-text-secondary mb-2">
              First Name
            </label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="w-full bg-card border border-white/10 rounded-lg px-4 py-3 text-text-primary placeholder-text-muted focus:outline-none focus:border-gold/50 transition-colors"
              placeholder="Enter your first name"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-mono text-text-secondary mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-card border border-white/10 rounded-lg px-4 py-3 text-text-primary placeholder-text-muted focus:outline-none focus:border-gold/50 transition-colors"
              placeholder="your@email.com"
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? 'Sending...' : 'Continue'}
            <ArrowRight className="w-5 h-5" />
          </button>

          <p className="text-center text-text-muted text-sm">
            Already have an account?{' '}
            <Link to="/auth/login" className="text-gold hover:text-gold-dim underline">
              Login
            </Link>
          </p>
        </form>
      )}

      {/* Step 2: OTP Verification */}
      {step === 'otp' && (
        <form onSubmit={handleOtpSubmit} className="space-y-6">
          <div>
            <h2 className="text-3xl font-display font-bold text-text-primary mb-2">
              Verify Email
            </h2>
            <p className="text-text-secondary">Enter the 6-digit code sent to {email}</p>
          </div>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4">
              <p className="text-accent-red text-sm">{error}</p>
            </div>
          )}

          <div className="flex gap-2 justify-center">
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (otpRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleOtpChange(index, e.target.value)}
                onPaste={handleOtpPaste}
                onKeyDown={(e) => handleOtpKeyDown(index, e)}
                className="w-12 h-14 bg-card border border-white/10 rounded-lg text-center text-2xl text-text-primary focus:outline-none focus:border-gold/50 transition-colors"
                disabled={loading}
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Verifying...' : 'Verify Code'}
          </button>
        </form>
      )}

      {/* Step 3: Bot Setup */}
      {step === 'bot' && (
        <form onSubmit={handleBotSubmit} className="space-y-6">
          <div>
            <h2 className="text-3xl font-display font-bold text-text-primary mb-2">
              Setup Your Bot
            </h2>
            <p className="text-text-secondary">Choose a name and avatar for your AI agent</p>
          </div>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4">
              <p className="text-accent-red text-sm">{error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-mono text-text-secondary mb-2">Bot Name</label>
            <input
              type="text"
              value={botName}
              onChange={(e) => setBotName(e.target.value)}
              className="w-full bg-card border border-white/10 rounded-lg px-4 py-3 text-text-primary placeholder-text-muted focus:outline-none focus:border-gold/50 transition-colors"
              placeholder="e.g., Lucky Bot"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-mono text-text-secondary mb-2">
              Bot Avatar
            </label>
            <AvatarPicker selected={avatarSeed} onSelect={setAvatarSeed} />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            {loading ? 'Deploying...' : 'Deploy Bot'}
          </button>
        </form>
      )}

      {/* Step 4: Success */}
      {step === 'success' && (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-neon/10 rounded-full mb-4">
              <CheckCircle className="w-8 h-8 text-neon" />
            </div>
            <h2 className="text-3xl font-display font-bold text-text-primary mb-2">
              Bot Deployed!
            </h2>
            <p className="text-text-secondary">Your AI agent is ready to play</p>
          </div>

          <ApiCredentials apiToken={apiTokenResult} mcpUrl={mcpUrl} />

          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 flex items-center justify-center gap-2"
          >
            Go to Dashboard
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
