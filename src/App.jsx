import CampaignDetails from './features/campaigns/CampaignDetails';
import MetaOAuthReturn from './components/meta/MetaOAuthReturn';
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from './context/AuthContext';
import LandingPage from './features/landing/LandingPage';
import OnboardingWizard from './features/onboarding/OnboardingWizard';
import CandidateDashboard from './features/dashboard/CandidateDashboard';
import AdminHub from './features/admin/AdminHub';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import SuperAdminLoginPage from './features/auth/SuperAdminLoginPage';

import CreateAdModal from './features/campaigns/CreateAdModal';
import Toast from './components/ui/Toast';
import SmoothScroll from './components/ui/SmoothScroll';
import PrivacyPolicy from './features/legal/PrivacyPolicy';
import DataDeletion from './features/legal/DataDeletion';
import TermsOfService from './features/legal/TermsOfService';
import RefundPolicy from './features/legal/RefundPolicy';
import ContactUs from './features/legal/ContactUs';
import { profileApi } from './api/profile';
import { campaignsApi } from './api/campaigns';

function CandidateWorkspace({ user, onLogout, onSwitchToAdmin, showToast, onProfileComplete }) {
  const [profile, setProfile] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [creating, setCreating] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([profileApi.getProfile(), campaignsApi.getCampaigns()]);
      setProfile(p);
      setCampaigns(c.map(item => ({ ...item, budget: item.budget_daily, radius: item.radius_km })));
      setError('');
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    void Promise.resolve().then(refresh);
    const onFocus = () => { void refresh(); };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [refresh]);
  const save = async (data) => {
    setSaving(true);
    try {
      const saved = await profileApi.updateProfile(data);
      setProfile(saved);
      if (saved.onboarding_completed) onProfileComplete();
      showToast('Profile saved.');
      return saved;
    } finally { setSaving(false); }
  };
  const submit = async (data) => {
    setCreating(true);
    try { await campaignsApi.createCampaign(data); setModalOpen(false); await refresh(); showToast(data.save_as_draft ? 'Draft saved.' : 'Ad submitted for company review.'); }
    finally { setCreating(false); }
  };
  if (!profile) return <div className="p-8" role="status">{error || 'Loading profile…'}{error && <button onClick={refresh} className="ml-4 underline">Retry</button>}</div>;
  return <>
    {!profile.onboarding_completed ? <OnboardingWizard initialProfile={profile} onSaveProfile={save} isSaving={saving} onComplete={refresh} /> :
      <CandidateDashboard user={user} profile={profile} campaigns={campaigns} campaignsLoading={loading} campaignsError={error} onRefreshCampaigns={refresh}
        onViewCampaign={setSelectedCampaign} onOpenCreateAdModal={() => setModalOpen(true)} onToggleCampaignStatus={async id => { try { await campaignsApi.toggleCampaignStatus(id); await refresh(); } catch (e) { showToast(e.message); } }}
        onSaveProfile={save} isSavingProfile={saving} onSwitchToAdmin={onSwitchToAdmin} onLogout={onLogout} />}
    {selectedCampaign && <CampaignDetails campaignId={selectedCampaign} onClose={() => setSelectedCampaign(null)} onUpdated={refresh} />}
    {modalOpen && <CreateAdModal isOpen onClose={() => setModalOpen(false)} onSubmit={submit} candidateProfile={{ ...profile, mobile: user.mobile }} isSubmitting={creating} />}
  </>;
}

const KNOWN_ROUTES = ['meta-connect', 'privacy', 'terms', 'refunds', 'data-deletion', 'contact', 'login', 'signup', 'register', 'super-admin-login'];

export default function App() {
  const { user, isCheckingSession, authError, checkSession, logout, setUser } = useAuth();
  const [candidatePreview, setCandidatePreview] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '' });
  


  const [currentRoute, setCurrentRoute] = useState(() => {
    const hash = window.location.hash.replace(/^#\/?/, '').split('?')[0].toLowerCase();
    return KNOWN_ROUTES.includes(hash) ? hash : null;
  });

  const showToast = (message, type = 'info') => setToast({ show: true, message, type });
  const handleLogout = async () => {
    try {
      await logout();
      setCandidatePreview(false);
      showToast('Logged out successfully.');
      window.location.hash = '';
    } catch (e) {
      showToast('Logout was not confirmed: ' + e.message, 'error');
    }
  };

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.replace(/^#\/?/, '').split('?')[0].toLowerCase();
      if (KNOWN_ROUTES.includes(hash)) {
        setCurrentRoute(hash);
      } else if (!hash) {
        setCurrentRoute(null);
      }
    };
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  const navigateTo = (route) => {
    const cleanRoute = (route || '').replace(/^#\/?/, '').toLowerCase();
    if (cleanRoute && KNOWN_ROUTES.includes(cleanRoute)) {
      setCurrentRoute(cleanRoute);
      window.location.hash = `#/${cleanRoute}`;
    } else {
      setCurrentRoute(null);
      window.location.hash = '';
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // If user is already logged in, redirect away from login/signup
  useEffect(() => {
    if (user && (currentRoute === 'login' || currentRoute === 'signup' || currentRoute === 'register' || currentRoute === 'super-admin-login')) {
      void Promise.resolve().then(() => { setCurrentRoute(null); window.location.hash = ''; });
    }
  }, [user, currentRoute]);

  if (currentRoute === 'meta-connect') return <MetaOAuthReturn onBack={() => navigateTo('')} />;

  // Handle dedicated Legal & Auth Pages
  if (currentRoute === 'privacy') return <PrivacyPolicy onBack={() => navigateTo('')} />;
  if (currentRoute === 'data-deletion') return <DataDeletion onBack={() => navigateTo('')} />;
  if (currentRoute === 'terms') return <TermsOfService onBack={() => navigateTo('')} />;
  if (currentRoute === 'refunds') return <RefundPolicy onBack={() => navigateTo('')} />;
  if (currentRoute === 'contact') return <ContactUs onBack={() => navigateTo('')} />;
  
  if (!user && currentRoute === 'login') return <LoginPage onNavigate={navigateTo} />;
  if (!user && (currentRoute === 'signup' || currentRoute === 'register')) return <RegisterPage onNavigate={navigateTo} />;
  if (!user && currentRoute === 'super-admin-login') return <SuperAdminLoginPage onNavigate={navigateTo} />;

  if (isCheckingSession) return <div className="p-10" role="status">Checking server session…</div>;
  if (authError && !user) return <div className="p-10" role="alert"><p>{authError}</p><button onClick={checkSession} className="underline">Retry session check</button></div>;

  return (
    <SmoothScroll>
      <Toast type={toast.type} show={toast.show} message={toast.message} onClose={() => setToast({ show: false, message: '' })} />
      {!user ? (
        <LandingPage
          onOpenAuth={mode => navigateTo(mode || 'login')}
          onNavigate={navigateTo}
          onLogout={handleLogout}
        />
      ) : (
        user.role === 'admin' && !candidatePreview ? (
          <AdminHub
            key={user.id}
            onSwitchToCandidateView={() => setCandidatePreview(true)}
            onLogout={handleLogout}
            showToast={showToast}
          />
        ) : (
          <CandidateWorkspace
            key={user.id}
            user={user}
            onLogout={handleLogout}
            showToast={showToast}
            onSwitchToAdmin={() => setCandidatePreview(false)}
            onProfileComplete={() => setUser(previous => ({ ...previous, onboarding_completed: true }))}
          />
        )
      )}
    </SmoothScroll>
  );
}
