import React, { useState, useEffect, useCallback } from 'react';
import { LayoutDashboard, RefreshCw, Share2, CheckCircle2 } from 'lucide-react';
import LocationPicker from '../../components/location/LocationPicker';
import ImageUploader from '../../components/uploads/ImageUploader';
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

export default function OnboardingWizard({
  initialProfile,
  onSaveProfile,
  onComplete,
  isSaving = false
}) {
  const [step, setStep] = useState(1);
  const [metaModalOpen, setMetaModalOpen] = useState(false);
  const [metaStatus, setMetaStatus] = useState(null);

  const fetchMetaStatus = useCallback(async () => {
    try {
      const res = await integrationsApi.getMetaStatus();
      setMetaStatus(res);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(fetchMetaStatus);
  }, [fetchMetaStatus]);

  // Form state
  const [name, setName] = useState(initialProfile?.candidate_name || '');
  const [post, setPost] = useState(initialProfile?.contesting_post || 'Ward Councillor / Corporator');
  const [ward, setWard] = useState(initialProfile?.gaon_ward || 'Rampur, Ward No. 12');
  const [area, setArea] = useState(initialProfile?.area_block || 'Sadabad Block, Hathras');
  const [pincode, setPincode] = useState(initialProfile?.pincode || '281306');
  const [photo, setPhoto] = useState(initialProfile?.photo_url || null);
  const [gpsLocation, setGpsLocation] = useState({
    lat: initialProfile?.lat || '27.4482',
    lng: initialProfile?.lng || '78.0416',
    accuracy: initialProfile?.accuracy_m || 25
  });
  const [symbol, setSymbol] = useState(initialProfile?.symbol_name || 'Car');
  const [customSymbol, setCustomSymbol] = useState(initialProfile?.custom_symbol_url || null);
  const [disclaimer, setDisclaimer] = useState(
    initialProfile?.disclaimer_text || `Paid for by: ${name || 'Candidate'} Campaign`
  );
  const [validationError, setValidationError] = useState('');

  const handleStep1Submit = async () => {
    if (!name.trim()) {
      setValidationError('Please enter candidate name.');
      return;
    }
    if (!ward.trim()) {
      setValidationError('Please enter Gaon or Ward name.');
      return;
    }
    if (!pincode.trim() || pincode.length !== 6) {
      setValidationError('Please enter a valid 6-digit postal pincode.');
      return;
    }
    setValidationError('');

    try {
    await onSaveProfile({
      candidate_name: name.trim(),
      contesting_post: post,
      gaon_ward: ward.trim(),
      area_block: area.trim(),
      pincode: pincode.trim(),
      lat: gpsLocation.lat,
      lng: gpsLocation.lng,
      accuracy_m: gpsLocation.accuracy,
      symbol_name: symbol,
      custom_symbol_url: customSymbol,
      photo_url: photo,
      disclaimer_text: disclaimer
    });

    setStep(2);
    } catch (error) { setValidationError(error.message); }
  };

  const handleStep3Submit = async () => {
    try {
    await onSaveProfile({
      onboarding_completed: true,
      candidate_name: name.trim(),
      contesting_post: post,
      gaon_ward: ward.trim(),
      area_block: area.trim(),
      pincode: pincode.trim(),
      lat: gpsLocation.lat,
      lng: gpsLocation.lng,
      accuracy_m: gpsLocation.accuracy,
      symbol_name: symbol,
      custom_symbol_url: customSymbol,
      photo_url: photo,
      disclaimer_text: disclaimer
    });
    setStep(4);
    } catch (error) { setValidationError(error.message); }
  };

  return (
    <div className="min-h-screen bg-[#fafafa] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Progress Header */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-gray-200/80 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Step {step} of 4
            </span>
            <h2 className="text-2xl font-bold text-gray-950 mt-1">Candidate Campaign Setup</h2>
          </div>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`h-2 rounded-full transition-all ${
                  step === s ? 'w-8 bg-emerald-600' : step > s ? 'w-8 bg-emerald-300' : 'w-5 bg-gray-200'
                }`}
              />
            ))}
          </div>
        </div>

        {/* STEP 1: Profile & Geolocation */}
        {step === 1 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 bg-white rounded-3xl p-6 sm:p-8 border border-gray-200/80 shadow-sm space-y-5">
              <h3 className="text-lg font-bold text-gray-950">1. Candidate Information & Target Ward</h3>

              {validationError && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 font-semibold">
                  {validationError}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">Candidate Full Name*</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      setDisclaimer(`Paid for by: ${e.target.value} Campaign`);
                    }}
                    placeholder="e.g. Rajesh Kumar Sharma"
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">Contesting Post*</label>
                  <select
                    value={post}
                    onChange={(e) => setPost(e.target.value)}
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm font-medium"
                  >
                    {CONTESTING_POSTS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">Gaon / Ward*</label>
                  <input
                    type="text"
                    value={ward}
                    onChange={(e) => setWard(e.target.value)}
                    placeholder="e.g. Rampur, Ward No. 12"
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">Area / Block*</label>
                  <input
                    type="text"
                    value={area}
                    onChange={(e) => setArea(e.target.value)}
                    placeholder="e.g. Sadabad Block, Hathras"
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-800 mb-1">6-digit Postal PIN Code*</label>
                  <input
                    type="text"
                    maxLength={6}
                    value={pincode}
                    onChange={(e) => setPincode(e.target.value.replace(/\D/g, ''))}
                    placeholder="281306"
                    className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm font-mono"
                  />
                </div>
                <div>
                  <LocationPicker
                    location={gpsLocation}
                    onChange={(coords) => setGpsLocation(coords)}
                    label="Constituency GPS Location"
                  />
                </div>
              </div>

              {/* Photo & Symbol */}
              <div className="pt-2 border-t border-gray-100">
                <ImageUploader
                  value={photo}
                  onChange={(dataUrl) => setPhoto(dataUrl)}
                  label="Candidate Display Photo (Square format recommended)"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-800 mb-2">Election Symbol*</label>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                  {DEFAULT_SYMBOLS.map((s) => (
                    <button
                      key={s.name}
                      type="button"
                      onClick={() => { setSymbol(s.name); setCustomSymbol(null); }}
                      className={`p-2.5 rounded-xl border text-center transition ${
                        symbol === s.name && !customSymbol
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

              <button
                type="button"
                disabled={isSaving}
                onClick={handleStep1Submit}
                className="w-full py-4 rounded-full font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] disabled:opacity-50 transition shadow-md text-sm flex items-center justify-center gap-2 mt-4"
              >
                {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
                {isSaving ? 'Saving Profile...' : 'Save Profile & Continue to Meta Setup →'}
              </button>
            </div>

            {/* Step 1 Live Preview Card */}
            <div className="lg:col-span-4 bg-white rounded-3xl p-6 border border-gray-200/80 shadow-sm space-y-4 h-fit">
              <h4 className="font-bold text-gray-950 text-sm">Draft Voter Card</h4>
              <div className="p-4 rounded-2xl bg-[#fafafa] border border-gray-200 space-y-3">
                <div className="w-20 h-20 rounded-2xl bg-gray-200 border border-gray-300 overflow-hidden mx-auto flex items-center justify-center">
                  {photo ? (
                    <img src={photo} alt="Candidate" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-xs text-gray-400">Photo</span>
                  )}
                </div>
                <div className="text-center">
                  <h5 className="font-bold text-gray-900 text-sm">{name || 'Candidate Name'}</h5>
                  <p className="text-xs text-emerald-700 font-semibold">{post}</p>
                  <p className="text-[11px] text-gray-500">{ward}</p>
                </div>
                <div className="pt-2 border-t border-gray-200 text-center">
                  <span className="text-xs font-bold text-gray-800 bg-white px-3 py-1 rounded-full border border-gray-200 inline-block shadow-sm">
                    Symbol: {symbol}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {validationError && step !== 1 && <p role="alert" className="text-red-700">{validationError}</p>}
        {/* STEP 2: Meta Managed Connection */}
        {step === 2 && (
          <div className="max-w-2xl mx-auto bg-white p-8 rounded-3xl border border-gray-200/80 shadow-sm space-y-6">
            <h3 className="text-xl font-bold text-gray-950">Step 2: Meta Ad Network Publishing</h3>
            <div className="p-5 rounded-2xl bg-[#fafafa] border border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-pink-500 text-white flex items-center justify-center font-bold shadow-xs">
                  <Share2 className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-gray-950">Facebook &amp; Instagram Ad Network</h4>
                  <p className="text-xs text-gray-500">
                    {metaStatus?.is_connected
                      ? `Linked: ${metaStatus.page_name} (Page ID: ${metaStatus.page_id})`
                      : 'Connect your official campaign page to enable automated ad publishing.'}
                  </p>
                </div>
              </div>
              <div>
                {metaStatus?.is_connected ? (
                  <span className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 flex items-center gap-1.5 shrink-0">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Connected
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => setMetaModalOpen(true)}
                    className="px-4 py-2 rounded-full text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs flex items-center gap-1.5 shrink-0"
                  >
                    <Share2 className="w-3.5 h-3.5" />
                    Connect Meta
                  </button>
                )}
              </div>
            </div>

            {metaStatus?.is_connected && (
              <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-100 text-xs text-blue-900 flex items-center justify-between">
                <span>Verified Meta Page: <strong>{metaStatus.page_name}</strong></span>
                <button
                  type="button"
                  onClick={() => setMetaModalOpen(true)}
                  className="text-xs font-bold text-blue-700 underline"
                >
                  Change Page
                </button>
              </div>
            )}

            <p className="text-xs text-gray-500">
              You can connect now or skip to connect later from your Candidate Dashboard settings.
            </p>
            <div className="flex justify-between pt-2">
              <button onClick={() => setStep(1)} className="text-xs font-semibold text-gray-600 hover:text-gray-950">
                ← Back to Profile
              </button>
              <button onClick={() => setStep(3)} className="px-8 py-3.5 rounded-full font-bold text-xs bg-[#bbf7d0] hover:bg-[#86efac] text-gray-950">
                Continue to Legal Disclaimer →
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Legal Disclaimer */}
        {step === 3 && (
          <div className="max-w-2xl mx-auto bg-white p-8 rounded-3xl border border-gray-200/80 shadow-sm space-y-6">
            <h3 className="text-xl font-bold text-gray-950">Step 3: ECI Compliance & Political Disclaimer</h3>
            <p className="text-xs text-gray-500">
              The Election Commission of India and Meta require all political advertisements to display an official "Paid for by" sponsor attribution.
            </p>
            <div>
              <label className="block text-xs font-semibold text-gray-800 mb-1.5">"Paid for by" Sponsor Text*</label>
              <input
                type="text"
                value={disclaimer}
                onChange={(e) => setDisclaimer(e.target.value)}
                className="w-full bg-[#fafafa] border border-gray-300 rounded-xl px-4 py-2.5 text-sm font-semibold"
              />
            </div>
            <div className="flex justify-between pt-2">
              <button onClick={() => setStep(2)} className="text-xs font-semibold text-gray-600 hover:text-gray-950">
                ← Back
              </button>
              <button
                disabled={isSaving}
                onClick={handleStep3Submit}
                className="px-8 py-3.5 rounded-full font-bold text-xs bg-[#bbf7d0] hover:bg-[#86efac] disabled:opacity-50 text-gray-950 flex items-center gap-1.5"
              >
                {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                Complete Onboarding →
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: Ready */}
        {step === 4 && (
          <div className="max-w-2xl mx-auto bg-white p-8 sm:p-10 rounded-3xl border border-gray-200/80 shadow-sm text-center space-y-6">
            <div className="w-16 h-16 rounded-3xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-3xl shadow-sm">
              🎉
            </div>
            <h3 className="text-2xl font-black text-gray-950">Onboarding Complete!</h3>
            <p className="text-xs text-gray-500 max-w-md mx-auto">
              Your profile has been saved. Draft submission does not confirm provider authorization or publication.
            </p>
            <button
              onClick={onComplete}
              className="px-10 py-4 rounded-full font-bold text-gray-950 bg-[#bbf7d0] hover:bg-[#86efac] transition shadow-md text-sm flex items-center justify-center gap-2 mx-auto"
            >
              <LayoutDashboard className="w-4 h-4" />
              Enter Candidate Dashboard Now
            </button>
          </div>
        )}

        {metaModalOpen && <MetaConnectModal
          isOpen={metaModalOpen}
          onClose={() => setMetaModalOpen(false)}
          onConnected={() => {
            fetchMetaStatus();
            setMetaModalOpen(false);
          }}
          initialPage={metaStatus?.is_connected ? { id: metaStatus.page_id, name: metaStatus.page_name } : null}
        />}
      </div>
    </div>
  );
}
