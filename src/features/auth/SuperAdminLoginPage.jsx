import React, { useState } from 'react';
import { Eye, EyeOff, ShieldCheck, ArrowLeft, RefreshCw, AlertCircle, Lock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function SuperAdminLoginPage({ onNavigate }) {
  const { superAdminLogin } = useAuth();
  const [loginInput, setLoginInput] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!loginInput.trim()) {
      setError('Please enter your Super Admin email, mobile, or username.');
      return;
    }
    if (!password) {
      setError('Please enter your administrator password.');
      return;
    }

    setLoading(true);
    try {
      await superAdminLogin({
        login: loginInput.trim(),
        password
      });
      // Redirect to admin hub root
      if (onNavigate) {
        onNavigate('');
      } else {
        window.location.hash = '';
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please verify your administrator credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#fafbfc] text-slate-800 font-sans flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative">
      {/* Top Back Nav */}
      <div className="absolute top-6 left-6">
        <button
          onClick={() => onNavigate ? onNavigate('') : (window.location.hash = '')}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-900 bg-white border border-slate-200/80 px-3.5 py-2 rounded-xl shadow-2xs transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Home</span>
        </button>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Main Admin Card */}
        <div className="bg-white border border-slate-200/90 rounded-3xl p-8 sm:p-10 shadow-lg relative overflow-hidden">
          {/* Top Security Indicator Line */}
          <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-orange-500 via-amber-400 to-orange-600" />

          {/* Admin Header Branding */}
          <div className="text-center space-y-3 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-400 text-white flex items-center justify-center font-black text-2xl shadow-xs mx-auto">
              A
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-orange-50 text-orange-700 border border-orange-200/80 mb-2">
                <ShieldCheck className="w-3.5 h-3.5 text-orange-600" />
                <span>Restricted Gateway</span>
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Super Admin <span className="text-orange-600">Control</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                Authorized platform operators only. Candidates must authenticate via the candidate portal.
              </p>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200/80 flex items-start gap-2.5 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="font-medium leading-relaxed">{error}</div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Admin Username, Email, or Mobile
              </label>
              <input
                type="text"
                autoComplete="username"
                value={loginInput}
                onChange={(e) => setLoginInput(e.target.value)}
                placeholder="admin@politiads.com"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-orange-500 transition shadow-2xs"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Security Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter administrator password"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-4 pr-11 py-3 text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-orange-500 transition shadow-2xs"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3.5 rounded-xl font-bold text-xs bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shadow-xs hover:shadow-md transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Credentials…</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Sign In to Super Admin Hub</span>
                </>
              )}
            </button>
          </form>

          {/* Security Disclaimer (Strictly NO Register Link) */}
          <div className="mt-6 pt-5 border-t border-slate-100 text-center">
            <p className="text-[11px] text-slate-400 leading-normal">
              🔒 <strong>Isolated Session</strong>: All administrative logins are verified and audit-logged against unauthorized intrusion.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
