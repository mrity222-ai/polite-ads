import React, { useState, useEffect, useCallback } from 'react';
import { reviewsApi } from '../../api/reviews';
import { AdContentEditor, AdPreview, BudgetBreakdown, ReviewHistory, FundingDays } from '../campaigns/AdContentEditor';

function ReviewCard({ item, onSaved }) {
  const [content, setContent] = useState(item.content);
  const [note, setNote] = useState('');
  const [meta, setMeta] = useState((item.content.pricing_snapshot?.meta_daily_paise || 0) / 100);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const original = item.original_submission || item.history.at(-1)?.snapshot || item.content;
  const editable = ['Pending', 'Changes Requested'].includes(item.company_review_status);
  const releasable = item.company_review_status === 'Approved' && !['Processing', 'Submitted', 'Reconciliation Required'].includes(item.publishing_job_status);
  const changedAllocation = Math.round(Number(meta) * 100) !== item.content.pricing_snapshot?.meta_daily_paise;
  const decide = async action => {
    setBusy(true); setError(''); setMessage('');
    try {
      const operation = action === 'release' ? reviewsApi.release : reviewsApi.decide;
      const result = await operation(item.id, { expected_version: item.version, action: action === 'release' ? 'changes' : action, content, note,
        meta_daily_paise: changedAllocation ? Math.round(Number(meta) * 100) : null });
      onSaved(result);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  return <section className="rounded-3xl bg-white border border-slate-200/80 p-6 space-y-5 shadow-2xs">
    <div>
      <h4 className="font-extrabold text-slate-900 text-base">{item.candidate_name} · {item.content.title}</h4>
      <p className="text-xs text-slate-400 mt-0.5">{item.id} · Version {item.version} · <span className="font-semibold text-orange-600">{item.company_review_status}</span></p>
      <p className="text-xs text-slate-500">Publishing: {item.publishing_job_status} · Provider: {item.provider_review_status} · Delivery: {item.delivery_status}</p>
    </div>
    {error && <p role="alert" className="text-rose-600 text-sm font-medium">{error}</p>}
    {message && <p role="status" className="text-emerald-600 text-sm font-medium">{message}</p>}
    <div className="grid lg:grid-cols-2 gap-5"><div className="space-y-4">
      <div className="rounded-xl border border-orange-200/80 bg-orange-50/50 p-4">
        <h5 className="text-xs font-bold text-orange-700 mb-2">Original candidate submission</h5>
        <p className="text-sm whitespace-pre-wrap text-slate-800 font-medium">{original.slogan}</p>
      </div>
      {editable && <AdContentEditor value={content} onChange={setContent} budgetReadOnly />}
    </div><div className="space-y-4"><AdPreview content={content} /><BudgetBreakdown quote={item.content.pricing_snapshot} />
      <p className="text-xs text-slate-600 font-medium">Verified available funds: <strong className="text-slate-900">₹{item.funds.available_paise / 100}</strong> · Reserved: <strong className="text-orange-600">₹{item.funds.reserved_paise / 100}</strong></p>
      {editable && <><label className="block text-xs space-y-1 text-slate-700 font-semibold"><span>Proposed Meta daily allocation (₹)</span><input aria-label="Proposed Meta daily allocation" type="number" min="0.01" step="0.01" value={meta} onChange={e => setMeta(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:bg-white focus:outline-none focus:border-orange-500" /></label>
        {changedAllocation && <p className="text-orange-800 text-xs bg-orange-50 border border-orange-200/80 rounded-xl p-2.5 font-medium">Saving this allocation requests candidate consent. Approval stays blocked until resubmission. Proposed company fee: ₹{(Number(content.budget_daily) - Number(meta)).toFixed(2)}.</p>}
        <label className="block text-xs space-y-1 text-slate-700 font-semibold"><span>Review note / reason</span><textarea aria-label="Review note / reason" rows={3} value={note} onChange={e => setNote(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:bg-white focus:outline-none focus:border-orange-500" /></label></>}
    </div></div>
    <ReviewHistory history={item.history} campaignId={item.id} />
    <FundingDays days={item.funding_days} />
    <p className="text-xs">Approved targeting: {item.publishing_context?.lat}, {item.publishing_context?.lng} · Page: {item.publishing_context?.page_id || "Connection required"} · Disclaimer: {item.publishing_context?.disclaimer || "Not provided"}</p>
    {releasable && <div className="space-y-2"><label className="text-xs block text-slate-700 font-semibold">Reason for returning campaign<textarea aria-label="Reason for returning campaign" value={note} onChange={e => setNote(e.target.value)} className="block w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:bg-white focus:outline-none focus:border-orange-500" /></label>
      <button disabled={busy || !note.trim()} onClick={() => decide('release')} className="bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200 px-4 py-2 rounded-xl text-xs font-semibold disabled:opacity-40">Return for Changes & Release Reserved Funds</button><p className="text-xs text-slate-500">Available credit can then be refunded through the verified refund process. This does not issue a gateway refund.</p></div>}
    {editable && <div className="flex flex-wrap gap-2.5">{[['save', 'Save Changes'], ['changes', 'Request Changes'], ['reject', 'Reject'], ['approve', 'Approve & Queue']].map(([action, label]) =>
      <button key={action} disabled={busy || (action === 'approve' && (changedAllocation || item.company_review_status !== 'Pending'))} onClick={() => decide(action)}
        className={`px-4 py-2 rounded-xl text-xs font-bold transition disabled:opacity-40 ${
          action === 'approve' 
            ? 'bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shadow-xs' 
            : action === 'reject'
            ? 'bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200'
            : action === 'changes'
            ? 'bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200'
        }`}>{busy ? 'Saving…' : label}</button>)}</div>}
  </section>;
}

function ReviewItem({ summary, first, onSaved }) {
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(first);
  useEffect(() => {
    if (!open) return undefined;
    let active = true;
    reviewsApi.detail(summary.id).then(data => { if (active) setDetail(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [open, summary.id, summary.version]);
  return <div className="space-y-3"><button onClick={() => setOpen(value => !value)} className="w-full border border-current/20 rounded-xl p-3 text-left text-sm">
    {summary.candidate_name} · {summary.title} · v{summary.version} · {summary.company_review_status} · ₹{summary.budget_daily}/day — {open ? 'Close Review' : 'Open Review'}</button>
    {error && <p role="alert">{error}</p>}{open && (detail ? <ReviewCard key={`${detail.id}:${detail.version}`} item={detail} onSaved={onSaved} /> : <p>Loading selected ad…</p>)}</div>;
}

export default function AdReviewStudio() {
  const [state, setState] = useState('Pending');
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { const response = await reviewsApi.queue(state, page, search); setItems(response.items); setTotal(response.total); setHasMore(response.has_more); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }, [state, page, search]);
  useEffect(() => { void Promise.resolve().then(load); }, [load]);
  const saved = async item => { setMessage(`Ad ${item.id}: ${item.company_review_status}. ${item.job_id ? 'Queued; Meta confirmation pending.' : 'No provider submission made.'}`); await load(); };
  return <div className="max-w-6xl space-y-5 text-slate-800 font-sans"><h3 className="font-extrabold text-xl text-slate-900">Ad Review Studio</h3>
    <p className="text-xs text-slate-500">Review each post and approve its final version. Only the selected ad loads full content and paginated history.</p>
    <div className="flex flex-wrap gap-3"><select aria-label="Review filter" className="border rounded-xl p-2 bg-white" value={state} onChange={e => { setState(e.target.value); setPage(1); }}>{['Pending', 'Changes Requested', 'Approved', 'Rejected', 'All'].map(s => <option key={s}>{s}</option>)}</select>
      <form onSubmit={e => { e.preventDefault(); setSearch(searchInput); setPage(1); }} className="flex gap-2"><input aria-label="Search reviews" value={searchInput} onChange={e => setSearchInput(e.target.value)} placeholder="Candidate, title or ad ID" className="border rounded-xl p-2 text-sm" /><button className="border rounded-xl px-3">Search</button></form>
      <button onClick={load} disabled={loading}>Refresh Queue</button></div>
    {error && <p role="alert" className="text-rose-600">{error}</p>}{message && <p role="status" className="text-emerald-600">{message}</p>}
    {loading ? <p>Loading reviews…</p> : items.length ? items.map((item, index) => <ReviewItem key={`${item.id}:${item.version}`} summary={item} first={index===0} onSaved={saved} />) : <p>No ads in this review filter.</p>}
    <div className="flex items-center gap-4 text-sm"><button disabled={loading || page<=1} onClick={() => setPage(value => value-1)} className="border rounded-xl px-3 py-2 disabled:opacity-40">Previous</button><span>Page {page} · {total} ads</span><button disabled={loading || !hasMore} onClick={() => setPage(value => value+1)} className="border rounded-xl px-3 py-2 disabled:opacity-40">Next</button></div>
  </div>;
}
