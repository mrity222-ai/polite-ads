import React from 'react';
import { BudgetBreakdown } from '../../features/campaigns/AdContentEditor';

export default function InvoiceModal({ invoice, isOpen, onClose }) {
  if (!isOpen || !invoice) return null;
  return <div className="fixed inset-0 z-50 bg-black/60 p-4 overflow-y-auto flex items-start justify-center" role="dialog" aria-modal="true" aria-label="Payment receipt">
    <article className="bg-white rounded-3xl p-6 my-6 w-full max-w-2xl text-gray-950 space-y-5">
      <div className="flex justify-between"><h3 className="text-xl font-bold">Payment receipt</h3><button aria-label="Close receipt" onClick={onClose}>✕</button></div>
      <p className="font-bold">PolitiAds · {invoice.invoice_number}</p>
      <dl className="text-sm space-y-2"><div>Date: {invoice.date}</div><div>Customer: {invoice.candidate_name}</div>
        <div>Reference: {invoice.razorpay_payment_id}</div><div>Item: {invoice.description}</div>
        <div>Payment status: {invoice.status}</div><div>Method: {invoice.payment_method}</div>
        <div className="text-xl font-bold">Amount received: ₹{invoice.amount_inr?.toLocaleString('en-IN')}</div></dl>
      {invoice.pricing_snapshot && <BudgetBreakdown quote={invoice.pricing_snapshot} />}
      <p className="text-sm">Reserved campaign funds: ₹{(invoice.reserved_paise || 0) / 100} · Refunds reserved/processed: ₹{(invoice.refund_reserved_paise || 0) / 100}</p>
      <p className="text-xs text-gray-600">This receipt records the payment received. Campaign allocation is separate from confirmed advertising delivery and actual spend. This is not a tax invoice or regulatory certification.</p>
      <div className="flex gap-3 justify-end"><button onClick={() => window.print()} className="border rounded-xl px-4 py-2">Print Receipt</button><button onClick={onClose} className="bg-emerald-700 text-white rounded-xl px-4 py-2">Close</button></div>
    </article></div>;
}
