import React, { useState, useEffect } from 'react';
import { reviewsApi } from '../../api/reviews';
import { checkout } from '../../api/checkout';
import { AdContentEditor, AdPreview, BudgetBreakdown, ReviewHistory, FundingDays } from './AdContentEditor';

function Editor({ detail, onSaved, onClose }) {
  const [content, setContent] = useState(detail.content);
  const [quote, setQuote] = useState(detail.content.pricing_snapshot);
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [days, setDays] = useState(1);
  const [message, setMessage] = useState('');
  const editable = !['Processing', 'Submitted', 'Reconciliation Required'].includes(detail.publishing_job_status) && detail.delivery_status !== 'Delivering';
  useEffect(() => {
    let active = true;
    if (content.budget_daily === detail.content.budget_daily && detail.content.pricing_snapshot) return undefined;
    reviewsApi.quote(content.budget_daily).then(q => { if (active) setQuote(q); }).catch(e => { if (active) { setQuote(null); setError(e.message); } });
    return () => { active = false; };
  }, [content.budget_daily, detail.content.budget_daily, detail.content.pricing_snapshot]);
  const update = next => {
    if (next.duration_days !== content.duration_days) setAccepted(false);
    if (next.budget_daily !== content.budget_daily) { setAccepted(false); setQuote(next.budget_daily === detail.content.budget_daily ? detail.content.pricing_snapshot : null); }
    setContent(next);
  };
  const submit = async draft => {
    setBusy(true); setError('');
    try { const result = await reviewsApi.revise(detail.id, { ...content, expected_version: detail.version, save_as_draft: draft, accepted_pricing: accepted ? quote : null }); await onSaved(result); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const pay = async () => {
    setBusy(true); setError('');
    try { await checkout('campaign_budget', detail.id, Math.round(detail.content.budget_daily * 100) * Number(days)); setMessage('Payment verified. Company approval and Meta confirmation are separate.'); await onSaved(); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  return <div className="space-y-5"><div className="flex justify-between"><h3 className="text-xl font-bold">Ad details & review</h3><button aria-label="Close" onClick={onClose} disabled={busy}>✕</button></div>
    <p className="text-sm">Version {detail.version} · {detail.company_review_status}</p>
    <p className="text-xs text-gray-500">Publishing: {detail.publishing_job_status} · Meta: {detail.provider_review_status} · Delivery: {detail.delivery_status}</p>
    {error && <p role="alert" className="text-red-700 text-sm">{error}</p>}{message && <p role="status" className="text-emerald-700 text-sm">{message}</p>}
    {!editable && <p className="text-amber-800 text-sm">Provider submission is recorded or in progress. Provider pause/cancellation must be confirmed before editing.</p>}
    <div className="grid md:grid-cols-2 gap-5"><div>{editable ? <AdContentEditor value={content} onChange={update} /> : <AdPreview content={content} />}</div>
      <div className="space-y-4"><AdPreview content={content} /><BudgetBreakdown quote={quote} />
        {editable && <label className="flex gap-2 text-sm"><input type="checkbox" checked={accepted} disabled={!quote} onChange={e => setAccepted(e.target.checked)} />I accept this budget breakdown for resubmission.</label>}
        <p className="text-sm">Available verified funds: ₹{detail.funds.available_paise / 100} · Reserved: ₹{detail.funds.reserved_paise / 100} · Consumed: ₹{(detail.funds.consumed_paise || 0) / 100}</p>
        {!['Draft', 'Rejected', 'Changes Requested'].includes(detail.company_review_status) && <div className="border rounded-xl p-3 space-y-2"><label className="text-sm">Fund campaign days<input aria-label="Fund campaign days" type="number" min="1" max="365" step="1" value={days} onChange={e => setDays(e.target.value)} className="border rounded-lg px-2 py-1 w-20 ml-2" /></label>
          <p className="text-xs">Funding uses the saved campaign pricing above; save content edits separately. No automatic recurring debit.</p>
          <button disabled={busy || !Number.isInteger(Number(days)) || Number(days) < 1 || Number(days) > 365} onClick={pay} className="bg-emerald-700 text-white rounded-xl px-4 py-2 disabled:opacity-40">Pay ₹{(detail.content.budget_daily * Number(days)).toLocaleString('en-IN')}</button></div>}
      </div></div>
    <ReviewHistory history={detail.history} campaignId={detail.id} />
    <FundingDays days={detail.funding_days} />
    {editable && <div className="flex gap-3 justify-end"><button onClick={() => submit(true)} disabled={busy} className="border rounded-xl px-4 py-2">Save Draft</button><button disabled={busy || !accepted || !quote} onClick={() => submit(false)} className="bg-emerald-700 text-white rounded-xl px-4 py-2 disabled:opacity-40">Update & Submit for Review</button></div>}
  </div>;
}

export default function CampaignDetails({ campaignId, onClose, onUpdated }) {
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { let active = true; reviewsApi.detail(campaignId).then(d => { if (active) setDetail(d); }).catch(e => { if (active) setError(e.message); }); return () => { active = false; }; }, [campaignId]);
  const saved = async result => { setDetail(result || await reviewsApi.detail(campaignId)); await onUpdated(); };
  return <div className="fixed inset-0 z-50 bg-black/60 p-4 overflow-y-auto flex justify-center items-start" role="dialog" aria-modal="true" aria-label="Ad details">
    <div className="bg-white text-gray-950 rounded-3xl p-6 w-full max-w-5xl my-5">{error ? <><p role="alert">{error}</p><button onClick={onClose}>Close</button></> : detail ? <Editor key={`${detail.id}:${detail.version}`} detail={detail} onSaved={saved} onClose={onClose} /> : <p>Loading ad…</p>}</div></div>;
}
