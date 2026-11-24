import React, { useState } from 'react';
import { integrationsApi } from '../../api/integrations';

export default function RefundControl({ transaction, onUpdated }) {
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [operation, setOperation] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [reconcile, setReconcile] = useState(false);
  const refund = async () => {
    if (!window.confirm(`Request ₹${amount} refund for this payment? Campaign-reserved funds are excluded.`)) return;
    setBusy(true); setMessage('');
    const id = operation || crypto.randomUUID();
    setOperation(id);
    try {
      const result = await integrationsApi.processRefund(transaction.id, Number(amount), reason, id);
      const pending = result.status_label === 'pending';
      setReconcile(pending); setMessage(pending ? 'Pending provider reconciliation. Keep this operation reference; do not submit a new refund.' : `Refund status: ${result.status_label}.`);
      if (!pending) { setOperation(null); setAmount(''); }
      await onUpdated();
    } catch (e) { setMessage(e.message); setReconcile(true); await onUpdated(); }
    finally { setBusy(false); }
  };
  return <details className="text-xs min-w-44 font-sans"><summary className="cursor-pointer text-orange-600 font-bold hover:underline">Refund available credit</summary>
    <div className="space-y-2 mt-2 p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700">
      <p className="text-[11px] text-slate-600">Available: <strong className="text-slate-900">₹{transaction.refundable_paise / 100}</strong> · Reserved: <strong className="text-orange-600">₹{transaction.reserved_paise / 100}</strong> · Refund reserved: <strong>₹{transaction.refund_reserved_paise / 100}</strong></p>
      {transaction.gateway_mock ? <p className="text-slate-400 text-[10px]">Gateway simulation. Use verified provider payments for real refunds.</p> : <>
        <input aria-label={`Refund amount ${transaction.id}`} type="number" min="0.01" step="0.01" max={transaction.refundable_paise / 100} value={amount} disabled={busy || reconcile} onChange={e => setAmount(e.target.value)} placeholder="Refund amount (₹)" className="bg-white border border-slate-200 rounded-lg p-2 w-full text-slate-900 focus:outline-none focus:border-orange-500" />
        <input aria-label={`Refund reason ${transaction.id}`} value={reason} disabled={busy || reconcile} onChange={e => setReason(e.target.value)} placeholder="Reason" className="bg-white border border-slate-200 rounded-lg p-2 w-full text-slate-900 focus:outline-none focus:border-orange-500" />
        <button disabled={busy || reconcile || !reason.trim() || !(Number(amount) > 0 && Math.round(Number(amount) * 100) <= transaction.refundable_paise)} onClick={refund} className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg p-2 font-bold text-xs disabled:opacity-40">Request Refund</button>
      </>}{message && <p role="status" className="text-emerald-700 text-xs font-medium">{message}</p>}{operation && <p className="break-all text-[10px] text-slate-400">Operation: {operation}</p>}</div>
  </details>;
}
