import React, { useState, useEffect, useCallback } from 'react';
import { 
  BarChart3, Megaphone, Vote, Target, CreditCard, Settings, 
  User, ShieldCheck, LogOut, PhoneCall, PlusCircle, PauseCircle, 
  PlayCircle, RefreshCw, ChevronDown, Share2 
} from 'lucide-react';
import LocationPicker from '../../components/location/LocationPicker';
import ImageUploader from '../../components/uploads/ImageUploader';
import PaymentHistory from '../billing/PaymentHistory';
import NotificationCenter from '../../components/notifications/NotificationCenter';
import MetaConnectModal from '../../components/meta/MetaConnectModal';
import { integrationsApi } from '../../api/integrations';

const CONTESTING_POSTS = [
  'Ward Councillor / Corporator',
  'Village Head (Gram Pradhan)',
  'Block Development Council (BDC)',
  'Block President (Pramukh)',
  'District Board Member (Zila Panchayat)',
  'Member of Legislative Assembly (MLA)'
];

const DEFAULT_SYMBOLS = [
  { name: 'Car', icon: '🚗' },
  { name: 'Tractor', icon: '🚜' },
  { name: 'Cricket Bat', icon: '🏏' },
  { name: 'Computer', icon: '💻' },
  { name: 'Ceiling Fan', icon: '🪭' },
  { name: 'Fountain Pen', icon: '✒️' }
];

export default function CandidateDashboard({
  user,
  profile,
  campaigns = [],
  campaignsLoading,
  campaignsError,
  onRefreshCampaigns,
  onOpenCreateAdModal,
  onViewCampaign,
  onToggleCampaignStatus,
  onSaveProfile,
  isSavingProfile = false,
  onSwitchToAdmin,
  onLogout
}) {
  const [saveError, setSaveError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [metaTarget, setMetaTarget] = useState('facebook');
  const [metaModalOpen, setMetaModalOpen] = useState(false);
  const [metaStatus, setMetaStatus] = useState(null);

  const fetchMetaStatus = useCallback(async () => {
    try {
      const res = await integrationsApi.getMetaStatus();
      setMetaStatus(res);
    } catch {
      setMetaStatus({ is_connected: false, connection_status: 'Verification unavailable', message: 'Could not verify provider connection. Refresh or reconnect.' });
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(fetchMetaStatus);
  }, [fetchMetaStatus]);

  const handleDisconnectMeta = async (target = 'all') => {
    if (window.confirm('Are you sure you want to disconnect your Meta account?')) {
      try {
        await integrationsApi.disconnectMeta(target);
        await fetchMetaStatus();
      } catch (err) {
        alert(err.message || 'Failed to disconnect Meta.');
      }
    }
  };

  // Settings form local state initialized from profile
  const [candidateName, setCandidateName] = useState(profile?.candidate_name || user?.full_name || '');
  const [contestingPost, setContestingPost] = useState(profile?.contesting_post || 'Ward Councillor / Corporator');
  const [ward, setWard] = useState(profile?.gaon_ward || 'Rampur, Ward No. 12');
  const [area, setArea] = useState(profile?.area_block || 'Sadabad Block, Hathras');
  const [pincode, setPincode] = useState(profile?.pincode || '281306');
  const [gpsLocation, setGpsLocation] = useState({
    lat: profile?.lat || '27.4482',
    lng: profile?.lng || '78.0416',
    accuracy: profile?.accuracy_m || 25
  });
  const [symbol, setSymbol] = useState(profile?.symbol_name || 'Car');
  const [photo, setPhoto] = useState(profile?.photo_url || null);
  const [defaultSlogan, setDefaultSlogan] = useState(profile?.default_slogan || 'काम किया है, काम करेंगे!');
  const [disclaimer, setDisclaimer] = useState(profile?.disclaimer_text || `Paid for by: ${candidateName} Campaign`);

  const hasLiveMetrics = campaigns.some(c => !c.is_mock && c.provider_review_status === 'Approved');
  // Provider metrics are unavailable in simulation.
  const totalReach = campaigns.reduce((acc, c) => acc + (c.reach || 0), 0);
  const activeCount = campaigns.filter(c => !c.is_mock && c.delivery_status === 'Delivering').length;
  const pendingCount = campaigns.filter(c => (c.status || '').includes('Review') || (c.status || '').includes('Pending')).length;
  const totalSpent = campaigns.reduce((acc, c) => acc + (c.spent || 0), 0);
  const totalClicks = campaigns.reduce((acc, c) => acc + (c.clicks || 0), 0);

  const handleSettingsSubmit = async (e) => {
    e.preventDefault();
    try {
    await onSaveProfile({
      candidate_name: candidateName,
      contesting_post: contestingPost,
      gaon_ward: ward,
      area_block: area,
      pincode: pincode,
      lat: gpsLocation.lat,
      lng: gpsLocation.lng,
      accuracy_m: gpsLocation.accuracy,
      symbol_name: symbol,
      photo_url: photo,
      default_slogan: defaultSlogan,
      disclaimer_text: disclaimer
    });
    setSaveError('');
    } catch (error) { setSaveError(error.message); }
  };

  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col font-sans">
      
      {/* Top Header */}
      <header className="h-16 bg-white border-b border-gray-200/80 px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gray-950 flex items-center justify-center shadow-sm">
            <Megaphone className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-black text-gray-950 tracking-tight">
            Politi<span className="text-emerald-600">Ads</span>
          </span>
          <span className="text-xs font-bold text-gray-400 hidden sm:inline border-l border-gray-200 pl-3">
            Candidate War-Room
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenCreateAdModal}
            className="px-4 py-2 rounded-full text-xs font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] transition shadow-sm flex items-center gap-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Launch New Ad</span>
            <span className="sm:hidden">New Ad</span>
          </button>

          {/* In-App Notifications */}
          <NotificationCenter />

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-full hover:bg-gray-100 transition border border-gray-200"
            >
              <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xs overflow-hidden">
                {profile?.photo_url ? (
                  <img src={profile.photo_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  user?.full_name?.[0] || 'U'
                )}
              </div>
              <span className="text-xs font-bold text-gray-800 hidden md:inline max-w-[120px] truncate">
                {user?.full_name || 'Candidate'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
            </button>

            {isProfileMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-gray-200 py-2 z-50 text-xs">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="font-bold text-gray-950 truncate">{user?.full_name}</p>
                  <p className="text-[11px] text-gray-500 truncate">{user?.email}</p>
                  <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800">
                    Role: {user?.role}
                  </span>
                </div>

                {user?.role === 'admin' && (
                  <button
                    onClick={() => {
                      setIsProfileMenuOpen(false);
                      onSwitchToAdmin();
                    }}
                    className="w-full px-4 py-2 text-left font-bold text-amber-700 hover:bg-amber-50 flex items-center gap-2"
                  >
                    <ShieldCheck className="w-4 h-4 text-amber-600" />
                    Switch to Super Admin Hub
                  </button>
                )}

                <button
                  onClick={() => {
                    setIsProfileMenuOpen(false);
                    onLogout();
                  }}
                  className="w-full px-4 py-2 text-left text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4 text-red-500" />
                  Log Out Securely
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex flex-col md:flex-row">
        
        {/* Left Sidebar */}
        <aside className="w-full md:w-64 bg-white border-r border-gray-200/80 p-5 flex flex-col justify-between shrink-0">
          <div>
            {/* Candidate Card Summary */}
            <div className="p-3.5 rounded-2xl bg-[#fafafa] border border-gray-200 mb-6">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-gray-200 border border-gray-300 overflow-hidden shrink-0 flex items-center justify-center">
                  {profile?.photo_url ? (
                    <img src={profile.photo_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <User className="w-6 h-6 text-gray-500" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="text-sm font-bold text-gray-950 truncate">{profile?.candidate_name || user?.full_name}</h4>
                  <p className="text-[11px] text-emerald-700 font-semibold truncate">{profile?.contesting_post || 'Candidate'}</p>
                  <p className="text-[10px] text-gray-500 truncate">{profile?.gaon_ward || 'Local Constituency'}</p>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="space-y-1">
              {[
                { id: 'overview', label: 'Overview & Analytics', icon: BarChart3 },
                { id: 'ads_manager', label: 'Ads Manager & Campaigns', icon: Megaphone, count: campaigns.length },
                { id: 'surveys_services', label: 'Surveys & Services', icon: Vote, badge: 'New' },
                { id: 'chess_spy', label: 'Chess Opponent Spy', icon: Target },
                { id: 'billing', label: 'Billing & Invoices', icon: CreditCard },
                { id: 'settings', label: 'Settings Canvas (All Details)', icon: Settings }
              ].map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                      isActive
                        ? 'bg-gray-950 text-white shadow-sm'
                        : 'text-gray-600 hover:text-gray-950 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-gray-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.count !== undefined && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                        isActive ? 'bg-gray-800 text-emerald-400' : 'bg-gray-200 text-gray-700'
                      }`}>
                        {item.count}
                      </span>
                    )}
                    {item.badge && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-500 text-gray-950">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="pt-6 border-t border-gray-100 space-y-2 mt-6">
            <a
              href="https://wa.me"
              target="_blank"
              rel="noreferrer"
              className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 transition"
            >
              <PhoneCall className="w-3.5 h-3.5 text-emerald-600" />
              Support contact
            </a>
          </div>
        </aside>

        {/* Dashboard Main Canvas */}
        <main className="flex-1 p-5 sm:p-8 overflow-y-auto">
          
          {/* TAB 1: Overview & Analytics */}
          {activeTab === 'overview' && (
            <div className="space-y-7">
              {/* Top 4 KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">Total Voter Reach</p>
                  <p className="text-2xl font-black text-gray-950">{hasLiveMetrics ? totalReach.toLocaleString() : 'Not available'}</p>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full inline-block mt-2">
                    Provider telemetry required
                  </span>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">Active Campaigns</p>
                  <p className="text-2xl font-black text-gray-950">{activeCount} Delivering</p>
                  <p className="text-[11px] text-gray-400 mt-2">
                    {pendingCount > 0 ? `${pendingCount} under company review` : 'No pending company reviews'}
                  </p>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">Total Ad Spend</p>
                  <p className="text-2xl font-black text-gray-950">{hasLiveMetrics ? `₹${totalSpent.toLocaleString()}` : 'Not available'}</p>
                  <span className="text-[11px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full inline-block mt-2">
                    Confirmed provider spend only
                  </span>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">Voter Clicks & WhatsApp</p>
                  <p className="text-2xl font-black text-gray-950">{hasLiveMetrics ? totalClicks.toLocaleString() : 'Not available'}</p>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full inline-block mt-2">
                    Direct voter inquiries
                  </span>
                </div>
              </div>

              <div className="bg-white border rounded-2xl p-5 space-y-3">
                {metaStatus?.message && <p role="alert" className="text-sm text-amber-800">{metaStatus.message}</p>}
                <p className="text-sm"><strong>Facebook:</strong> {metaStatus?.facebook_connected ? metaStatus.page_name : metaStatus?.connection_status || 'Not connected'}</p>
                <p className="text-sm"><strong>Instagram:</strong> {metaStatus?.instagram_connected ? `@${metaStatus.instagram_username}` : 'Not connected'}</p>
                <div className="flex flex-wrap gap-3">
                  <button onClick={() => { setMetaTarget('facebook'); setMetaModalOpen(true); }} className="px-4 py-2 rounded-full bg-blue-600 text-white">Connect Facebook</button>
                  <button disabled={!metaStatus?.facebook_connected} onClick={() => { setMetaTarget('instagram'); setMetaModalOpen(true); }} className="px-4 py-2 rounded-full bg-pink-600 text-white disabled:opacity-50">Connect Instagram</button>
                  {metaStatus?.instagram_connected && <button onClick={() => handleDisconnectMeta('instagram')} className="px-4 py-2 border rounded-full">Disconnect Instagram</button>}
                </div>
                <p className="text-xs text-gray-500">Instagram uses your Facebook Page authorization. App disconnect does not delete your social accounts or stop ads already running outside the app.</p>
              </div>
              {/* Meta Connection Status Card */}
              <div className="bg-gradient-to-r from-blue-50/70 via-indigo-50/50 to-pink-50/40 p-5 rounded-2xl border border-blue-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-2xs">
                <div className="flex items-start sm:items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-pink-500 flex items-center justify-center text-white shrink-0 shadow-xs">
                    <Share2 className="w-5 h-5" />
                  </div>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-gray-950">Meta Ad Network (Facebook &amp; Instagram)</h4>
                      {metaStatus?.is_connected ? (
                        <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
                          Facebook Connected
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold text-gray-600 bg-gray-200 px-2 py-0.5 rounded-full">
                          Not Connected
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600">
                      {metaStatus?.is_connected ? (
                        <span>Linked Page: <strong className="text-gray-900">{metaStatus.page_name}</strong> (ID: {metaStatus.page_id}) &bull; Instagram auto-enabled</span>
                      ) : (
                        <span>Connect your official Facebook Page to publish hyper-targeted ward election ads.</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
                  {metaStatus?.is_connected ? (
                    <>
                      <button
                        type="button"
                        onClick={() => { setMetaTarget('facebook'); setMetaModalOpen(true); }}
                        className="flex-1 sm:flex-initial px-4 py-2 rounded-full text-xs font-bold text-blue-700 bg-white hover:bg-blue-50 border border-blue-200 transition shadow-2xs"
                      >
                        Change Page
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDisconnectMeta('facebook')}
                        className="flex-1 sm:flex-initial px-3 py-2 rounded-full text-xs font-bold text-rose-700 bg-white hover:bg-rose-50 border border-rose-200 transition shadow-2xs"
                      >
                        Disconnect
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      onClick={() => { setMetaTarget('facebook'); setMetaModalOpen(true); }}
                      className="w-full sm:w-auto px-5 py-2.5 rounded-full text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2 transition shadow-xs"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                      <span>Connect Facebook &amp; Instagram</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Recent Campaigns Section */}
              <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-gray-950">Campaign Status</h3>
                  <button
                    onClick={() => setActiveTab('ads_manager')}
                    className="text-xs font-bold text-emerald-700 hover:underline"
                  >
                    View All Campaigns →
                  </button>
                </div>

                <div className="divide-y divide-gray-100">
                  {campaigns.slice(0, 3).map((ad) => (
                    <div key={ad.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-gray-950">{ad.title}</h4>
                          <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full">
                            {ad.badge}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-500 mt-0.5">
                          ₹{ad.budget}/day · {ad.radius} km radius · Reach: {ad.is_mock ? 'Not available' : ad.reach.toLocaleString()}
                        </p>
                      </div>
                      <span className={`text-xs font-bold px-3 py-1 rounded-full self-start sm:self-auto ${
                        ad.status.includes('Live') ? 'bg-emerald-100 text-emerald-800' :
                        ad.status.includes('Paused') ? 'bg-yellow-100 text-yellow-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {ad.status}
                      </span>
                    </div>
                  ))}
                  {campaigns.length === 0 && (
                    <div className="py-8 text-center text-xs text-gray-500">
                      No campaigns created yet. Click "+ Launch New Ad" to begin.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Ads Manager & Campaigns */}
          {activeTab === 'ads_manager' && (
            <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-gray-950">Campaigns Manager</h3>
                  <p className="text-xs text-gray-500">Drafts and provider statuses; mock records do not represent actual delivery.</p>
                </div>
                <button
                  onClick={onOpenCreateAdModal}
                  className="px-4 py-2 rounded-full text-xs font-bold bg-[#bbf7d0] hover:bg-[#86efac] text-gray-950 transition"
                >
                  + Create New Ad
                </button>
              </div>

              <div className="divide-y divide-gray-100">
                {campaignsLoading ? (
                  <div className="py-12 text-center text-xs text-gray-500 flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
                    Loading campaigns from server database...
                  </div>
                ) : campaignsError ? (
                  <div className="py-8 text-center text-xs text-red-600 space-y-2">
                    <p>{campaignsError}</p>
                    <button
                      onClick={onRefreshCampaigns}
                      className="px-3 py-1 bg-red-50 text-red-700 rounded-lg text-xs font-bold"
                    >
                      Retry
                    </button>
                  </div>
                ) : campaigns.length === 0 ? (
                  <div className="py-12 text-center space-y-3">
                    <Megaphone className="w-8 h-8 text-gray-300 mx-auto" />
                    <p className="text-xs text-gray-500">No campaigns launched yet.</p>
                    <button
                      onClick={onOpenCreateAdModal}
                      className="px-4 py-2 rounded-full text-xs font-bold bg-[#bbf7d0] text-gray-950"
                    >
                      + Launch Your First Ad
                    </button>
                  </div>
                ) : (
                  campaigns.map((ad) => (
                    <div key={ad.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-xs text-gray-950">{ad.title}</p>
                          {ad.meta_ad_id && (
                            <span className="text-[10px] font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                              Meta: {ad.meta_ad_id}
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-emerald-700 font-bold block mt-0.5">{ad.badge}</span>
                        <p className="text-[11px] text-gray-400 mt-0.5">
                          Budget: ₹{ad.budget}/day • Radius: {ad.radius} km • Reach: {ad.is_mock ? 'Not available' : ad.reach.toLocaleString()} voters
                        </p>
                      </div>

                      <div className="flex items-center gap-2 self-start sm:self-auto">
                        <button onClick={() => onViewCampaign(ad.id)} className="border border-gray-300 rounded-xl px-3 py-1 text-xs font-bold">View / Edit</button>
                        <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                          ad.status.includes('Live') ? 'bg-emerald-100 text-emerald-800' :
                          ad.status.includes('Paused') ? 'bg-yellow-100 text-yellow-800' :
                          'bg-amber-100 text-amber-800'
                        }`}>
                          {ad.status}
                        </span>

                        {!ad.is_mock && ad.delivery_status === 'Delivering' && (
                          <button
                            onClick={() => onToggleCampaignStatus(ad.id)}
                            title="Pause active campaign"
                            className="px-3 py-1 rounded-xl text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 flex items-center gap-1 transition"
                          >
                            <PauseCircle className="w-3.5 h-3.5 text-gray-600" />
                            Pause
                          </button>
                        )}

                        {!ad.is_mock && ad.provider_review_status === 'Approved' && ad.delivery_status === 'Paused' && (
                          <button
                            onClick={() => onToggleCampaignStatus(ad.id)}
                            title="Resume paused campaign"
                            className="px-3 py-1 rounded-xl text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-800 flex items-center gap-1 transition"
                          >
                            <PlayCircle className="w-3.5 h-3.5 text-emerald-600" />
                            Resume
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Surveys & Services */}
          {activeTab === 'surveys_services' && (
            <div className="space-y-6">
              <h3 className="text-lg font-bold text-gray-950">Political Surveys & Special Services</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 rounded-3xl bg-white border border-gray-200 shadow-sm space-y-3">
                  <h4 className="font-bold text-sm text-gray-900">Voter Opinion Poll Ads</h4>
                  <p className="text-xs text-gray-500">Run poll ads to collect voter sentiment on primary local ward issues.</p>
                  <button
                    onClick={onOpenCreateAdModal}
                    className="w-full py-2 rounded-full text-xs font-bold bg-[#bbf7d0] hover:bg-[#86efac] text-gray-950 transition"
                  >
                    + Launch Poll Ad
                  </button>
                </div>

                <div className="p-6 rounded-3xl bg-white border border-gray-200 shadow-sm space-y-3">
                  <h4 className="font-bold text-sm text-gray-900">In-App Updates</h4>
                  <p className="text-xs text-gray-500">Automated WhatsApp political messaging is unavailable. Review updates appear in the notification center.</p>
                  <a
                    href="https://wa.me"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2 rounded-full text-xs font-bold bg-gray-100 hover:bg-gray-200 text-gray-800 block text-center transition"
                  >
                    Unavailable
                  </a>
                </div>

                <div className="p-6 rounded-3xl bg-white border border-gray-200 shadow-sm space-y-3">
                  <h4 className="font-bold text-sm text-gray-900">Custom HD Video Reels</h4>
                  <p className="text-xs text-gray-500">High-impact 30-sec reels created by our political creative team with speech enhancements.</p>
                  <a
                    href="https://wa.me"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2 rounded-full text-xs font-bold bg-gray-100 hover:bg-gray-200 text-gray-800 block text-center transition"
                  >
                    Request Video
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Chess Opponent Spy */}
          {activeTab === 'chess_spy' && (
            <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-gray-950">Chess Opponent Spy Intelligence</h3>
              <p className="text-xs text-gray-500">
                Live competitor data is not available.
              </p>
              <div className="p-8 rounded-2xl bg-[#fafafa] border border-gray-200 text-center space-y-2">
                <Target className="w-10 h-10 text-emerald-600 mx-auto" />
                <h4 className="font-bold text-sm text-gray-900">Competitor Feed Unavailable</h4>
                <p className="text-xs text-gray-500 max-w-md mx-auto">
                  No live Ad Library integration is configured.
                </p>
              </div>
            </div>
          )}

          {/* TAB 5: Billing & Invoices */}
          {activeTab === 'billing' && (
            <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-gray-950">Billing & Payment Receipts</h3>
              <PaymentHistory />

            </div>
          )}

          {/* TAB 6: Settings Canvas */}
          {activeTab === 'settings' && (
            <div className="bg-white p-6 sm:p-8 rounded-3xl border border-gray-200 shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-950">Candidate Settings Canvas</h3>{saveError && <p role="alert" className="text-red-700">{saveError}</p>}
                  <p className="text-xs text-gray-500">Manage all your profile details, constituency GPS, photo, and legal disclaimer.</p>
                </div>
                <button
                  type="button"
                  onClick={handleSettingsSubmit}
                  disabled={isSavingProfile}
                  className="px-5 py-2.5 rounded-full text-xs font-bold bg-[#bbf7d0] hover:bg-[#86efac] disabled:opacity-50 text-gray-950 flex items-center gap-1.5 transition shadow-sm"
                >
                  {isSavingProfile ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  Save Changes to Database
                </button>
              </div>

              {saveError && <p role="alert" className="text-red-700">{saveError}</p>}
              <form onSubmit={handleSettingsSubmit} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-800 mb-1">Candidate Full Name</label>
                    <input
                      type="text"
                      value={candidateName}
                      onChange={(e) => setCandidateName(e.target.value)}
                      className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-800 mb-1">Contesting Post</label>
                    <select
                      value={contestingPost}
                      onChange={(e) => setContestingPost(e.target.value)}
                      className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm"
                    >
                      {CONTESTING_POSTS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-800 mb-1">Gaon / Ward</label>
                    <input
                      type="text"
                      value={ward}
                      onChange={(e) => setWard(e.target.value)}
                      className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-800 mb-1">Area / Block</label>
                    <input
                      type="text"
                      value={area}
                      onChange={(e) => setArea(e.target.value)}
                      className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-800 mb-1">Pincode</label>
                    <input
                      type="text"
                      maxLength={6}
                      value={pincode}
                      onChange={(e) => setPincode(e.target.value.replace(/\D/g, ''))}
                      className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm font-mono"
                    />
                  </div>
                  <div>
                    <LocationPicker
                      location={gpsLocation}
                      onChange={(coords) => setGpsLocation(coords)}
                      label="Constituency GPS Coordinates"
                    />
                  </div>
                </div>

                <div className="pt-2 border-t border-gray-100">
                  <ImageUploader
                    value={photo}
                    onChange={(dataUrl) => setPhoto(dataUrl)}
                    label="Candidate Display Photo"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-2">Election Symbol</label>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                    {DEFAULT_SYMBOLS.map((s) => (
                      <button
                        key={s.name}
                        type="button"
                        onClick={() => setSymbol(s.name)}
                        className={`p-2.5 rounded-xl border text-center transition ${
                          symbol === s.name
                            ? 'border-emerald-600 bg-emerald-50 text-emerald-950 font-bold'
                            : 'border-gray-200 bg-[#fafafa] text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <span className="text-2xl block">{s.icon}</span>
                        <span className="text-[11px] block mt-0.5 truncate">{s.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">Default Campaign Slogan</label>
                  <input
                    type="text"
                    value={defaultSlogan}
                    onChange={(e) => setDefaultSlogan(e.target.value)}
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">ECI Legal Disclaimer ("Paid for by")</label>
                  <input
                    type="text"
                    value={disclaimer}
                    onChange={(e) => setDisclaimer(e.target.value)}
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2 text-sm"
                  />
                </div>

                <div className="pt-4 border-t border-gray-100 flex justify-end">
                  <button
                    type="submit"
                    disabled={isSavingProfile}
                    className="px-6 py-3 rounded-full text-xs font-bold bg-[#bbf7d0] hover:bg-[#86efac] disabled:opacity-50 text-gray-950 flex items-center gap-2 transition shadow-md"
                  >
                    {isSavingProfile ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
                    Save Changes to Database
                  </button>
                </div>
              </form>
            </div>
          )}

        </main>
      </div>

      {metaModalOpen && <MetaConnectModal
        isOpen={metaModalOpen}
        target={metaTarget}
        onClose={() => setMetaModalOpen(false)}
        onConnected={() => {
          fetchMetaStatus();
          setMetaModalOpen(false);
        }}
        initialPage={metaStatus?.is_connected ? { id: metaStatus.page_id, name: metaStatus.page_name } : null}
      />}
    </div>
  );
}
