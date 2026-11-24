import React from 'react';
import { ArrowLeft, Trash2, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function DataDeletion({ onBack }) {
  return (
    <div className="min-h-screen bg-[#fafafa] text-gray-900 font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Header */}
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
            <Trash2 className="w-4 h-4 text-rose-600" />
            <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Meta User Data Deletion</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm p-6 sm:p-10 space-y-8">
          {/* Header */}
          <div className="border-b border-gray-100 pb-6 space-y-2">
            <span className="text-[11px] font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Facebook Platform Compliance
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-950 tracking-tight">
              User Data Deletion Instructions
            </h1>
            <p className="text-xs text-gray-500">
              Domain: <span className="font-semibold text-gray-800">politiads.maeaco.com</span> &bull; Operated by Maeaco
            </p>
          </div>

          {/* Explanation */}
          <div className="space-y-3 text-xs sm:text-sm text-gray-700 leading-relaxed">
            <p>
              PolitiAds values your privacy and data ownership. In compliance with <strong>Meta Platform Terms (Section 4.a: Data Deletion)</strong> and the <strong>Digital Personal Data Protection Act, 2023</strong>, this page provides explicit instructions on how you can remove your activities and request the complete deletion of your personal and Facebook Page data stored on our servers.
            </p>
          </div>

          {/* Option 1: Meta Settings */}
          <section className="space-y-4 bg-gray-50 p-6 rounded-2xl border border-gray-200">
            <h2 className="text-base font-bold text-gray-950 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Method 1: Revoke Access Directly via Facebook Settings
            </h2>
            <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
              If you wish to remove PolitiAds permissions from your Facebook account:
            </p>
            <ol className="list-decimal list-inside space-y-2 text-xs sm:text-sm text-gray-700 pl-2">
              <li>Log in to your Facebook profile and navigate to <strong>Settings & Privacy &gt; Settings</strong>.</li>
              <li>In the left menu, select <strong>Apps and Websites</strong> (or visit <a href="https://www.facebook.com/settings?tab=applications" target="_blank" rel="noreferrer" className="text-emerald-700 font-semibold underline">facebook.com/settings?tab=applications</a>).</li>
              <li>Locate <strong>PolitiAds</strong> in the list of authorized applications.</li>
              <li>Click the <strong>Remove</strong> button.</li>
              <li>Confirm your choice. This immediately revokes all OAuth tokens and terminates PolitiAds access to your Facebook Pages.</li>
            </ol>
          </section>

          {/* Option 2: Request Server-Side Deletion */}
          <section className="space-y-4 bg-gray-50 p-6 rounded-2xl border border-gray-200">
            <h2 className="text-base font-bold text-gray-950 flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-rose-600" />
              Method 2: Request Complete Server Data Deletion from PolitiAds
            </h2>
            <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
              To permanently erase your candidate profile, uploaded portrait photos, party symbols, draft campaigns, and stored encrypted access tokens from our database:
            </p>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 pl-2">
              <p>
                1. Send an email to: <a href="mailto:privacy@maeaco.com" className="font-bold text-emerald-700 underline">privacy@maeaco.com</a> or <a href="mailto:support@maeaco.com" className="font-bold text-emerald-700 underline">support@maeaco.com</a>.
              </p>
              <p>
                2. Use the Subject line: <strong>"User Data Deletion Request - [Your Registered Email or Mobile]"</strong>.
              </p>
              <p>
                3. Mention your candidate name and registered ward/mobile number.
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-gray-200 text-xs text-gray-600 flex items-start gap-2.5">
              <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <p>
                <strong>Verification & Confirmation:</strong> Our data protection team will verify your identity and purge your database records, encrypted tokens, and uploaded media within <strong>72 hours</strong>. You will receive an email confirmation with a unique Deletion Confirmation ID.
              </p>
            </div>
          </section>

          {/* Data Retention Exceptions */}
          <section className="space-y-2 border-t border-gray-100 pt-6 text-xs text-gray-500">
            <h3 className="font-bold text-gray-800">Statutory Recordkeeping Requirements:</h3>
            <p>
              Financial invoice records, Razorpay payment reference IDs, and double-entry ledger entries are retained in an immutable, anonymized audit log as strictly mandated by Indian taxation laws (GST Act, 2017) and company accounting regulations for statutory audit periods.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
