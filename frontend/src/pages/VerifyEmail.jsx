import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../lib/api';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided.');
      return;
    }

    api.post(`/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(() => {
        setStatus('success');
        setMessage('Your email has been verified successfully!');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Verification failed. The link may be expired.');
      });
  }, [searchParams]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-md p-8 text-center">
        {status === 'verifying' && (
          <>
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#1e3a5f] mx-auto mb-4"></div>
            <h2 className="text-lg font-semibold text-[#1e3a5f]">Verifying your email...</h2>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-emerald-600 text-3xl">&#10003;</span>
            </div>
            <h2 className="text-lg font-semibold text-[#1e3a5f] mb-2">Email Verified!</h2>
            <p className="text-gray-500 mb-6">{message}</p>
            <Link
              to="/dashboard"
              className="inline-block px-6 py-2 bg-[#1e3a5f] text-white font-medium rounded-lg hover:bg-[#2d6a9f] transition-colors no-underline"
            >
              Go to Dashboard
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-red-600 text-3xl">&#10007;</span>
            </div>
            <h2 className="text-lg font-semibold text-[#1e3a5f] mb-2">Verification Failed</h2>
            <p className="text-gray-500 mb-6">{message}</p>
            <Link
              to="/dashboard"
              className="inline-block px-6 py-2 bg-[#1e3a5f] text-white font-medium rounded-lg hover:bg-[#2d6a9f] transition-colors no-underline"
            >
              Go to Dashboard
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
