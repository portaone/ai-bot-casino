import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { Shield, ArrowRight } from 'lucide-react';

export function VerifyPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const { setAuth, setApiToken } = useAuthStore();

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(300); // 5 minutes
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Get otp_id from URL params or location state
  const otpId =
    searchParams.get('otp_id') || (location.state as any)?.otp_id || '';
  const email = (location.state as any)?.email || '';

  // Check for magic token on mount
  useEffect(() => {
    const magicToken = searchParams.get('magic_token');
    if (magicToken && otpId) {
      handleMagicLinkVerify(magicToken);
    }
  }, [searchParams, otpId]);

  // Timer countdown
  useEffect(() => {
    if (timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  const handleMagicLinkVerify = async (magicToken: string) => {
    setLoading(true);
    setError('');

    try {
      const response = await authApi.verifyMagicLink({
        otp_id: otpId,
        magic_token: magicToken,
      });

      // Store auth token
      setAuth(response.data.access_token, { id: '', first_name: '', email: '' });

      if (response.data.api_token) {
        setApiToken(response.data.api_token);
      }

      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid magic link. Please try again.');
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

  const handleSubmit = async (e: React.FormEvent) => {
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

      if (!otpId) {
        setError('Invalid verification session. Please try again.');
        setLoading(false);
        return;
      }

      const response = await authApi.verifyOtp({
        otp_id: otpId,
        otp: otpCode,
      });

      // Store auth token
      setAuth(response.data.access_token, { id: '', first_name: '', email: '' });

      if (response.data.api_token) {
        setApiToken(response.data.api_token);
      }

      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!otpId) {
    return (
      <div className="w-full max-w-md">
        <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-6 text-center">
          <p className="text-accent-red">Invalid verification session. Please try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-neon/10 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-neon" />
            </div>
          </div>
          <h2 className="text-3xl font-display font-bold text-text-primary mb-2 text-center">
            Verify Your Email
          </h2>
          <p className="text-text-secondary text-center">
            {email ? `Enter the 6-digit code sent to ${email}` : 'Enter the 6-digit code'}
          </p>
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

        <div className="text-center">
          <p className="text-text-muted text-sm">
            Code expires in{' '}
            <span
              className={
                timeRemaining < 60 ? 'text-accent-red font-mono' : 'text-gold font-mono'
              }
            >
              {formatTime(timeRemaining)}
            </span>
          </p>
        </div>

        <button
          type="submit"
          disabled={loading || timeRemaining === 0}
          className="w-full bg-gradient-to-r from-gold to-gold-dim text-void font-bold py-3 rounded-lg hover:shadow-lg hover:shadow-gold/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? 'Verifying...' : 'Verify Code'}
          <ArrowRight className="w-5 h-5" />
        </button>

        <div className="text-center">
          <button
            type="button"
            className="text-text-secondary hover:text-gold text-sm underline transition-colors"
            disabled={loading}
          >
            Resend code
          </button>
        </div>
      </form>
    </div>
  );
}
