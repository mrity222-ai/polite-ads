import React from 'react';
import { ArrowLeft, Shield, Lock, FileText, CheckCircle2 } from 'lucide-react';

export default function PrivacyPolicy({ onBack }) {
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
            <Shield className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Legal Compliance</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm p-6 sm:p-10 space-y-8">
          {/* Document Header */}
          <div className="border-b border-gray-100 pb-6 space-y-2">
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Official Privacy Policy
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-950 tracking-tight">
              Privacy Policy for PolitiAds
            </h1>
            <p className="text-xs text-gray-500">
              Domain: <span className="font-semibold text-gray-800">politiads.maeaco.com</span> &bull; Operated by Maeaco &bull; Effective Date: October 27, 2026
            </p>
          </div>

          {/* Intro */}
          <section className="space-y-3 text-xs sm:text-sm text-gray-700 leading-relaxed">
            <p>
              At <strong>PolitiAds</strong> (accessible from <code>politiads.maeaco.com</code>, operated by <strong>Maeaco</strong>), we respect and protect the privacy of election candidates, campaign managers, and visitors. This Privacy Policy details how we collect, store, encrypt, process, and protect candidate information when you create and manage hyperlocal political advertisements across Meta platforms (Facebook and Instagram).
            </p>
            <p>
              We comply strictly with India’s <strong>Digital Personal Data Protection Act (DPDP Act 2023)</strong>, the <strong>Information Technology Act, 2000</strong>, and <strong>Meta’s Platform Terms and Developer Policies</strong> regarding political and social issue advertising.
            </p>
          </section>

          {/* 1. Information We Collect */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              1. Information We Collect
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>To prepare, review, and publish authorized election campaign advertisements, we collect:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li><strong>Candidate Account Details:</strong> Full name, mobile number, and email address for account authentication and OTP verification.</li>
                <li><strong>Constituency & Electoral Details:</strong> Target ward number, Gram Panchayat, municipal body, block name, and PIN code.</li>
                <li><strong>Campaign Assets:</strong> Candidate portrait photograph, registered party/independent election symbol, campaign slogans, and WhatsApp/helpline phone number.</li>
                <li><strong>Geographical Coordinates:</strong> GPS latitude and longitude (captured with explicit browser permission) or manual PIN code boundaries to define ad targeting fences (1 km to 10 km radius).</li>
                <li><strong>Payment Transaction Records:</strong> Order IDs, integer paise transaction amounts, and payment verification identifiers issued by Razorpay. We do not store raw credit/debit card numbers or UPI PINs.</li>
              </ul>
            </div>
          </section>

          {/* 2. Meta Platform Data & Marketing API Usage */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <Lock className="w-5 h-5 text-emerald-600" />
              2. Meta Platform Data & Marketing API Usage
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>When candidates connect their Meta (Facebook) account to PolitiAds:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li><strong>Access Tokens:</strong> We request user authorization to manage campaign assets via Meta Marketing API (<code>ads_management</code>, <code>pages_read_engagement</code>, and <code>pages_manage_ads</code>).</li>
                <li><strong>Encryption at Rest:</strong> All Meta OAuth tokens and Page Access Tokens are immediately encrypted using <strong>Fernet authenticated encryption</strong> cryptographic standards before being saved in our relational database.</li>
                <li><strong>Limited Purpose:</strong> Meta Page tokens are utilized solely for publishing approved candidate ad creatives with verified <em>"Paid for by"</em> disclaimers and fetching real-time delivery status.</li>
                <li><strong>Zero Data Sale:</strong> PolitiAds and Maeaco never sell, lease, transfer, or broker candidate data or voter engagement metrics to third-party data brokers or marketing aggregators.</li>
              </ul>
            </div>
          </section>

          {/* 3. ECI Compliance & Disclaimers */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              3. Election Commission of India (ECI) Compliance
            </h2>
            <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
              In accordance with guidelines from the Election Commission of India (ECI) and Meta’s Advertising Policies on Social Issues, Elections or Politics:
            </p>
            <ul className="list-disc list-inside space-y-1.5 pl-2 text-xs sm:text-sm text-gray-600">
              <li>Every ad submitted through PolitiAds includes a mandatory, non-editable <strong>"Paid for by: [Candidate Name/Campaign]"</strong> disclaimer.</li>
              <li>Ads are placed initially in a <strong>PAUSED</strong> state on Meta’s ad network until full editorial and compliance review is completed by the agency.</li>
              <li>Candidates are responsible for obtaining required MCMC (Media Certification and Monitoring Committee) pre-certification when the Model Code of Conduct is in force.</li>
            </ul>
          </section>

          {/* 4. Security & Sensitive Data Redaction */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 flex items-center gap-2">
              <Shield className="w-5 h-5 text-emerald-600" />
              4. Data Security & Storage
            </h2>
            <div className="space-y-2 text-xs sm:text-sm text-gray-700 leading-relaxed">
              <p>
                We enforce multi-layered defense to safeguard campaign information:
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-2 text-gray-600">
                <li><strong>Password Protection:</strong> Passwords are cryptographically hashed using <strong>Argon2id</strong>.</li>
                <li><strong>Session Tokens:</strong> Stored as SHA-256 hashes and delivered via secure <code>HttpOnly</code> and <code>SameSite=Lax</code> browser cookies.</li>
                <li><strong>CSRF & Throttling:</strong> State-altering write operations enforce HMAC CSRF tokens and per-IP rate-limiting to prevent brute-force attacks.</li>
                <li><strong>Redacting Logger:</strong> Server logs automatically mask bearer tokens, webhook signatures, and candidate personal identifiers with <code>[REDACTED_SECRET]</code>.</li>
              </ul>
            </div>
          </section>

          {/* 5. User Data Deletion Rights */}
          <section className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-gray-950">
              5. User Data Deletion & Revocation Rights
            </h2>
            <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
              Candidates have full control over their personal and campaign data. You may request permanent deletion of your account, campaign drafts, and associated Meta tokens at any time by visiting our dedicated <a href="#/data-deletion" className="text-emerald-700 font-bold underline">User Data Deletion Instructions</a> page or by emailing us at <a href="mailto:privacy@maeaco.com" className="text-emerald-700 font-bold underline">privacy@maeaco.com</a>. Requests are completed within 72 hours.
            </p>
          </section>

          {/* 6. Grievance Officer & Contact Information */}
          <section className="space-y-3 border-t border-gray-100 pt-6">
            <h2 className="text-base sm:text-lg font-bold text-gray-950">
              6. Grievance Officer & Contact Information
            </h2>
            <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
              In accordance with the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021, the Grievance Officer for PolitiAds is:
            </p>
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs sm:text-sm text-gray-800 space-y-1">
              <p><strong>Grievance Redressal Officer:</strong> Compliance Team, PolitiAds (Maeaco)</p>
              <p><strong>Official Domain:</strong> politiads.maeaco.com</p>
              <p><strong>Email:</strong> <a href="mailto:privacy@maeaco.com" className="text-emerald-700 font-semibold underline">privacy@maeaco.com</a> / <a href="mailto:support@maeaco.com" className="text-emerald-700 font-semibold underline">support@maeaco.com</a></p>
              <p><strong>Resolution Turnaround:</strong> Within 48 business hours</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
