import React from 'react';
import { ArrowLeft, Scale, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function TermsOfService({ onBack }) {
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
            <Scale className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Terms of Service</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm p-6 sm:p-10 space-y-8">
          {/* Header */}
          <div className="border-b border-gray-100 pb-6 space-y-2">
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Legal Agreement
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-950 tracking-tight">
              Terms of Service
            </h1>
            <p className="text-xs text-gray-500">
              Domain: <span className="font-semibold text-gray-800">politiads.maeaco.com</span> &bull; Operated by Maeaco &bull; Effective Date: October 27, 2026
            </p>
          </div>

          {/* Intro */}
          <div className="space-y-3 text-xs sm:text-sm text-gray-700 leading-relaxed">
            <p>
              Welcome to <strong>PolitiAds</strong> (accessible at <code>politiads.maeaco.com</code>), owned and operated by <strong>Maeaco</strong> ("we", "us", or "the Platform"). By registering an account, preparing an election ad draft, or submitting campaign budgets, you ("Candidate", "User", or "Campaign Manager") agree to be bound by these Terms of Service.
            </p>
            <p>
              If you do not agree with any part of these Terms, you must not use or access our software or services.
            </p>
          </div>

          {/* 1. Nature of Service & Intermediary Status */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              1. Nature of Service & Intermediary Role
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>
                PolitiAds provides a self-serve advertising technology workflow for local candidates contesting Indian elections (including Gram Panchayat, Nagar Palika, Ward Councillor, Block Pramukh, and Assembly elections).
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li><strong>Technology Intermediary:</strong> We act strictly as a technical intermediary and digital marketing enabler. We are not a political party, election sponsor, political action committee, or campaign affiliate.</li>
                <li><strong>Agency Management:</strong> We review ad creative formatting, ensure compliance with Meta political ad specifications, and manage technical delivery parameters on behalf of registered candidates.</li>
              </ul>
            </div>
          </section>

          {/* 2. Candidate Obligations & Election Laws */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              2. Candidate Obligations & Compliance with Election Laws
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>As a candidate utilizing PolitiAds, you represent and warrant that:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li>You are lawfully contesting or exploring candidacy in the specified local election constituency.</li>
                <li>All uploaded assets (photographs, party election symbols, candidate declarations) are authentic, legally authorized, and do not infringe on third-party trademarks or copyrights.</li>
                <li><strong>Election Commission of India (ECI) Compliance:</strong> You bear full responsibility for obtaining mandatory pre-certification from the District or State <strong>Media Certification and Monitoring Committee (MCMC)</strong> when required by the Model Code of Conduct.</li>
                <li><strong>Mandatory Disclaimers:</strong> You consent to the automatic display of the official <em>"Paid for by: [Candidate Name]"</em> disclaimer on all public ad placements.</li>
              </ul>
            </div>
          </section>

          {/* 3. Prohibited Content & Account Suspension */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              3. Prohibited Content & Immediate Account Suspension
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>
                Candidates are strictly prohibited from submitting ad creatives containing:
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li>Hate speech, appeals to caste, religious communalism, or inciteful sectarian language.</li>
                <li>Unverified personal allegations, defamatory attacks, or slander against political opponents.</li>
                <li>Misleading voting instructions, fake polling location information, or deepfake generative audio/video.</li>
              </ul>
              <p className="bg-rose-50 text-rose-800 p-4 rounded-xl border border-rose-200 text-xs">
                <strong>Enforcement:</strong> Our compliance team reserves the unilateral right to reject any ad draft, suspend offending candidate accounts, and immediately revoke active sessions without prior notice if content violates ECI regulations or Meta's Advertising Policies.
              </p>
            </div>
          </section>

          {/* 4. Financial Terms, Budgets & Delivery */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950">
              4. Campaign Budgets, Pricing & Delivery
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li><strong>Integer Paise Precision:</strong> All financial transactions and balances are calculated strictly in integer paise (1 INR = 100 paise) via Razorpay.</li>
                <li><strong>Initial PAUSED Default:</strong> To protect candidates from accidental budget exhaustion, all campaigns pushed to Meta are created in a default <code>PAUSED</code> state until human verification and candidate funding are confirmed.</li>
                <li><strong>No Guaranteed Election Outcome:</strong> PolitiAds delivers targeted digital impressions based on geofencing and budget; we do not guarantee voting outcomes, election victory, or specific turnout numbers.</li>
              </ul>
            </div>
          </section>

          {/* 5. Limitation of Liability */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950">
              5. Limitation of Liability & Indemnification
            </h2>
            <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
              To the maximum extent permitted by Indian law, Maeaco and PolitiAds shall not be liable for any indirect, incidental, punitive, or consequential damages resulting from upstream Meta ad delivery delays, network outages, or regulatory disqualifications imposed by election authorities. You agree to indemnify and hold harmless Maeaco from any claims, fines, or legal proceedings arising from your campaign statements or trademark violations.
            </p>
          </section>

          {/* 6. Jurisdiction & Contact */}
          <section className="space-y-2 border-t border-gray-100 pt-6 text-xs text-gray-600">
            <p>
              <strong>Governing Law:</strong> These Terms are governed by and construed in accordance with the laws of India. Any disputes arising under these Terms shall be subject to the exclusive jurisdiction of the competent courts in India.
            </p>
            <p>
              <strong>Questions:</strong> For inquiries regarding these Terms, contact our legal counsel at <a href="mailto:support@maeaco.com" className="text-emerald-700 font-semibold underline">support@maeaco.com</a>.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
