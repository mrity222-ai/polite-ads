import React from 'react';
import { ArrowLeft, RefreshCw, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function RefundPolicy({ onBack }) {
  return (
    <div className="min-h-screen bg-[#fafafa] text-gray-900 font-sans selection:bg-emerald-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-xs font-bold text-gray-700 hover:text-gray-950 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to PolitiAds</span>
          </button>
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Refund & Cancellation</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm p-6 sm:p-10 space-y-8">
          {/* Header */}
          <div className="border-b border-gray-100 pb-6 space-y-2">
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Razorpay Merchant Compliance
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-950 tracking-tight">
              Refund & Cancellation Policy
            </h1>
            <p className="text-xs text-gray-500">
              Domain: <span className="font-semibold text-gray-800">politiads.maeaco.com</span> &bull; Operated by Maeaco &bull; Effective Date: October 27, 2026
            </p>
          </div>

          {/* Intro */}
          <div className="space-y-3 text-xs sm:text-sm text-gray-700 leading-relaxed">
            <p>
              At <strong>PolitiAds</strong> (operated by <strong>Maeaco</strong>), we strive to deliver transparent, reliable hyperlocal advertising services for Indian election candidates. This Refund & Cancellation Policy outlines the exact conditions under which refunds are approved, calculated, and credited back to candidates.
            </p>
          </div>

          {/* Cancellation & Refund Scenarios */}
          <section className="space-y-4">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              1. Refund Eligibility & Scenarios
            </h2>
            <div className="space-y-3">
              {/* Scenario 1 */}
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs sm:text-sm space-y-1">
                <h3 className="font-bold text-gray-900">Scenario A: Campaign Rejected during Administrative Compliance Review</h3>
                <p className="text-gray-600 leading-relaxed">
                  If an ad draft submitted by a candidate cannot be approved due to compliance guidelines, incorrect ward jurisdiction, or non-verifiable candidate documentation, the candidate will receive a <strong>100% full refund</strong> of all deposited funds.
                </p>
              </div>

              {/* Scenario 2 */}
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs sm:text-sm space-y-1">
                <h3 className="font-bold text-gray-900">Scenario B: Candidate Cancels Prior to Meta Submission</h3>
                <p className="text-gray-600 leading-relaxed">
                  If a candidate chooses to cancel an ad draft while it is still under company review and has not yet been pushed to Meta’s ad network, a <strong>100% full refund</strong> will be initiated immediately upon cancellation request.
                </p>
              </div>

              {/* Scenario 3 */}
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs sm:text-sm space-y-1">
                <h3 className="font-bold text-gray-900">Scenario C: Campaign Paused or Terminated Mid-Flight</h3>
                <p className="text-gray-600 leading-relaxed">
                  If a campaign is active on Meta and the candidate decides to permanently pause or stop the ad, the candidate is entitled to a refund of the <strong>unspent daily budget balance</strong>. Any ad spend already delivered to Meta and the proportional platform processing cut are non-refundable.
                </p>
              </div>

              {/* Scenario 4 */}
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs sm:text-sm space-y-1">
                <h3 className="font-bold text-gray-900">Scenario D: Duplicate Payment or Technical Gateway Errors</h3>
                <p className="text-gray-600 leading-relaxed">
                  In case of technical network timeouts resulting in multiple debits for a single order, duplicate charges are automatically reconciled and refunded in full.
                </p>
              </div>
            </div>
          </section>

          {/* Refund Timeline & Mode */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <Clock className="w-5 h-5 text-emerald-600" />
              2. Refund Processing Timelines & Mode of Payment
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>
                All refunds are processed strictly through our integrated payment gateway (<strong>Razorpay</strong>):
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li><strong>Mode:</strong> Refunds are credited strictly to the <strong>original source of payment</strong> (same UPI ID, bank account, or debit/credit card). Cash or third-party transfer refunds are never issued.</li>
                <li><strong>Timeline:</strong> Once initiated by PolitiAds, funds typically reflect in the candidate’s bank account within <strong>5 to 7 business days</strong>, depending on the issuing bank’s clearance cycles.</li>
                <li><strong>Ledger Tracking:</strong> Every refund is recorded with an immutable negative reversal entry in the candidate's double-entry accounting ledger.</li>
              </ul>
            </div>
          </section>

          {/* How to Request a Refund */}
          <section className="space-y-3 border-t border-gray-100 pt-6">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-emerald-600" />
              3. How to Request a Refund
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>To request a refund or report a billing discrepancy:</p>
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs space-y-1 text-gray-800">
                <p>1. Email: <a href="mailto:billing@maeaco.com" className="font-bold text-emerald-700 underline">billing@maeaco.com</a> or <a href="mailto:support@maeaco.com" className="font-bold text-emerald-700 underline">support@maeaco.com</a></p>
                <p>2. Subject: <strong>"Refund Request - [Order ID or Payment ID]"</strong></p>
                <p>3. Include: Registered candidate mobile number, Order ID, and reason for cancellation.</p>
                <p>4. Response Window: Our finance team responds within <strong>24 business hours</strong>.</p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
