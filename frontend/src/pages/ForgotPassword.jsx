import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post(`/auth/forgot-password?email=${encodeURIComponent(email)}`);
    } catch { /* always show success to prevent email enumeration */ }
    setSent(true);
    setLoading(false);
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-md p-8">
        <h2 className="text-xl font-bold text-[#1e3a5f] mb-2 text-center">Forgot Password</h2>

        {sent ? (
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 mt-4">
              <span className="text-blue-600 text-2xl">&#9993;</span>
            </div>
            <p className="text-gray-600 mb-6">
              If an account exists with that email, we've sent a password reset link.
              Check your inbox.
            </p>
            <Link to="/login" className="text-[#2d6a9f] hover:underline text-sm">
              Back to Sign In
            </Link>
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-500 mb-6 text-center">
              Enter your email and we'll send you a reset link.
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
                  placeholder="you@example.com"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-[#1e3a5f] text-white font-semibold rounded-lg hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
            <div className="text-center mt-4">
              <Link to="/login" className="text-sm text-[#2d6a9f] hover:underline">
                Back to Sign In
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
