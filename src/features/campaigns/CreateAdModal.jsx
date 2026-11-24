import React, { useState, useEffect } from 'react';
import { reviewsApi } from '../../api/reviews';
import { AdContentEditor, BudgetBreakdown, AdPreview } from './AdContentEditor';

export default function CreateAdModal({ isOpen, onClose, onSubmit, candidateProfile, isSubmitting = false }) {
  const [content, setContent] = useState({ title: `${candidateProfile?.gaon_ward || 'Ward'} Campaign`,
    whatsapp_phone: candidateProfile?.mobile || '', slogan: candidateProfile?.default_slogan || '',
    area: candidateProfile?.gaon_ward || '', pincode: candidateProfile?.pincode || '', radius_km: 8,
    budget_daily: 500, duration_days: 1, billing_timezone: 'Asia/Kolkata', template_id: 1, symbol: candidateProfile?.symbol_name || 'Car', photo_url: candidateProfile?.photo_url || null });
  const [quote, setQuote] = useState(null);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    reviewsApi.quote(content.budget_daily).then(data => { if (active) { setQuote(data); setError(''); } }).catch(e => { if (active) { setQuote(null); setError(e.message); } });
    return () => { active = false; };
  }, [content.budget_daily]);
  const update = next => { setContent(next); if (next.duration_days !== content.duration_days) setAccepted(false); if (next.budget_daily !== content.budget_daily) { setAccepted(false); setQuote(null); } };
  const submit = async draft => {
    setError('');
    try { await onSubmit({ ...content, save_as_draft: draft, accepted_pricing: accepted ? quote : null }); }
    catch (e) {
      setError(e.message);
      if (e.status === 409) {
        setAccepted(false);
        try { setQuote(await reviewsApi.quote(content.budget_daily)); }
        catch (refreshError) { setQuote(null); setError(refreshError.message); }
      }
    }
  };
  if (!isOpen) return null;
  return <div className="fixed inset-0 z-50 bg-black/60 overflow-y-auto p-4 flex items-start justify-center" role="dialog" aria-modal="true" aria-label="Create ad">
    <div className="bg-white text-gray-950 rounded-3xl p-6 w-full max-w-4xl my-6 space-y-5">
      <div className="flex justify-between"><h3 className="font-bold text-xl">Create ad draft</h3><button onClick={onClose} disabled={isSubmitting} aria-label="Close">✕</button></div>
      <p className="text-sm text-gray-600">Submit to our team first. Meta submission requires company approval and verified funds.</p>
      {error && <p role="alert" className="text-red-700 text-sm">{error}</p>}
      <div className="grid md:grid-cols-2 gap-6"><AdContentEditor value={content} onChange={update} /><div className="space-y-4"><AdPreview content={content} /><BudgetBreakdown quote={quote} />
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={accepted} disabled={!quote} onChange={e => setAccepted(e.target.checked)} />I accept this customer total, Meta allocation and company fee.</label></div></div>
      <div className="flex justify-end gap-3"><button className="border rounded-xl px-4 py-2" disabled={isSubmitting} onClick={() => submit(true)}>Save Draft</button>
        <button className="bg-emerald-700 text-white rounded-xl px-4 py-2 disabled:opacity-40" disabled={isSubmitting || !accepted || !quote} onClick={() => submit(false)}>{isSubmitting ? 'Saving…' : 'Submit for Review'}</button></div>
    </div></div>;
}
