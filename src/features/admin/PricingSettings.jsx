import React, { useState, useEffect } from 'react';
import { reviewsApi } from '../../api/reviews';
import { BudgetBreakdown } from '../campaigns/AdContentEditor';

export default function PricingSettings() {
  const [policy, setPolicy] = useState(null);
  const [gross, setGross] = useState(200);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { reviewsApi.policy().then(setPolicy).catch(e => setError(e.message)); }, []);
  const save = async () => {
    setBusy(true); setError(''); setMessage('');
    try { setPolicy(await reviewsApi.savePolicy(policy)); setMessage('Policy saved for new quotes. Existing campaign agreements are unchanged.'); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const total = Math.round(Number(gross) * 100);
  const meta = policy?.mode === 'fixed_meta' ? Number(policy.meta_daily_paise) : total - Math.round(total * Number(policy?.commission_pct || 0) / 100);
  return <section className="max-w-3xl rounded-3xl bg-white border border-slate-200/80 p-6 space-y-5 text-slate-800 shadow-2xs font-sans">
    <h3 className="text-xl font-extrabold text-slate-900">Pricing & Margin Settings</h3>
    <p className="text-xs text-slate-500">Set the customer daily split. Allocation is a plan, not confirmed Meta spend or earned revenue.</p>
    {error && <p role="alert" className="text-rose-600 text-xs font-medium">{error}</p>}{message && <p role="status" className="text-emerald-600 text-xs font-medium">{message}</p>}
    {policy && <><label className="block text-xs font-semibold text-slate-700">Allocation mode<select aria-label="Allocation mode" value={policy.mode} onChange={e => setPolicy({ ...policy, mode: e.target.value })} className="block bg-slate-50 border border-slate-200 text-slate-900 p-3 rounded-xl w-full mt-1 text-xs focus:bg-white focus:outline-none focus:border-orange-500"><option value="percentage">Percentage company fee</option><option value="fixed_meta">Fixed Meta daily allocation</option></select></label>
      {policy.mode === 'percentage' ? <label className="block text-xs font-semibold text-slate-700">Company fee (%)<input aria-label="Company fee percentage" type="number" min="0" max="99.99" step="0.01" value={policy.commission_pct} onChange={e => setPolicy({ ...policy, commission_pct: Number(e.target.value) })} className="block bg-slate-50 border border-slate-200 text-slate-900 p-3 rounded-xl w-full mt-1 text-xs focus:bg-white focus:outline-none focus:border-orange-500" /></label> :
        <label className="block text-xs font-semibold text-slate-700">Meta daily allocation (₹)<input aria-label="Meta daily allocation" type="number" min="0.01" step="0.01" value={policy.meta_daily_paise / 100} onChange={e => setPolicy({ ...policy, meta_daily_paise: Math.round(Number(e.target.value) * 100) })} className="block bg-slate-50 border border-slate-200 text-slate-900 p-3 rounded-xl w-full mt-1 text-xs focus:bg-white focus:outline-none focus:border-orange-500" /></label>}
      <label className="block text-xs font-semibold text-slate-700">Preview customer daily total (₹)<input aria-label="Preview customer daily total" type="number" min="200" value={gross} onChange={e => setGross(e.target.value)} className="block bg-slate-50 border border-slate-200 text-slate-900 p-3 rounded-xl w-full mt-1 text-xs focus:bg-white focus:outline-none focus:border-orange-500" /></label>
      {meta > 0 && meta <= total ? <BudgetBreakdown quote={{ customer_daily_paise: total, meta_daily_paise: meta, company_fee_paise: total-meta }} /> : <p className="text-rose-600 text-xs font-medium">Meta allocation must be positive and no larger than the customer total.</p>}
      <button disabled={busy || !(meta > 0 && meta <= total)} onClick={save} className="rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white px-5 py-3 font-bold text-xs shadow-xs disabled:opacity-40">{busy ? 'Saving…' : 'Save Pricing Policy'}</button></>}
  </section>;
}
