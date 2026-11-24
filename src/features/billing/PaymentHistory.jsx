import { checkout } from '../../api/checkout';
import React, { useState, useEffect, useCallback } from 'react';
import {
  CheckCircle2,
  Layers,
  CreditCard,
  FileText,
  RefreshCw,
  AlertCircle,
  Zap,
} from 'lucide-react';
import { integrationsApi } from '../../api/integrations';
import InvoiceModal from '../../components/billing/InvoiceModal';

export default function PaymentHistory() {
  const [subStatus, setSubStatus] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  const [purchasingPlanId, setPurchasingPlanId] = useState(null);
  const [purchaseSuccessMessage, setPurchaseSuccessMessage] = useState('');

  const loadBillingData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [subData, invData] = await Promise.all([
        integrationsApi.getSubscriptionStatus(),
        integrationsApi.getInvoices()
      ]);
      setSubStatus(subData);
      setInvoices(invData || []);
    } catch (err) {
      setError(err.message || 'Failed to load billing information.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(loadBillingData);
  }, [loadBillingData]);

  const handleSubscribe = async (plan) => {
    setPurchasingPlanId(plan.id);
    setPurchaseSuccessMessage('');
    setError('');

    try {
      if (!window.confirm('This purchase starts a new 30-day subscription immediately after payment verification. It replaces current access; unused time is not carried forward. Continue?')) return;
      await checkout('subscription_plan', plan.id);
      setPurchaseSuccessMessage(`Payment verified for ${plan.name}.`);
      await loadBillingData();
    } catch (err) {
      setError(err.message || 'Subscription checkout failed.');
    } finally {
      setPurchasingPlanId(null);
    }
  };

  const handleViewInvoice = (invoice) => {
    setSelectedInvoice(invoice);
    setIsInvoiceModalOpen(true);
  };

  if (loading) {
    return (
      <div className="p-8 text-center space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto" />
        <p className="text-xs text-gray-500 font-medium">Loading active subscription &amp; invoices...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Top Notifications */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
          <button onClick={loadBillingData} className="font-bold underline">Retry</button>
        </div>
      )}

      {purchaseSuccessMessage && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span className="font-bold">{purchaseSuccessMessage}</span>
        </div>
      )}

      {/* ========================================================
          1. CURRENT ACTIVE PACKAGE / ACTIVE DEMO STATUS CARD
      ======================================================== */}
      <div className="bg-gradient-to-br from-emerald-950 via-slate-900 to-slate-950 text-white p-6 sm:p-8 rounded-3xl border border-emerald-900/40 shadow-xl relative overflow-hidden">
        
        {/* Soft Background Accent Glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  {subStatus?.entitlement_status === 'active' ? (subStatus.is_demo ? 'Active Trial' : 'Active Subscription') : (subStatus?.status || 'Access Unavailable')}
                </span>
                <span className="text-xs text-gray-400 font-medium">
                  {subStatus?.days_remaining !== undefined ? `${subStatus.days_remaining} days remaining` : '30-day cycle'}
                </span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                {subStatus?.plan_name || 'No active entitlement'}
              </h3>
            </div>

            <div className="text-left sm:text-right bg-white/10 backdrop-blur-md px-4 py-3 rounded-2xl border border-white/10 shrink-0">
              <span className="text-[10px] uppercase font-bold text-gray-300 tracking-wider block">
                Daily Ad Limit Cap
              </span>
              <div className="text-xl sm:text-2xl font-black text-emerald-400">
                ₹{subStatus?.daily_ad_limit?.toLocaleString() ?? '0'}
                <span className="text-xs text-gray-300 font-normal"> / day</span>
              </div>
            </div>
          </div>

          {/* Active Features Checklist */}
          <div className="pt-4 border-t border-white/10">
            <span className="text-[11px] uppercase font-bold text-gray-400 tracking-wider block mb-2.5">
              Included Campaign Privileges:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs text-gray-200">
              {(subStatus?.features || [
                'Hyperlocal Ward Slogan Polish',
                'Real Meta Sandbox Ad Simulation',
                'ECI Compliant Disclaimers',
                'Direct WhatsApp Voter Forwarding'
              ]).map((feat, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span className="truncate">{feat}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================
          2. AVAILABLE PACKAGES (SYNCED FROM SUPER ADMIN)
      ======================================================== */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
          <div>
            <h4 className="text-lg font-bold text-gray-950 flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600" />
              <span>Available Subscription Packages</span>
            </h4>
            <p className="text-xs text-gray-500">
              Packages are managed by the platform team. Review the package details before checkout.
            </p>
          </div>
          <button
            type="button"
            onClick={loadBillingData}
            className="self-start sm:self-auto px-3 py-1.5 rounded-full text-xs font-semibold text-gray-600 bg-gray-100 hover:bg-gray-200 transition flex items-center gap-1.5"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Sync Packages</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {(subStatus?.available_plans || []).map((plan) => {
            const isCurrent = subStatus?.plan_id === plan.id;
            return (
              <div
                key={plan.id}
                className={`p-6 rounded-3xl border flex flex-col justify-between transition ${
                  isCurrent
                    ? 'border-emerald-600 bg-emerald-50/30 shadow-md ring-2 ring-emerald-600/20'
                    : 'border-gray-200 bg-white hover:border-gray-300 shadow-2xs'
                }`}
              >
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <h5 className="font-bold text-gray-950 text-base">{plan.name}</h5>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {plan.badge || 'Standard'}
                    </span>
                  </div>

                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-black text-gray-950">
                      ₹{plan.price?.toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-500 font-medium">/ cycle</span>
                  </div>

                  <div className="text-xs text-emerald-700 font-medium bg-emerald-50/80 px-2.5 py-1 rounded-lg">
                    Daily Cap: ₹{plan.daily_ad_limit?.toLocaleString()}/day
                  </div>

                  <ul className="space-y-2 text-xs text-gray-600 pt-2 border-t border-gray-100">
                    {(plan.features || []).map((feat, fIdx) => (
                      <li key={fIdx} className="flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-5">
                  {isCurrent ? (
                    <button
                      type="button"
                      disabled
                      className="w-full py-2.5 rounded-full text-xs font-bold bg-emerald-600 text-white cursor-default flex items-center justify-center gap-1.5 shadow-2xs"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Current Active Plan</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleSubscribe(plan)}
                      disabled={purchasingPlanId === plan.id}
                      className="w-full py-2.5 rounded-full text-xs font-bold bg-black hover:bg-neutral-800 text-white transition flex items-center justify-center gap-1.5 shadow-xs disabled:opacity-50"
                    >
                      {purchasingPlanId === plan.id ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <Zap className="w-3.5 h-3.5 text-amber-400" />
                          <span>Upgrade to {plan.name.split(' ')[0]}</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================
          3. INVOICES & GST RECEIPTS TABLE
      ======================================================== */}
      <div className="space-y-4">
        <div className="border-b border-gray-100 pb-3">
          <h4 className="text-lg font-bold text-gray-950 flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-600" />
            <span>Payment Receipts</span>
          </h4>
          <p className="text-xs text-gray-500">
            View verified payment records for campaign funding and subscriptions. These receipts are not tax invoices.
          </p>
        </div>

        {invoices.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-gray-50 border border-gray-200 space-y-2">
            <CreditCard className="w-8 h-8 text-gray-400 mx-auto" />
            <p className="text-xs text-gray-500 font-medium">No payment transactions recorded yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-gray-200 bg-white shadow-2xs">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-600 uppercase text-[10px] font-bold tracking-wider border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3.5">Invoice #</th>
                  <th className="px-4 py-3.5">Date</th>
                  <th className="px-4 py-3.5">Package / Item</th>
                  <th className="px-4 py-3.5">Amount</th>
                  <th className="px-4 py-3.5">Payment Method</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5 text-right">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50/80 transition">
                    <td className="px-4 py-3.5 font-mono font-bold text-gray-950">
                      {inv.invoice_number}
                    </td>
                    <td className="px-4 py-3.5 text-gray-600">
                      {inv.date}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-gray-900">{inv.description}</div>
                      <div className="text-[10px] text-gray-400 font-mono">{inv.sac_code ? `SAC: ${inv.sac_code}` : "Payment receipt"}</div>
                    </td>
                    <td className="px-4 py-3.5 font-black text-gray-950 font-mono text-sm">
                      ₹{inv.amount_inr?.toLocaleString()}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-gray-700 uppercase">
                      {inv.payment_method}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        type="button"
                        onClick={() => handleViewInvoice(inv)}
                        className="px-3 py-1.5 rounded-full text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition inline-flex items-center gap-1.5 shadow-2xs"
                      >
                        <FileText className="w-3.5 h-3.5 text-emerald-700" />
                        <span>View Receipt</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invoice Modal for Printable Receipt */}
      <InvoiceModal
        invoice={selectedInvoice}
        isOpen={isInvoiceModalOpen}
        onClose={() => {
          setIsInvoiceModalOpen(false);
          setSelectedInvoice(null);
        }}
      />

    </div>
  );
}
