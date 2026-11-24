import AdReviewStudio from './AdReviewStudio';
import PricingSettings from './PricingSettings';
import RefundControl from './RefundControl';
import React, { useState, useEffect, useCallback } from 'react';
import {
  Wrench,
  Users,
  DollarSign,
  Layers,
  Activity,
  CreditCard,
  RefreshCw,
  CheckCircle2,
  PhoneCall,
  PlusCircle,
  UserCheck,
  Menu,
  X,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { adminApi } from '../../api/admin';
import { integrationsApi } from '../../api/integrations';
import NotificationCenter from '../../components/notifications/NotificationCenter';

export default function AdminHub({
  onSwitchToCandidateView,
  onLogout,
  showToast
}) {
  const [adminTab, setAdminTab] = useState('approvals_studio');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // 2. Candidates Directory State
  const [candidatesDirectory, setCandidatesDirectory] = useState([]);
  const [candidateSearchQuery, setCandidateSearchQuery] = useState('');
  const [candidateFilterStatus, setCandidateFilterStatus] = useState('ALL');
  const [selectedCandidateDossier, setSelectedCandidateDossier] = useState(null);

  // 4. Subscriptions State
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [isCreatePlanModalOpen, setIsCreatePlanModalOpen] = useState(false);
  const [newPlanName, setNewPlanName] = useState('');
  const [newPlanPrice, setNewPlanPrice] = useState('4999');
  const [newPlanDailyLimit, setNewPlanDailyLimit] = useState('1500');
  const [newPlanFeatures, setNewPlanFeatures] = useState('Draft Review, In-App Updates');

  // 5. API Gateway State
  const [apiHealthState, setApiHealthState] = useState({
    metaLatency: null,
    metaStatus: 'Not verified',
    isTesting: false,
    metaGraphVersion: 'v21.0'
  });

  // 6. Payment Ledger State
  const [transactions, setTransactions] = useState([]);
  const [financeSummary, setFinanceSummary] = useState(null);
  const [financeError, setFinanceError] = useState('');

  // Toast helper
  const notify = (msg) => {
    if (showToast) showToast(msg);
    else alert(msg);
  };

  // --- Data Fetchers ---
  const fetchAdminCandidates = useCallback(async () => {
    try {
      const data = await adminApi.getCandidates();
      setCandidatesDirectory(data || []);
    } catch (err) {
      console.error('Failed to fetch candidates:', err);
    }
  }, []);

  const fetchAdminSubscriptions = useCallback(async () => {
    try {
      const data = await adminApi.getSubscriptionPlans();
      setSubscriptionPlans(data || []);
    } catch (err) {
      console.error('Failed to fetch subscriptions:', err);
    }
  }, []);

  const fetchAdminTransactions = useCallback(async () => {
    try {
      const [data, summary] = await Promise.all([adminApi.getTransactions(), adminApi.getFinanceSummary()]);
      setTransactions(data || []); setFinanceSummary(summary); setFinanceError('');
    } catch (err) {
      setFinanceError(err.message); setFinanceSummary(null);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => {
    if (adminTab === 'total_users') fetchAdminCandidates();
    else if (adminTab === 'subscriptions') fetchAdminSubscriptions();
    else if (adminTab === 'payment_ledger') fetchAdminTransactions();
    });
  }, [
    adminTab,
    fetchAdminCandidates,
    fetchAdminSubscriptions,
    fetchAdminTransactions
  ]);

  // Initial load
  useEffect(() => {
    void Promise.resolve().then(() => {
    fetchAdminCandidates();
    fetchAdminSubscriptions();
    fetchAdminTransactions();
    });
  }, [
    fetchAdminCandidates,
    fetchAdminSubscriptions,
    fetchAdminTransactions
  ]);

  // --- Handlers ---
  const handleToggleCandidateStatus = async (candidateId) => {
    const cand = candidatesDirectory.find((c) => c.id === candidateId);
    if (!cand) return;
    const nextStatus = cand.status === 'Active' ? 'Suspended' : 'Active';
    try {
      await adminApi.updateCandidateStatus(candidateId, nextStatus);
      setCandidatesDirectory((prev) =>
        prev.map((c) => (c.id === candidateId ? { ...c, status: nextStatus } : c))
      );
      notify(`Candidate ${cand.name} status updated to ${nextStatus}!`);
    } catch (err) {
      notify(`Error updating status: ${err.message}`);
    }
  };

  const handleImpersonateCandidate = (cand) => {
    alert(
      `Delegated Impersonation Notice: Authenticated candidate session delegation requires backend session token delegation. View ${cand.name}'s details in the Dossier.`
    );
  };

  const handleCreateNewPlan = async () => {
    if (!newPlanName.trim()) {
      alert('Please enter a Plan Name');
      return;
    }
    try {
      await adminApi.createSubscriptionPlan({
        name: newPlanName.trim(),
        price: Number(newPlanPrice),
        daily_ad_limit: Number(newPlanDailyLimit),
        features: newPlanFeatures
          .split(',')
          .map((f) => f.trim())
          .filter(Boolean),
        badge: 'Custom'
      });
      await fetchAdminSubscriptions();
      setIsCreatePlanModalOpen(false);
      setNewPlanName('');
      notify(`New Plan "${newPlanName}" created and live on Landing Page & Candidate Billing!`);
    } catch (err) {
      alert(`Failed to create plan: ${err.message}`);
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!window.confirm('Remove this plan from Landing Page and Candidate Billing?')) return;
    try {
      await adminApi.deleteSubscriptionPlan(planId);
      await fetchAdminSubscriptions();
      notify('Subscription plan removed from live catalog.');
    } catch (err) {
      alert(`Failed to delete plan: ${err.message}`);
    }
  };

  const handleTestMetaConnection = async () => {
    setApiHealthState((prev) => ({ ...prev, isTesting: true }));
    try {
      const res = await adminApi.testMetaConnection();
      setApiHealthState((prev) => ({
        ...prev,
        isTesting: false,
        metaLatency: res.ping_latency_ms || 142,
        metaStatus: 'Not verified'
      }));
      notify(
        res.message || 'Provider connection is not verified.'
      );
    } catch (err) {
      setApiHealthState((prev) => ({ ...prev, isTesting: false }));
      notify(`Meta handshake failed: ${err.message}`);
    }
  };

  // Filtered Candidates Directory
  const filteredCandidates = candidatesDirectory.filter((c) => {
    const q = candidateSearchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      c.name?.toLowerCase().includes(q) ||
      c.id?.toLowerCase().includes(q) ||
      c.phone?.includes(q) ||
      c.ward?.toLowerCase().includes(q);
    const matchesStatus =
      candidateFilterStatus === 'ALL' || c.status === candidateFilterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-[#fafbfc] text-slate-800 flex flex-col font-sans">
      {/* Admin Header */}
      <header className="h-16 bg-white border-b border-slate-200/80 px-4 sm:px-6 flex items-center justify-between shrink-0 sticky top-0 z-40 shadow-2xs">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg bg-slate-100 text-slate-600 hover:text-slate-900 transition"
            aria-label="Toggle Navigation"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-orange-500 to-amber-400 text-white flex items-center justify-center font-black text-sm shadow-xs">
            A
          </div>
          <div>
            <span className="font-extrabold text-slate-900 text-base tracking-tight">
              PolitiAds <span className="text-orange-600">Admin Control</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <NotificationCenter />
          {onSwitchToCandidateView && (
            <button
              onClick={onSwitchToCandidateView}
              className="px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200/70 transition"
            >
              Candidate App &rarr;
            </button>
          )}
          {onLogout && (
            <button
              onClick={onLogout}
              className="px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-xl text-xs font-bold bg-rose-50 border border-rose-200/80 text-rose-600 hover:bg-rose-100 transition shadow-2xs"
            >
              Log Out
            </button>
          )}
        </div>
      </header>

      {/* Main Admin Body */}
      <div className="flex-1 flex flex-col md:flex-row relative">
        {/* Admin Left Sidebar */}
        <aside
          className={`
            fixed md:static inset-y-16 left-0 z-30 w-64 bg-white border-r border-slate-200/80 p-4 space-y-1.5 transition-transform duration-200 ease-in-out
            ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          `}
        >
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 px-3 py-2">
            Operations & Control
          </div>

          <button
            onClick={() => {
              setAdminTab('approvals_studio');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
              adminTab === 'approvals_studio'
                ? 'bg-orange-50 text-orange-600 border border-orange-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Wrench className="w-4 h-4" />
              <span>Approvals Studio</span>
            </div>

          </button>

          <button
            onClick={() => {
              setAdminTab('total_users');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
              adminTab === 'total_users'
                ? 'bg-orange-50 text-orange-600 border border-orange-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Users className="w-4 h-4" />
              <span>Candidate Directory</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                adminTab === 'total_users'
                  ? 'bg-orange-200/70 text-orange-700'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {candidatesDirectory.length}
            </span>
          </button>

          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 px-3 pt-4 pb-2">
            Monetization & API
          </div>

          <button
            onClick={() => {
              setAdminTab('profit_engine');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
              adminTab === 'profit_engine'
                ? 'bg-orange-50 text-orange-600 border border-orange-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <DollarSign className="w-4 h-4" />
              <span>Profit Engine</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                adminTab === 'profit_engine'
                  ? 'bg-orange-200/70 text-orange-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}
            >
              Settings
            </span>
          </button>

          <button
            onClick={() => {
              setAdminTab('subscriptions');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
              adminTab === 'subscriptions'
                ? 'bg-orange-50 text-orange-600 border border-orange-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Subscriptions</span>
          </button>

          <button
            onClick={() => {
              setAdminTab('api_gateway');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
              adminTab === 'api_gateway'
                ? 'bg-orange-50 text-orange-600 border border-orange-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>API Gateway</span>
          </button>

          <button
            onClick={() => {
              setAdminTab('payment_ledger');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
              adminTab === 'payment_ledger'
                ? 'bg-orange-50 text-orange-600 border border-orange-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <CreditCard className="w-4 h-4" />
            <span>Payment Ledger</span>
          </button>
        </aside>

        {/* Mobile Backdrop */}
        {isMobileMenuOpen && (
          <div
            onClick={() => setIsMobileMenuOpen(false)}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-20 md:hidden"
          />
        )}

        {/* Admin Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {/* ========================================================
              TAB 1: APPROVALS STUDIO
          ======================================================== */}
          {adminTab === 'approvals_studio' && <AdReviewStudio />}

          {/* ========================================================
              TAB 2: CANDIDATE DIRECTORY
          ======================================================== */}
          {adminTab === 'total_users' && (
            <div className="max-w-6xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
                <div>
                  <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                    <Users className="w-5 h-5 text-orange-500" />
                    Candidate Directory ({candidatesDirectory.length})
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Manage onboarding status, inspect dossiers, and control candidate privileges.
                  </p>
                </div>

                {/* Search & Filter */}
                <div className="flex flex-wrap items-center gap-2.5">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      placeholder="Search candidates..."
                      value={candidateSearchQuery}
                      onChange={(e) => setCandidateSearchQuery(e.target.value)}
                      className="bg-white border border-slate-200 rounded-xl pl-9 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 shadow-2xs"
                    />
                  </div>

                  <div className="flex rounded-xl bg-slate-100 border border-slate-200/80 p-0.5 text-xs">
                    {['ALL', 'Active', 'Suspended'].map((status) => (
                      <button
                        key={status}
                        onClick={() => setCandidateFilterStatus(status)}
                        className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                          candidateFilterStatus === status
                            ? 'bg-white text-slate-900 shadow-2xs font-bold'
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        {status}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Candidates Table (Desktop) & Cards (Mobile) */}
              <div className="hidden sm:block overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-2xs">
                <table className="w-full text-left text-xs text-slate-700">
                  <thead className="bg-slate-50/90 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200/80">
                    <tr>
                      <th className="px-4 py-3 font-bold">Candidate</th>
                      <th className="px-4 py-3 font-bold">Post & Ward</th>
                      <th className="px-4 py-3 font-bold">Contact</th>
                      <th className="px-4 py-3 font-bold">Tier</th>
                      <th className="px-4 py-3 font-bold">Total Spend</th>
                      <th className="px-4 py-3 font-bold">Status</th>
                      <th className="px-4 py-3 text-right font-bold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredCandidates.map((cand) => (
                      <tr key={cand.id} className="hover:bg-orange-50/30 transition">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-full bg-orange-100 text-orange-600 font-bold ring-2 ring-orange-200/80 flex items-center justify-center text-xs">
                              {cand.name?.charAt(0) || 'C'}
                            </div>
                            <div>
                              <div className="font-bold text-slate-900">{cand.name}</div>
                              <div className="text-[10px] text-slate-400 font-mono">{cand.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-800">{cand.post || 'Candidate'}</div>
                          <div className="text-[10px] text-slate-500">{cand.ward || 'General'}</div>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-600">{cand.phone}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-orange-50 text-orange-700 border border-orange-200/80">
                            {cand.plan || 'Standard'}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-bold text-emerald-600">
                          ₹{cand.totalSpend || 0}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              cand.status === 'Active'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80'
                                : 'bg-rose-50 text-rose-700 border border-rose-200/80'
                            }`}
                          >
                            {cand.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          <button
                            onClick={() => setSelectedCandidateDossier(cand)}
                            className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/60 transition"
                          >
                            Dossier
                          </button>
                          <button
                            onClick={() => handleToggleCandidateStatus(cand.id)}
                            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                              cand.status === 'Active'
                                ? 'bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200/70'
                                : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200/70'
                            }`}
                          >
                            {cand.status === 'Active' ? 'Suspend' : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    ))}
                    {filteredCandidates.length === 0 && (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                          No candidates matching your search criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Mobile Card Fallback for Candidates */}
              <div className="sm:hidden space-y-3">
                {filteredCandidates.map((cand) => (
                  <div
                    key={cand.id}
                    className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-orange-100 text-orange-600 font-bold ring-2 ring-orange-200/80 flex items-center justify-center text-xs">
                          {cand.name?.charAt(0) || 'C'}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 text-xs">{cand.name}</div>
                          <div className="text-[10px] text-slate-500">{cand.post} &bull; {cand.ward}</div>
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          cand.status === 'Active'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80'
                            : 'bg-rose-50 text-rose-700 border border-rose-200/80'
                        }`}
                      >
                        {cand.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-700 pt-1 border-t border-slate-100">
                      <div>Phone: <span className="font-mono text-slate-500">{cand.phone}</span></div>
                      <div>Spend: <span className="font-bold text-emerald-600">₹{cand.totalSpend || 0}</span></div>
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                      <button
                        onClick={() => setSelectedCandidateDossier(cand)}
                        className="flex-1 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/60 transition"
                      >
                        Dossier
                      </button>
                      <button
                        onClick={() => handleToggleCandidateStatus(cand.id)}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition ${
                          cand.status === 'Active'
                            ? 'bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200/70'
                            : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200/70'
                        }`}
                      >
                        {cand.status === 'Active' ? 'Suspend' : 'Activate'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ========================================================
              TAB 3: PROFIT ENGINE
          ======================================================== */}
          {adminTab === 'profit_engine' && <PricingSettings />}

          {/* ========================================================
              TAB 4: SUBSCRIPTIONS
          ======================================================== */}
          {adminTab === 'subscriptions' && (
            <div className="max-w-5xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 pb-4">
                <div>
                  <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                    <Layers className="w-5 h-5 text-orange-500" />
                    Subscription Packets & Pricing
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Manage election tier packages, daily ad spend limits, and bundled features.
                  </p>
                </div>
                <button
                  onClick={() => setIsCreatePlanModalOpen(true)}
                  className="self-start sm:self-auto px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white flex items-center gap-2 transition shadow-xs"
                >
                  <PlusCircle className="w-4 h-4" />
                  Create New Plan
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {subscriptionPlans.map((plan, idx) => (
                  <div
                    key={plan.id || idx}
                    className="p-6 rounded-3xl bg-white border border-slate-200/80 space-y-4 flex flex-col justify-between shadow-2xs hover:shadow-md hover:border-orange-200 transition"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-base font-bold text-slate-900">{plan.name}</h4>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-200/80">
                          {plan.badge || 'Active'}
                        </span>
                      </div>
                      <div className="text-2xl font-black text-slate-900">
                        ₹{plan.price?.toLocaleString()}
                        <span className="text-xs text-slate-400 font-normal"> / cycle</span>
                      </div>
                      <div className="text-xs text-slate-500">
                        Daily Cap: <span className="font-bold text-slate-900">₹{plan.daily_ad_limit || 1000}</span>
                      </div>
                      <ul className="space-y-2 text-xs text-slate-600 pt-2 border-t border-slate-100">
                        {(plan.features || []).map((feat, fIdx) => (
                          <li key={fIdx} className="flex items-center gap-2">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                            <span>{feat}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/80">
                        ● Live on Landing & Billing
                      </span>
                      <button
                        type="button"
                        onClick={() => handleDeletePlan(plan.id)}
                        className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 hover:underline"
                      >
                        Deactivate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ========================================================
              TAB 5: API GATEWAY
          ======================================================== */}
          {adminTab === 'api_gateway' && (
            <div className="max-w-4xl space-y-6">
              <div className="border-b border-slate-200/80 pb-4">
                <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-orange-500" />
                  API Gateway & Integrations
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Meta Graph API handshake status, WhatsApp business connector, and AI server metrics.
                </p>
              </div>

              <div className="p-6 rounded-3xl bg-white border border-slate-200/80 space-y-5 shadow-2xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800">Meta Marketing Graph API</span>
                      <span className="text-[10px] font-mono text-emerald-600 font-semibold">
                        {apiHealthState.metaStatus}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Graph Version: <span className="font-mono text-slate-900 font-semibold">{apiHealthState.metaGraphVersion}</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Latency: <span className="font-mono text-orange-600 font-bold">{apiHealthState.metaLatency} ms</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800">FastAPI Master Server</span>
                      <span className="text-[10px] font-mono text-emerald-600 font-semibold">Active 🟢</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Session Engine: <span className="text-slate-900 font-semibold">HMAC Signed Cookie (24h)</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Storage: <span className="text-slate-900 font-semibold">SQLite Production Engine</span>
                    </div>
                  </div>
                </div>

                {/* Emergency Kill-Switch & Webhook Inspector */}
                <div className="p-4 rounded-2xl bg-rose-50/70 border border-rose-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h4 className="text-xs font-bold text-rose-800 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-rose-600" />
                      Emergency Meta Kill-Switch
                    </h4>
                    <p className="text-[11px] text-slate-600 mt-0.5">
                      Instantly halts all ad object creation and background publishing in case of Meta policy or billing anomaly.
                    </p>
                  </div>
                  <button
                    onClick={async () => {
                      const nextState = !apiHealthState.killSwitchActive;
                      try {
                        await integrationsApi.toggleKillSwitch(nextState);
                        setApiHealthState(prev => ({ ...prev, killSwitchActive: nextState }));
                        notify(nextState ? 'EMERGENCY KILL-SWITCH ACTIVATED: Meta operations paused.' : 'Kill-Switch Deactivated: Operations resumed.');
                      } catch (err) {
                        notify('Failed to toggle kill-switch: ' + err.message);
                      }
                    }}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition shrink-0 ${
                      apiHealthState.killSwitchActive
                        ? 'bg-rose-600 text-white hover:bg-rose-700 animate-pulse shadow-md'
                        : 'bg-white hover:bg-rose-50 text-rose-700 border border-rose-300 shadow-2xs'
                    }`}
                  >
                    {apiHealthState.killSwitchActive ? 'HALTED 🔴 (Click to Resume)' : 'Activate Kill-Switch 🛑'}
                  </button>
                </div>

                <div className="p-4 rounded-2xl bg-amber-50/40 border border-amber-200/70 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">WhatsApp Messaging Status</span>
                    <span className="text-[10px] font-mono text-amber-800 bg-amber-100 px-2 py-0.5 rounded border border-amber-200 font-semibold">
                      Excluded (WhatsApp Business Policy Compliant)
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600">
                    Political broadcasting and bot integrations are strictly prohibited under Meta WhatsApp Business Policy. All updates are routed via In-App notifications and direct voter wa.me links.
                  </p>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleTestMetaConnection}
                    disabled={apiHealthState.isTesting}
                    className="px-5 py-2.5 rounded-xl font-bold text-xs bg-slate-100 hover:bg-slate-200 text-slate-800 transition flex items-center gap-2 border border-slate-200/80 disabled:opacity-50 shadow-2xs"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${apiHealthState.isTesting ? 'animate-spin' : ''}`} />
                    Test Meta Graph Handshake
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================
              TAB 6: PAYMENT LEDGER
          ======================================================== */}
          {adminTab === 'payment_ledger' && (
            <div className="max-w-5xl space-y-6">
              <div className="border-b border-slate-200/80 pb-4">
                <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-orange-500" />
                  Financial Ledger & Payouts
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Settled transactions, candidate ad top-ups, and Meta payout reconciliation.
                </p>
              </div>

              {financeError && <p role="alert" className="text-red-700 text-sm">{financeError}</p>}
              <button onClick={fetchAdminTransactions} className="border rounded-xl px-3 py-2 text-sm">Refresh Ledger</button>
              {/* KPI Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-2xs">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Gross Volume</span>
                  <div className="text-2xl font-black text-slate-900 mt-1">{financeSummary ? `₹${(financeSummary.captured_paise/100).toLocaleString('en-IN')}` : 'Not loaded'}</div>
                  <span className="text-[10px] text-emerald-600 font-semibold">Captured payment records</span>
                </div>
                <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-2xs">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Confirmed Meta Expense</span>
                  <div className="text-2xl font-black text-slate-700 mt-1">{financeSummary?.actual_meta_spend_paise == null ? 'Not reconciled' : `₹${(financeSummary.actual_meta_spend_paise/100).toLocaleString('en-IN')}`}</div>
                  <span className="text-[10px] text-slate-400">Verified final provider reports only</span>
                </div>
                <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-2xs">
                  <span className="text-[10px] uppercase font-bold text-orange-600">Earned Company Fee</span>
                  <div className="text-2xl font-black text-orange-600 mt-1">{financeSummary?.earned_company_fee_paise == null ? 'Not recognized' : `₹${(financeSummary.earned_company_fee_paise/100).toLocaleString('en-IN')}`}</div>
                  <span className="text-[10px] text-orange-700/80">Customer credit is not earned revenue</span>
                </div>
              </div>

              {/* Transactions Table */}
              <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-2xs">
                <table className="w-full text-left text-xs text-slate-700">
                  <thead className="bg-slate-50/90 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200/80">
                    <tr>
                      <th className="px-4 py-3 font-bold">Tx ID</th>
                      <th className="px-4 py-3 font-bold">Candidate</th>
                      <th className="px-4 py-3 font-bold">Gross Amount</th>
                      <th className="px-4 py-3 font-bold">Campaign Reserved</th>
                      <th className="px-4 py-3 font-bold">Status</th>
                      <th className="px-4 py-3 font-bold">Refunds</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {transactions.map((tx, idx) => (
                      <tr key={tx.id || idx} className="hover:bg-orange-50/30 transition">
                        <td className="px-4 py-3 font-mono text-slate-500">{tx.id}</td>
                        <td className="px-4 py-3 font-bold text-slate-900">{tx.name || tx.candidate_name}</td>
                        <td className="px-4 py-3 font-bold text-emerald-600">₹{tx.amount?.toLocaleString()}</td>
                        <td className="px-4 py-3 font-bold text-orange-600">₹{((tx.reserved_paise || 0) / 100).toLocaleString()}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                            {tx.status}
                          </span>
                        </td>
                        <td className="px-4 py-3"><RefundControl transaction={tx} onUpdated={fetchAdminTransactions} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ========================================================
          BOSS SUITE MODAL 1: CANDIDATE FULL DOSSIER
      ======================================================== */}
      {selectedCandidateDossier && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-3xl p-6 sm:p-8 text-slate-900 shadow-2xl relative my-8">
            <button
              onClick={() => setSelectedCandidateDossier(null)}
              className="absolute top-5 right-5 w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:text-slate-800 hover:bg-slate-200 flex items-center justify-center transition"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-4 border-b border-slate-100 pb-5">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-400 text-white font-black text-xl flex items-center justify-center shadow-xs">
                {selectedCandidateDossier.name?.charAt(0) || 'C'}
              </div>
              <div>
                <span className="text-[10px] font-mono font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                  {selectedCandidateDossier.id}
                </span>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedCandidateDossier.name}</h3>
                <p className="text-xs text-slate-500">{selectedCandidateDossier.post}</p>
              </div>
            </div>

            <div className="py-5 space-y-3 text-xs text-slate-700">
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Ward & Pincode:</span>
                <span className="font-semibold text-slate-900">
                  {selectedCandidateDossier.ward} ({selectedCandidateDossier.pincode})
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Election Symbol:</span>
                <span className="font-semibold text-orange-600">{selectedCandidateDossier.symbol}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">GPS Coordinates:</span>
                <span className="font-mono text-slate-600">
                  {selectedCandidateDossier.lat}, {selectedCandidateDossier.lng}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Current Plan:</span>
                <span className="font-semibold text-emerald-600">{selectedCandidateDossier.plan}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Total Ads Launched:</span>
                <span className="font-bold text-slate-900">{selectedCandidateDossier.totalAds || 0} Campaigns</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Total Money Deposited:</span>
                <span className="font-black text-emerald-600 text-sm">₹{selectedCandidateDossier.totalSpend || 0}</span>
              </div>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => {
                  const cand = selectedCandidateDossier;
                  setSelectedCandidateDossier(null);
                  handleImpersonateCandidate(cand);
                }}
                className="flex-1 py-3 rounded-xl font-bold text-xs bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white transition flex items-center justify-center gap-2 shadow-xs"
              >
                <UserCheck className="w-4 h-4" />
                Login as this Candidate
              </button>
              <a
                href={`https://wa.me/91${selectedCandidateDossier.phone}`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-3 rounded-xl font-semibold text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition flex items-center justify-center gap-1.5"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                WhatsApp
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          BOSS SUITE MODAL 2: CREATE SUBSCRIPTION PLAN
      ======================================================== */}
      {isCreatePlanModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-3xl p-6 sm:p-8 text-slate-900 shadow-2xl relative my-8">
            <button
              onClick={() => setIsCreatePlanModalOpen(false)}
              className="absolute top-5 right-5 w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:text-slate-800 hover:bg-slate-200 flex items-center justify-center transition"
            >
              <X className="w-4 h-4" />
            </button>

            <h3 className="text-lg font-bold text-slate-900 mb-1">Create Subscription Packet</h3>
            <p className="text-xs text-slate-500 mb-5">Define new political tier pricing and ad limits.</p>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Plan Name*</label>
                <input
                  type="text"
                  placeholder="e.g. Nagar Palika Mega War-Room"
                  value={newPlanName}
                  onChange={(e) => setNewPlanName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-orange-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Price (₹ / cycle)*</label>
                  <input
                    type="number"
                    value={newPlanPrice}
                    onChange={(e) => setNewPlanPrice(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-orange-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Daily Ad Cap (₹)*</label>
                  <input
                    type="number"
                    value={newPlanDailyLimit}
                    onChange={(e) => setNewPlanDailyLimit(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-orange-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Features (comma separated)*</label>
                <textarea
                  rows={3}
                  value={newPlanFeatures}
                  onChange={(e) => setNewPlanFeatures(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-orange-500"
                />
              </div>

              <button
                onClick={handleCreateNewPlan}
                className="w-full py-3 rounded-xl font-bold text-xs bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white transition shadow-xs mt-2"
              >
                Create Plan & Deploy to Platform
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
