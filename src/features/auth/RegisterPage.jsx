import React, { useState } from 'react';
import { Eye, EyeOff, ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AuthIllustration from './AuthIllustration';
import { integrationsApi } from '../../api/integrations';
import SocialAuthButtons from './SocialAuthButtons';

export default function RegisterPage({ onNavigate }) {
  const { register } = useAuth();

  // Form Fields
  const [fullName, setFullName] = useState('');
  const [mobile, setMobile] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [socialNotice, setSocialNotice] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSocialNotice('');

    if (!fullName.trim()) {
      setError('Please enter your full legal candidate name.');
      return;
    }
    const cleanMobile = mobile.replace(/\D/g, '');
    if (cleanMobile.length !== 10) {
      setError('Please enter a valid 10-digit Indian WhatsApp mobile number.');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        mobile: cleanMobile,
        email: email.trim().toLowerCase(),
        password,
        confirm_password: confirmPassword
      });
      // Successful registration transitions to onboarding
      if (onNavigate) {
        onNavigate('');
      } else {
        window.location.hash = '';
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSocialClick = async (provider) => {
    setError('');
    if (provider !== 'Facebook') { setSocialNotice(`${provider} sign-in is not configured. Use email or Facebook.`); return; }
    setLoading(true); setSocialNotice('Opening Facebook authorization…');
    try { const response = await integrationsApi.startFacebookLogin(); window.location.assign(response.authorization_url); }
    catch (e) { setError(e.message); setSocialNotice(''); setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans flex flex-col justify-center py-6 px-4 sm:px-6 lg:px-8">
      {/* Top Back Nav */}
      <div className="max-w-7xl mx-auto w-full mb-4 px-2">
        <button
          type="button"
          onClick={() => {
            if (onNavigate) onNavigate('');
            else window.location.hash = '';
          }}
          className="inline-flex items-center gap-2 text-xs font-semibold text-gray-600 hover:text-black py-2 px-3 rounded-full hover:bg-gray-100 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </button>
      </div>

      {/* Main 2-Column Grid */}
      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-14 items-center">
        
        {/* Left Column: Form Card */}
        <div className="w-full max-w-md mx-auto px-4 sm:px-6 py-4 flex flex-col justify-center">
          
          <div className="mb-6 text-left">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-950 tracking-tight mb-2.5">
              Create an account
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 leading-relaxed font-normal">
              Simplify your workflow and boost your productivity with PolitiAds. Get started for free.
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2.5" role="alert">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          {socialNotice && (
            <div className="mb-4 p-3 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>{socialNotice}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3.5">
            {/* Full Name */}
            <div>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Full Name"
                autoComplete="name"
                className="w-full rounded-full border border-gray-300 px-6 py-3.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition bg-white"
              />
            </div>

            {/* Mobile Number */}
            <div>
              <input
                type="tel"
                maxLength={10}
                value={mobile}
                onChange={(e) => setMobile(e.target.value.replace(/\D/g, ''))}
                placeholder="10-Digit Mobile / WhatsApp Number"
                autoComplete="tel"
                className="w-full rounded-full border border-gray-300 px-6 py-3.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition bg-white"
              />
            </div>

            {/* Email Address */}
            <div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email Address"
                autoComplete="email"
                className="w-full rounded-full border border-gray-300 px-6 py-3.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition bg-white"
              />
            </div>

            {/* Password with Eye Icon */}
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password (min 8 characters)"
                autoComplete="new-password"
                className="w-full rounded-full border border-gray-300 px-6 py-3.5 pr-12 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition bg-white"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Confirm Password with Eye Icon */}
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm Password"
                autoComplete="new-password"
                className="w-full rounded-full border border-gray-300 px-6 py-3.5 pr-12 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition bg-white"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition"
                title={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-full bg-black hover:bg-neutral-800 disabled:opacity-60 text-white font-bold py-4 text-sm transition shadow-sm active:scale-[0.99] flex items-center justify-center gap-2"
              >
                {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
                <span>{loading ? 'Creating Account...' : 'Create Account'}</span>
              </button>
            </div>
          </form>

          {/* Social Auth Buttons (Google, Apple, Facebook) */}
          <div className="mt-6">
            <SocialAuthButtons onSocialClick={handleSocialClick} />
          </div>

          {/* Footer Toggle Link */}
          <div className="mt-6 text-center text-xs text-gray-500">
            <span>Already have an account? </span>
            <button
              type="button"
              onClick={() => {
                if (onNavigate) onNavigate('login');
                else window.location.hash = '#/login';
              }}
              className="font-bold text-[#22c55e] hover:underline cursor-pointer"
            >
              Log in
            </button>
          </div>

        </div>

        {/* Right Column: Mint Pastel Illustration Card */}
        <div className="w-full h-full">
          <AuthIllustration headline="Make your election campaign easier and organized with PolitiAds" />
        </div>

      </div>
    </div>
  );
}
