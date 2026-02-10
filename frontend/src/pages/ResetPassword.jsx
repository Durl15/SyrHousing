import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../lib/api';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [status, setStatus] = useState('form'); // form | success | error
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const token = searchParams.get('token');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    if (!token) {
      setError('No reset token provided');
      return;
    }

    setLoading(true);
    try {
      await api.post(`/auth/reset-password?token=${encodeURIComponent(token)}&new_password=${encodeURIComponent(password)}`);
      setStatus('success');
    } catch (err) {
      setError(err.response?.data?.detail || 'Reset failed. The link may be expired.');
      setStatus('error');
    }
    setLoading(false);
  };

  if (status === 'success') {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-md p-8 text-center">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-emerald-600 text-3xl">&#10003;</span>
          </div>
          <h2 className="text-lg font-semibold text-[#1e3a5f] mb-2">Password Reset!</h2>
          <p className="text-gray-500 mb-6">Your password has been updated. You can now sign in.</p>
          <Link
            to="/login"
            className="inline-block px-6 py-2 bg-[#1e3a5f] text-white font-medium rounded-lg hover:bg-[#2d6a9f] transition-colors no-underline"
          >
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-md p-8">
        <h2 className="text-xl font-bold text-[#1e3a5f] mb-6 text-center">Reset Password</h2>

        {!token && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm mb-4">
            No reset token found. Please use the link from your email.
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm mb-4">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !token}
            className="w-full py-2.5 bg-[#1e3a5f] text-white font-semibold rounded-lg hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
