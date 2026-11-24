import React, { useState, useEffect } from 'react';
import { integrationsApi } from '../../api/integrations';
import {
  Megaphone,
  ArrowRight,
  ShieldCheck,
  Vote,
  Sliders,
  PhoneCall,
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function LandingPage({
  onOpenAuth,
  onNavigate,
  onLogout
}) {
  const { user, isAuthenticated } = useAuth();

  // Landing Page Interactive Simulator State
  const [simName, setSimName] = useState('Rajesh Sharma');
  const [simPhone, setSimPhone] = useState('9876543210');
  const [simPost, setSimPost] = useState('Ward Councillor / Corporator');
  const [simArea, setSimArea] = useState('Civil Lines, Ward 14');
  const [simRadius, setSimRadius] = useState(8);
  const [simSymbol, setSimSymbol] = useState('Car');
  const [simBudget, setSimBudget] = useState(500);

  // Buffer signature pill input
  const [pillName, setPillName] = useState('');

  // Live Dynamic Plans from Super Admin
  const [livePlans, setLivePlans] = useState([]);
  const [_plansLoading, setPlansLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    integrationsApi.getPublicPlans()
      .then((data) => {
        if (isMounted && Array.isArray(data) && data.length > 0) {
          setLivePlans(data);
        }
      })
      .catch((err) => {
        console.warn('Using offline plan fallback:', err);
      })
      .finally(() => {
        if (isMounted) setPlansLoading(false);
      });
    return () => { isMounted = false; };
  }, []);

  // Reach estimates
  const simReachMin = Math.round(simBudget * 28);
  const simReachMax = Math.round(simBudget * 44);

  const handlePillSubmit = (e) => {
    e.preventDefault();
    if (pillName.trim()) {
      setSimName(pillName.trim());
    }
    if (onOpenAuth) {
      onOpenAuth('signup');
    }
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Commit Banner */}
      <div className="bg-[#0b1320] text-gray-200 text-xs py-2.5 px-4 text-center border-b border-gray-800">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-3 flex-wrap">
          <span className="font-bold tracking-wider text-emerald-400 uppercase text-[10px] bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
            Chess Model 2.0
          </span>
          <span className="text-gray-300">
            Development preview: submit drafts for company review. Live advertising and competitor tracking are unavailable.
          </span>
          <a
            href="#chess-model"
            className="underline font-semibold text-white hover:text-emerald-400 transition ml-1"
          >
            Explore Chess Model &rarr;
          </a>
        </div>
      </div>

      {/* Clean Public Navbar (Buffer Style) */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-9 h-9 rounded-lg bg-gray-950 flex items-center justify-center shadow-sm">
              <Megaphone className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-black tracking-tight text-gray-950 flex items-center">
              Politi<span className="text-emerald-600">Ads</span>
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-7 text-[15px] font-medium text-gray-700">
            <a href="#simulator" className="hover:text-gray-950 transition">
              Ad Simulator
            </a>
            <a href="#chess-model" className="hover:text-gray-950 transition">
              Chess Model
            </a>
            <a href="#pricing" className="hover:text-gray-950 transition">
              Pricing
            </a>
            <a href="#faq" className="hover:text-gray-950 transition">
              FAQ
            </a>
          </nav>

          {/* Action Buttons: Dynamic based on Session */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-2 sm:gap-3">
                <span className="text-xs text-gray-600 hidden lg:inline">
                  Signed in as <b className="text-gray-950">{user?.full_name}</b> ({user?.role})
                </span>
                {user?.role === 'admin' ? (
                  <button
                    onClick={() => onNavigate && onNavigate('admin')}
                    className="px-4 py-2 rounded-full text-xs font-bold text-slate-950 bg-amber-400 hover:bg-amber-300 transition shadow-sm"
                  >
                    Super Admin Hub
                  </button>
                ) : (
                  <button
                    onClick={() => onNavigate && onNavigate('dashboard')}
                    className="px-4 py-2 rounded-full text-xs font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] transition shadow-sm"
                  >
                    My Dashboard
                  </button>
                )}
                {onLogout && (
                  <button
                    onClick={onLogout}
                    className="px-3.5 py-2 rounded-full text-xs font-semibold text-gray-600 hover:text-red-600 hover:bg-red-50 transition"
                  >
                    Log out
                  </button>
                )}
              </div>
            ) : (
              <>
                <button
                  onClick={() => onOpenAuth && onOpenAuth('login')}
                  className="px-4 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm font-semibold text-gray-800 hover:text-gray-950 transition"
                >
                  Log in
                </button>
                <button
                  onClick={() => onOpenAuth && onOpenAuth('signup')}
                  className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-semibold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] transition shadow-sm"
                >
                  Get started for free
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-14 pb-20 md:pt-24 md:pb-32 bg-[#fafafa] bg-grid-pattern border-b border-gray-100 overflow-hidden">
        {/* Floating Badges */}
        <div className="hidden lg:block absolute left-12 top-24 bg-white/90 backdrop-blur-md p-3 rounded-2xl shadow-lg border border-gray-100 animate-bounce duration-1000">
          <div className="flex items-center gap-2 text-xs font-semibold text-gray-800">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            Meta ECI Verified Templates
          </div>
        </div>

        <div className="hidden lg:block absolute right-14 top-36 bg-white/90 backdrop-blur-md p-3.5 rounded-2xl shadow-lg border border-gray-100">
          <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">
            Ward Reach Efficiency
          </div>
          <div className="text-sm font-black text-emerald-700">₹0.04 / Local Voter</div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <Vote className="w-3.5 h-3.5" />
            Engineered for Gram Panchayat, Nagar Palika & Vidhan Sabha
          </span>

          <h1 className="text-4xl sm:text-6xl font-black text-gray-950 tracking-tight leading-[1.12]">
            Build your election campaign audience. Grow on Facebook & Instagram.
          </h1>

          <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto font-normal leading-relaxed">
            Stop wasting budget on broad city targeting. Launch hyper-local, symbol-pinned Facebook
            and Instagram ads within 3km of your polling booth in 60 seconds.
          </p>

          {/* Buffer Signature Pill Input Bar */}
          <div className="pt-4 max-w-xl mx-auto">
            <form
              onSubmit={handlePillSubmit}
              className="bg-white p-2 rounded-full border border-gray-200 shadow-xl flex items-center justify-between transition focus-within:ring-2 focus-within:ring-emerald-500/20"
            >
              <input
                type="text"
                placeholder="Enter candidate name (e.g. Ramesh Kumar)"
                value={pillName}
                onChange={(e) => setPillName(e.target.value)}
                className="w-full pl-5 pr-2 py-2 text-xs sm:text-sm bg-transparent border-none text-gray-900 placeholder-gray-400 focus:outline-none"
              />
              <button
                type="submit"
                className="shrink-0 px-5 sm:px-7 py-3 rounded-full text-xs sm:text-sm font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] transition flex items-center gap-1.5 shadow-sm"
              >
                <span>Start Campaign</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
            <p className="text-xs text-gray-400 mt-3 font-normal">
              No Meta Ads Manager complexity &bull; Election Commission compliant disclaimers &bull; Human quality review
            </p>
          </div>
        </div>
      </section>

      {/* Interactive Ad Simulator */}
      <section id="simulator" className="py-20 md:py-24 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14 space-y-3">
            <h2 className="text-2xl sm:text-4xl font-black text-gray-950 tracking-tight">
              Test Drive Your Ward Ad Campaign
            </h2>
            <p className="text-sm text-gray-600">
              Customize your parameters on the left. The live simulator on the right computes real-time voter
              impressions and renders the exact feed format that local voters see.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left: Interactive Controls */}
            <div className="lg:col-span-7 bg-[#fafafa] p-6 sm:p-8 rounded-3xl border border-gray-200/80 shadow-sm space-y-6">
              <div className="flex items-center gap-2 border-b border-gray-200 pb-3">
                <Sliders className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
                  Interactive Campaign Parameters
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-1">Candidate Name</label>
                  <input
                    type="text"
                    value={simName}
                    onChange={(e) => setSimName(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-xl px-3.5 py-2.5 text-xs text-gray-900 focus:outline-none focus:border-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-1">WhatsApp / Contact</label>
                  <input
                    type="tel"
                    value={simPhone}
                    onChange={(e) => setSimPhone(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-xl px-3.5 py-2.5 text-xs text-gray-900 focus:outline-none focus:border-emerald-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-1">Contesting Post</label>
                  <select
                    value={simPost}
                    onChange={(e) => setSimPost(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-xl px-3.5 py-2.5 text-xs text-gray-900 focus:outline-none focus:border-emerald-600"
                  >
                    <option value="Ward Councillor / Corporator">Ward Councillor / Corporator</option>
                    <option value="Gram Pradhan / Sarpanch">Gram Pradhan / Sarpanch</option>
                    <option value="Block Pramukh">Block Pramukh</option>
                    <option value="Zila Panchayat Member">Zila Panchayat Member</option>
                    <option value="Nagar Palika President">Nagar Palika President</option>
                    <option value="MLA Candidate">MLA Candidate</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-800 mb-1">Ward / Village Area</label>
                  <input
                    type="text"
                    value={simArea}
                    onChange={(e) => setSimArea(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-xl px-3.5 py-2.5 text-xs text-gray-900 focus:outline-none focus:border-emerald-600"
                  />
                </div>
              </div>

              {/* Radius Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-gray-800">Hyper-Local Geofence Radius</span>
                  <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    {simRadius} km around polling booth
                  </span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="40"
                  value={simRadius}
                  onChange={(e) => setSimRadius(Number(e.target.value))}
                  className="w-full accent-emerald-600 h-2 bg-gray-200 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-gray-400">
                  <span>3 km (Single Ward)</span>
                  <span>15 km (Tehsil / Block)</span>
                  <span>40 km (Constituency)</span>
                </div>
              </div>

              {/* Symbol Picker */}
              <div>
                <label className="block text-xs font-bold text-gray-800 mb-1.5">
                  Assigned Election Symbol (चुनिए चुनाव चिन्ह)
                </label>
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                  {['Car', 'Kite', 'Bicycle', 'Hand Pump', 'Clock', 'Almirah'].map((sym) => (
                    <button
                      key={sym}
                      type="button"
                      onClick={() => setSimSymbol(sym)}
                      className={`p-2 rounded-xl text-xs font-semibold border text-center transition ${
                        simSymbol === sym
                          ? 'border-emerald-600 bg-emerald-50 text-emerald-800 font-bold shadow-sm'
                          : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {sym}
                    </button>
                  ))}
                </div>
              </div>

              {/* Budget Slider */}
              <div className="space-y-1.5 pt-2 border-t border-gray-200">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-gray-800">Daily Campaign Budget</span>
                  <span className="font-bold text-lg text-gray-950">₹{simBudget}/day</span>
                </div>
                <input
                  type="range"
                  min="200"
                  max="5000"
                  step="100"
                  value={simBudget}
                  onChange={(e) => setSimBudget(Number(e.target.value))}
                  className="w-full accent-emerald-600 h-2 bg-gray-200 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[11px] text-gray-500 font-medium">
                  <span>₹200 (Ward Micro)</span>
                  <span>₹1,500 (Medium)</span>
                  <span>₹5,000 (Maximum Saturation)</span>
                </div>
              </div>

              {/* Dynamic Reach KPI Banner */}
              <div className="bg-emerald-50 border border-emerald-200/80 rounded-2xl p-4 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                    Estimated Daily Voter Reach
                  </span>
                  <div className="text-xl font-black text-emerald-950">
                    {simReachMin.toLocaleString()} – {simReachMax.toLocaleString()} Local Voters
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-emerald-700 font-medium block">
                    Quality Guarantee
                  </span>
                  <span className="text-xs font-bold text-emerald-900 flex items-center gap-1 justify-end">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                    Human Review Included
                  </span>
                </div>
              </div>
            </div>

            {/* Right: Phone Live Feed Preview */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="w-[320px] sm:w-[350px] bg-gray-950 rounded-[44px] p-3 shadow-2xl border-[6px] border-gray-900 relative">
                {/* Speaker pill */}
                <div className="w-20 h-4 bg-gray-800 rounded-full mx-auto mb-2"></div>

                <div className="bg-white rounded-[34px] overflow-hidden text-gray-900 text-xs shadow-inner">
                  {/* Meta Feed Header */}
                  <div className="p-3.5 flex items-center justify-between border-b border-gray-100">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xs">
                        {simName.charAt(0) || 'P'}
                      </div>
                      <div>
                        <div className="font-bold text-xs leading-none">{simName}</div>
                        <div className="text-[9px] text-gray-400 mt-0.5">Sponsored &bull; Paid for by Campaign</div>
                      </div>
                    </div>
                    <span className="text-gray-400 font-bold">&bull;&bull;&bull;</span>
                  </div>

                  {/* Ad Post Copy */}
                  <div className="px-3.5 py-2 text-[11px] leading-relaxed text-gray-800 font-medium">
                    वार्ड के सच्चे विकास और जनता की आवाज के लिए आपके अपने उम्मीदवार {simName} को भारी मतों से विजयी बनाएं।
                  </div>

                  {/* Creative Poster Visual */}
                  <div className="bg-gradient-to-br from-emerald-900 to-slate-900 p-4 text-white relative min-h-[220px] flex flex-col justify-between">
                    <div className="flex justify-between items-start">
                      <span className="bg-amber-400 text-slate-950 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider">
                        {simPost}
                      </span>
                      <div className="bg-white/20 backdrop-blur-md px-2 py-0.5 rounded-full text-[10px] font-bold">
                        {simArea}
                      </div>
                    </div>

                    <div className="my-3 text-center space-y-1">
                      <div className="text-base font-black tracking-tight">{simName}</div>
                      <p className="text-[10px] text-gray-200">ईमानदार &bull; कर्मठ &bull; विकासशील</p>
                    </div>

                    <div className="bg-white/10 backdrop-blur-md p-2 rounded-xl border border-white/20 flex items-center justify-between">
                      <div className="text-left">
                        <span className="text-[8px] text-gray-300 block">चुनाव चिन्ह:</span>
                        <span className="text-xs font-bold text-amber-300">{simSymbol}</span>
                      </div>
                      <div className="text-right">
                        <span className="text-[8px] text-gray-300 block">लक्ष्य:</span>
                        <span className="text-xs font-bold text-white">सच्चा विकास</span>
                      </div>
                    </div>
                  </div>

                  {/* Meta Action Bar */}
                  <div className="p-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                    <div>
                      <div className="text-[9px] text-gray-500 uppercase tracking-wider">Hyperlocal Campaign</div>
                      <div className="text-[11px] font-bold text-gray-900">{simArea}</div>
                    </div>
                    <a
                      href={`https://wa.me/91${simPhone}`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm"
                    >
                      <PhoneCall className="w-3 h-3" />
                      Contact
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Chess Model Section */}
      <section id="chess-model" className="py-20 md:py-24 bg-[#fafafa] border-b border-gray-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              4-Tier Tactical Architecture
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-gray-950 tracking-tight">
              The PolitiAds Chess Model
            </h2>
            <p className="text-sm text-gray-600">
              Every political office requires a different strategic footprint. From hyper-localized 3km ward
              saturation to constituency-wide voter mobilization.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                tier: 'Pawn (पैदल)',
                office: 'Ward Councillor / Gram Pradhan',
                radius: '3 – 5 km Radius',
                budget: '₹200 – ₹500 / day',
                desc: 'Hyperlocal ward saturation. Reaches every household inside your polling boundary multiple times.',
                badge: 'Local Ward'
              },
              {
                tier: 'Knight (घोड़ा)',
                office: 'Block Pramukh / Zila Panchayat',
                radius: '8 – 15 km Radius',
                budget: '₹800 – ₹1,500 / day',
                desc: 'Tehsil-wide awareness campaigns with village cluster targeting and symbol identification.',
                badge: 'Tehsil / Block'
              },
              {
                tier: 'Bishop (ऊँट)',
                office: 'Vidhan Sabha (MLA)',
                radius: '20 – 35 km Radius',
                budget: '₹2,500 – ₹8,000 / day',
                desc: 'Assembly constituency blitz. Demographic segmentation across youth, farmers, and urban wards.',
                badge: 'Constituency'
              },
              {
                tier: 'Queen (रानी)',
                office: 'Lok Sabha (MP)',
                radius: '50 – 80 km Radius',
                budget: '₹10,000+ / day',
                desc: 'Full parliamentary sweep with parallel multi-candidate war rooms and real-time sentiment alerts.',
                badge: 'Parliament'
              }
            ].map((chess, idx) => (
              <div
                key={idx}
                className="bg-white p-6 rounded-3xl border border-gray-200/90 shadow-sm hover:shadow-md transition space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-900">{chess.tier}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {chess.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-gray-950 leading-snug">{chess.office}</h3>
                  <div className="text-xs font-semibold text-emerald-700">{chess.radius}</div>
                  <p className="text-xs text-gray-600 leading-relaxed">{chess.desc}</p>
                </div>
                <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                  <span className="text-gray-400">Budget Range:</span>
                  <span className="font-bold text-gray-900">{chess.budget}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 md:py-24 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
            <h2 className="text-3xl sm:text-4xl font-black text-gray-950 tracking-tight">
              Transparent Election Pricing
            </h2>
            <p className="text-sm text-gray-600">
              Zero hidden setup fees. Pay only for Meta direct voter impressions plus our quality review service.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {(livePlans.length > 0 ? livePlans : [
              {
                id: 'plan_panchayat',
                name: 'Gram Panchayat Starter',
                price: 999,
                badge: 'Popular',
                daily_ad_limit: 500,
                features: [
                  '3km Polling Booth Geofence',
                  'Symbol & Photo Integration',
                  'Hindi / Regional Slogan Polish',
                  'ECI Compliant Disclaimers',
                  'Direct WhatsApp Contact Button'
                ]
              },
              {
                id: 'plan_ward',
                name: 'Ward Councillor Pro',
                price: 2499,
                badge: 'Best Value',
                daily_ad_limit: 1500,
                features: [
                  '8km Multi-Ward Geofence',
                  'Meta Ad Library Opponent Spy',
                  'Daily Poster Creative Updates',
                  'Priority Copyrighting Polish',
                  'Live Impression Analytics Dashboard',
                  'WhatsApp Lead Forwarding'
                ]
              },
              {
                id: 'plan_mla',
                name: 'Vidhan Sabha MLA War-Room',
                price: 9999,
                badge: 'Elite',
                daily_ad_limit: 10000,
                features: [
                  'Entire Constituency (40km)',
                  '4-Tier Chess Counter-Attacks',
                  'Dedicated Campaign Manager',
                  'Ground Sentiment Reports',
                  'Unlimited Meta Push'
                ]
              }
            ]).map((plan, idx) => (
              <div
                key={idx}
                className={`p-7 rounded-3xl border flex flex-col justify-between transition ${
                  plan.featured
                    ? 'border-emerald-600 bg-white shadow-xl relative ring-2 ring-emerald-600/20'
                    : 'border-gray-200 bg-[#fafafa] shadow-sm'
                }`}
              >
                {plan.featured && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-600 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                    Most Popular
                  </span>
                )}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-950">{plan.name || plan.title}</h3>
                    {plan.badge && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                        {plan.badge}
                      </span>
                    )}
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-black text-gray-950">
                      ₹{typeof plan.price === 'number' ? plan.price.toLocaleString() : plan.price}
                    </span>
                    <span className="text-xs text-gray-500 font-medium">/ cycle</span>
                  </div>
                  <p className="text-xs text-emerald-700 font-medium">
                    Daily Ad Limit: ₹{(plan.daily_ad_limit || 500).toLocaleString()}/day
                  </p>
                  <ul className="space-y-2.5 pt-3 border-t border-gray-100 text-xs text-gray-700">
                    {plan.features.map((feat, fIdx) => (
                      <li key={fIdx} className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => {
                    if (onOpenAuth) onOpenAuth('signup');
                    else window.location.hash = '#/signup';
                  }}
                  className={`w-full mt-8 py-3.5 rounded-full text-xs font-bold transition shadow-sm ${
                    (plan.badge || '').toLowerCase().includes('popular') || (plan.badge || '').toLowerCase().includes('best')
                      ? 'bg-black hover:bg-neutral-800 text-white'
                      : 'bg-[#bbf7d0] hover:bg-[#86efac] text-gray-950'
                  }`}
                >
                  Choose {plan.name || plan.title || 'Plan'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 bg-[#fafafa] border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12 space-y-2">
            <h2 className="text-2xl sm:text-3xl font-black text-gray-950 tracking-tight">
              Frequently Asked Questions
            </h2>
            <p className="text-xs text-gray-600">
              Clear answers regarding local election ad guidelines and operations.
            </p>
          </div>

          <div className="space-y-4">
            {[
              {
                q: 'Do I need a separate Meta Business Manager account?',
                a: 'No. PolitiAds manages the technical Meta Marketing API connection through verified agency channels, saving candidates from account bans and verification delays.'
              },
              {
                q: 'How does PolitiAds ensure Election Commission (ECI) compliance?',
                a: 'Every ad creative automatically embeds the mandatory "Paid for by: [Candidate Name]" disclaimer required by Election Commission guidelines.'
              },
              {
                q: 'What happens after I submit an ad?',
                a: 'Our quality team checks regional spelling, verifies that your election symbol is clear and centered, sets the exact geofence, and pushes the ad live to Meta.'
              },
              {
                q: 'Can voters contact me directly from the ad?',
                a: 'Yes! Every ad includes your WhatsApp or direct phone button, enabling local ward voters to message or call your election office with one tap.'
              }
            ].map((faq, idx) => (
              <div key={idx} className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm space-y-1.5">
                <h4 className="text-sm font-bold text-gray-950">{faq.q}</h4>
                <p className="text-xs text-gray-600 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Clean Footer */}
      <footer className="py-12 bg-white border-t border-gray-200 text-gray-500 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-gray-100 pb-6">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gray-950 flex items-center justify-center">
                <Megaphone className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold text-gray-950 text-sm">PolitiAds</span>
              <span className="text-gray-400">&bull; politiads.maeaco.com</span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-6 text-gray-600">
              <a href="#simulator" className="hover:text-gray-950">Simulator</a>
              <a href="#chess-model" className="hover:text-gray-950">Chess Model</a>
              <a href="#pricing" className="hover:text-gray-950">Pricing</a>
              <a href="#faq" className="hover:text-gray-950">FAQ</a>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-[12px]">
            <div className="flex flex-wrap items-center justify-center gap-5 text-gray-600 font-medium">
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('privacy')}
                className="hover:text-emerald-700 hover:underline transition"
              >
                Privacy Policy
              </button>
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('terms')}
                className="hover:text-emerald-700 hover:underline transition"
              >
                Terms of Service
              </button>
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('refunds')}
                className="hover:text-emerald-700 hover:underline transition"
              >
                Refund Policy
              </button>
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('data-deletion')}
                className="hover:text-emerald-700 hover:underline transition"
              >
                User Data Deletion
              </button>
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('contact')}
                className="hover:text-emerald-700 hover:underline transition"
              >
                Contact &amp; Grievance
              </button>
            </div>
            <div className="text-gray-400 text-[11px] text-center sm:text-right">
              &copy; 2026 PolitiAds (politiads.maeaco.com) by Maeaco. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
