import React from 'react';
import MetaConnectModal from './MetaConnectModal';
import { useAuth } from '../../context/AuthContext';
const errors = {
  invalid_state: 'This authorization link expired or belongs to a different browser. Start again.',
  access_denied: 'Facebook authorization was cancelled. Your accounts were not connected.',
  permissions_required: 'Required permissions were not granted. Authorize again and select the intended Page.',
  account_exists: 'An account with this email already exists. Log in with your password and connect Facebook from the dashboard.',
  identity_conflict: 'This Facebook identity is already linked to another app account.',
  wrong_facebook_account: 'Use the Facebook account that manages your selected Page.',
  inactive_account: 'This app account is not active.',
  provider_unavailable: 'Facebook verification failed. Check Meta app configuration and try again.'
};
export default function MetaOAuthReturn({ onBack }) {
  const { user, isCheckingSession } = useAuth();
  const query = new URLSearchParams(window.location.hash.split('?')[1] || '');
  const purpose = query.get('purpose') || 'facebook';
  if (isCheckingSession) return <p className="p-8" role="status">Checking app session…</p>;
  if (query.get('result') === 'error') return <div className="p-8 max-w-xl mx-auto space-y-4"><h1 className="font-bold text-xl">Facebook authorization was not completed</h1><p role="alert">{errors[query.get('error')] || 'Authorization failed. Check the app configuration and start again.'}</p><button onClick={onBack} className="underline">Return to app</button></div>;
  if (purpose === 'login') return <div className="p-8 space-y-4"><p>{user ? `Signed in as ${user.full_name}.` : 'Facebook login did not create a valid app session. Try again.'}</p><button onClick={onBack} className="underline">Continue to app</button></div>;
  if (!user) return <div className="p-8">Log in to the app before selecting a Facebook or Instagram account.<button onClick={onBack} className="underline ml-2">Return</button></div>;
  return <MetaConnectModal isOpen target={purpose === 'instagram' ? 'instagram' : 'facebook'} onClose={onBack} onConnected={onBack} />;
}
