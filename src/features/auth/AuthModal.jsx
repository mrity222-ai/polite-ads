import React, { useState } from 'react';
import { Megaphone, X, AlertCircle, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AuthModal({
  isOpen,
  onClose,
  initialMode = 'signup',
  onSuccess
}) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState(initialMode); // 'signup' | 'login'

  // Signup fields
  const [regFullName, setRegFullName] = useState('');
  const [regMobile, setRegMobile] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [regError, setRegError] = useState('');
  const [regLoading, setRegLoading] = useState(false);

  // Login fields
  const [loginInput, setLoginInput] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  if (!isOpen) return null;

  const handleSignUpSubmit = async (e) => {
    e.preventDefault();
    setRegError('');

    if (!regFullName.trim()) {
      setRegError('Please enter your full legal name.');
      return;
    }
    const cleanMobile = regMobile.replace(/\D/g, '');
    if (cleanMobile.length !== 10) {
      setRegError('Please enter a valid 10-digit Indian WhatsApp mobile number.');
      return;
    }
    if (!regEmail.trim() || !regEmail.includes('@')) {
      setRegError('Please enter a valid email address.');
      return;
    }
    if (!regPassword || regPassword.length < 8) {
      setRegError('Password must be at least 8 characters.');
      return;
    }
    if (regPassword !== regConfirmPassword) {
      setRegError('Passwords do not match.');
      return;
    }

    setRegLoading(true);
    try {
      const newUser = await register({
        full_name: regFullName.trim(),
        mobile: cleanMobile,
        email: regEmail.trim(),
        password: regPassword,
        confirm_password: regConfirmPassword
      });
      onSuccess?.(newUser, 'signup');
      onClose();
    } catch (err) {
      setRegError(err.message || 'Registration failed. Please try again.');
    } finally {
      setRegLoading(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    if (!loginInput.trim() || !loginPassword) {
      setLoginError('Please enter both mobile/email and password.');
      return;
    }

    setLoginLoading(true);
    try {
      const loggedUser = await login({ login: loginInput.trim(), password: loginPassword });
      onSuccess?.(loggedUser, 'login');
      onClose();
    } catch (err) {
      setLoginError(err.message || 'Invalid credentials.');
    } finally {
      setLoginLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-gray-950/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white w-full max-w-md rounded-3xl p-7 sm:p-9 border border-gray-200 shadow-2xl relative my-8 animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gray-950 flex items-center justify-center shadow-sm">
            <Megaphone className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-black text-gray-950">
            Politi<span className="text-emerald-600">Ads</span>
          </span>
        </div>

        <h2 className="text-2xl font-bold text-gray-950 tracking-tight">
          {mode === 'signup' ? 'Create Candidate Account' : 'Log In to War-Room'}
        </h2>
        <p className="text-xs text-gray-500 mt-1 mb-6">
          {mode === 'signup'
            ? 'Create your profile and submit drafts for company review.'
            : 'Access your voter analytics, opponent spy, and ad manager.'}
        </p>

        {mode === 'signup' ? (
          <form onSubmit={handleSignUpSubmit} className="space-y-3.5">
            {regError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{regError}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Full Legal Name*</label>
              <input
                type="text"
                value={regFullName}
                onChange={(e) => setRegFullName(e.target.value)}
                placeholder="e.g. Rajesh Kumar Sharma"
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">WhatsApp Mobile Number*</label>
              <div className="relative flex">
                <span className="inline-flex items-center px-3 rounded-l-xl border border-r-0 border-gray-300 bg-gray-100 text-gray-600 text-xs font-semibold">🇮🇳 +91</span>
                <input
                  type="tel"
                  maxLength={10}
                  value={regMobile}
                  onChange={(e) => setRegMobile(e.target.value.replace(/\D/g, ''))}
                  placeholder="9876543210"
                  className="w-full bg-[#fafafa] border border-gray-300 rounded-r-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address*</label>
              <input
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                placeholder="rajesh@campaign.in"
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Password (min 8 characters)*</label>
              <input
                type="password"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Confirm Password*</label>
              <input
                type="password"
                value={regConfirmPassword}
                onChange={(e) => setRegConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={regLoading}
              className="w-full mt-2 py-3.5 rounded-full font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] disabled:opacity-50 transition shadow-md text-sm flex items-center justify-center gap-2"
            >
              {regLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
              {regLoading ? 'Creating Account...' : 'Create Account & Continue →'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            {loginError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{loginError}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Email or Mobile Number</label>
              <input
                type="text"
                value={loginInput}
                onChange={(e) => setLoginInput(e.target.value)}
                placeholder="e.g. rajesh@campaign.in or 9876543210"
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-3.5 rounded-full font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] disabled:opacity-50 transition text-sm shadow-md flex items-center justify-center gap-2"
            >
              {loginLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
              {loginLoading ? 'Authenticating...' : 'Log In to Dashboard'}
            </button>

          </form>
        )}

        <div className="mt-6 pt-4 border-t border-gray-100 text-center text-xs text-gray-500">
          {mode === 'signup' ? (
            <span>
              Already have an account?{' '}
              <button
                onClick={() => { setMode('login'); setRegError(''); }}
                className="font-bold text-emerald-700 hover:underline"
              >
                Log in here
              </button>
            </span>
          ) : (
            <span>
              Don't have an account yet?{' '}
              <button
                onClick={() => { setMode('signup'); setLoginError(''); }}
                className="font-bold text-emerald-700 hover:underline"
              >
                Create free account
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
