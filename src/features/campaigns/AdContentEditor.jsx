import React, { useState } from 'react';
import { reviewsApi } from '../../api/reviews';

export function BudgetBreakdown({ quote }) {
  if (!quote) return <p className="text-sm">Budget breakdown unavailable. Refresh before submitting.</p>;
  const money = value => `₹${(value / 100).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  return <div className="rounded-xl border border-current/20 p-4 space-y-2 text-sm" aria-label="Budget breakdown">
    <div className="flex justify-between"><span>Customer daily total</span><strong>{money(quote.customer_daily_paise)}</strong></div>
    <div className="flex justify-between"><span>Meta daily allocation</span><strong>{money(quote.meta_daily_paise)}</strong></div>
    <div className="flex justify-between"><span>Company service fee</span><strong>{money(quote.company_fee_paise)}</strong></div>
    <p className="text-xs opacity-70">Planned allocation per day. Company fee is earned in proportion to verified final Meta spend; unused credit stays refundable. Provider budget requirements still apply.</p>
  </div>;
}

export function AdContentEditor({ value, onChange, dark = false, budgetReadOnly = false }) {
  const input = `w-full rounded-xl border px-3 py-2 text-sm ${dark ? 'bg-slate-950 border-slate-700 text-white' : 'bg-white border-gray-300 text-gray-950'}`;
  const fields = [['title', 'Campaign title'], ['area', 'Target area / ward'], ['pincode', 'Pincode'],
    ['whatsapp_phone', 'WhatsApp phone'], ['symbol', 'Election symbol'], ['radius_km', 'Radius (3–40 km)', 'number'],
    ['budget_daily', 'Customer daily total (₹)', 'number'], ['duration_days', 'Campaign duration (days)', 'number']];
  const set = (key, val) => onChange({ ...value, [key]: val });
  return <div className="space-y-4">
    <p className="text-xs opacity-70">{value.duration_days || 1} day(s) · Asia/Kolkata · Planned customer total: ₹{(Number(value.budget_daily || 0) * Number(value.duration_days || 1)).toLocaleString('en-IN')}. Funding is reserved daily; delivery requires provider confirmation.</p>
    <div className="grid sm:grid-cols-2 gap-3">{fields.map(([key, label, type]) => <label key={key} className="block text-xs space-y-1">
      <span>{label}</span><input aria-label={label} className={input} type={type || 'text'} value={value[key] ?? ''}
        readOnly={key === 'budget_daily' && budgetReadOnly}
        min={key === 'budget_daily' ? 200 : key === 'radius_km' ? 3 : key === 'duration_days' ? 1 : undefined}
        max={key === 'radius_km' ? 40 : key === 'duration_days' ? 365 : undefined} step={key === 'radius_km' ? 0.1 : key === 'duration_days' ? 1 : 0.01}
        onChange={e => set(key, type === 'number' ? Number(e.target.value) : e.target.value)} />
    </label>)}</div>
    <label className="block text-xs space-y-1"><span>Post content / caption</span>
      <textarea aria-label="Post content / caption" className={input} rows={5} value={value.slogan || ''} onChange={e => set('slogan', e.target.value)} /></label>
    <label className="block text-xs space-y-1"><span>Existing layout</span><select aria-label="Existing layout" className={input} value={value.template_id || 1} onChange={e => set('template_id', Number(e.target.value))}>
      {[1, 2, 3, 4].map(id => <option key={id} value={id}>Style {id}</option>)}</select></label>
    {value.photo_url && <div className="text-xs space-y-2"><span>Existing campaign image</span><img src={value.photo_url} alt="Existing campaign asset" className="max-h-40 rounded-xl object-contain" /></div>}
  </div>;
}

export function AdPreview({ content }) {
  return <div className="rounded-2xl bg-emerald-950 text-white p-5 space-y-3 break-words" aria-label="Ad preview">
    <p className="text-xs opacity-70">Content preview • Company and Meta review required</p>
    <h4 className="font-bold">{content.title}</h4><p className="whitespace-pre-wrap text-sm">{content.slogan}</p>
    <p className="text-xs opacity-70">{content.area} · {content.pincode} · {content.radius_km} km</p>
    <p className="text-xs">WhatsApp: {content.whatsapp_phone}</p>
  </div>;
}

export function ReviewHistory({ history = [], campaignId }) {
  const [older, setOlder] = useState([]);
  const [more, setMore] = useState(history.length === 10);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [media, setMedia] = useState({});
  const loadMedia = async version => {
    try { const response = await reviewsApi.revisionMedia(campaignId, version); setMedia(previous => ({ ...previous, [version]: response.photo_url })); }
    catch (e) { setError(e.message); }
  };
  const rows = [...history, ...older];
  const load = async () => {
    setBusy(true); setError('');
    try { const response = await reviewsApi.history(campaignId, rows.at(-1)?.version); setOlder(previous => [...previous, ...response.items]); setMore(Boolean(response.next_before_version)); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  return <details className="rounded-xl border border-current/20 p-3 text-sm"><summary className="cursor-pointer font-semibold">Review history ({rows.length} loaded)</summary>
    <div className="space-y-3 mt-3">{rows.map(row => <div key={row.version} className="border-t border-current/10 pt-2">
      <p>Version {row.version} · {row.action} · {new Date(row.created_at).toLocaleString()}</p>
      <p className="text-xs opacity-70">{row.note}</p><details><summary className="text-xs cursor-pointer">Saved content and pricing</summary>
        <p className="text-sm mt-2 whitespace-pre-wrap">{row.snapshot.slogan}</p><p className="text-xs">{row.snapshot.title} · {row.snapshot.area} · {row.snapshot.pincode} · {row.snapshot.radius_km} km · {row.snapshot.whatsapp_phone}</p>
        <BudgetBreakdown quote={row.snapshot.pricing_snapshot} /></details>
      {row.snapshot.has_image && campaignId && <button onClick={() => loadMedia(row.version)} className="text-xs underline">View Saved Image</button>}
      {media[row.version] && <img src={media[row.version]} alt={`Saved image for version ${row.version}`} className="max-h-48 rounded-xl object-contain" />}
    </div>)}</div>{error && <p role="alert">{error}</p>}{more && campaignId && <button onClick={load} disabled={busy} className="mt-3 underline">{busy ? 'Loading…' : 'Load Older Versions'}</button>}</details>;
}

export function FundingDays({ days = [] }) {
  return <details className="border border-current/20 rounded-xl p-3 text-sm"><summary className="cursor-pointer font-bold">Daily funding & settlement</summary>
    <p className="text-xs my-2">Timezone: Asia/Kolkata. Fees are earned in proportion to verified final Meta spend. Unknown delivery keeps funds reserved.</p>
    <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr>{['Date', 'Version', 'Status', 'Meta allocated', 'Actual Meta spend', 'Earned fee'].map(label => <th key={label} className="p-2 text-left">{label}</th>)}</tr></thead>
      <tbody>{days.map(day => <tr key={day.id}>{[day.billing_date, day.version, day.status, `₹${day.meta_paise/100}`, day.status==='settled' ? `₹${day.actual_spend_paise/100}` : 'Not reconciled', day.status==='settled' ? `₹${day.earned_fee_paise/100}` : 'Not recognized'].map((value, i) => <td key={i} className="p-2 border-t border-current/10">{value}</td>)}</tr>)}</tbody></table></div>
    {!days.length && <p className="text-xs">No approved funding days yet.</p>}</details>;
}
