import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { LogIn, ArrowRight } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.login({
        email: email.trim(),
      });

      // Navigate to verification page with otp_id
      navigate(`/auth/verify?otp_id=${response.data.otp_id}`, {
        state: { email, otp_id: response.data.otp_id },
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-gold/10 rounded-lg flex items-center justify-center">
              <LogIn className="w-6 h-6 text-gold" />
            </div>
          </div>
          <h2 className="text-3xl font-display font-bold text-text-primary mb-2 text-center">
            Welcome Back
          </h2>
          <p className="text-text-secondary text-center">
            Enter your email to receive a login code
          </p>
        </div>

        {error && (
          <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4">
            <p className="text-accent-red text-sm">{error}</p>
          </div>
        )}

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
          {loading ? 'Sending Code...' : 'Send Login Code'}
          <ArrowRight className="w-5 h-5" />
        </button>

        <p className="text-center text-text-muted text-sm">
          Don't have an account?{' '}
          <Link to="/auth/register" className="text-gold hover:text-gold-dim underline">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}
