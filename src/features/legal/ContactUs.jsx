import React from 'react';
import { ArrowLeft, Mail, Phone, MapPin, Clock, ShieldCheck } from 'lucide-react';

export default function ContactUs({ onBack }) {
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
            <Mail className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Contact & Grievance</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm p-6 sm:p-10 space-y-8">
          {/* Header */}
          <div className="border-b border-gray-100 pb-6 space-y-2">
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Customer Support & Compliance
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-950 tracking-tight">
              Contact Us & Grievance Redressal
            </h1>
            <p className="text-xs text-gray-500">
              PolitiAds &bull; Operated by Maeaco &bull; Official Domain: <span className="font-semibold text-gray-800">politiads.maeaco.com</span>
            </p>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200/80 space-y-2">
              <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
                <Mail className="w-4 h-4" />
                <span>General & Technical Support</span>
              </div>
              <p className="text-xs text-gray-600">
                For campaign assistance, ad formatting queries, and onboarding guidance:
              </p>
              <a href="mailto:support@maeaco.com" className="block text-xs font-bold text-gray-950 hover:text-emerald-700">
                support@maeaco.com
              </a>
            </div>

            <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200/80 space-y-2">
              <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
                <Phone className="w-4 h-4" />
                <span>Billing & Refunds Desk</span>
              </div>
              <p className="text-xs text-gray-600">
                For payment receipts, GST invoices, and refund reconciliations:
              </p>
              <a href="mailto:billing@maeaco.com" className="block text-xs font-bold text-gray-950 hover:text-emerald-700">
                billing@maeaco.com
              </a>
            </div>

            <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200/80 space-y-2">
              <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
                <ShieldCheck className="w-4 h-4" />
                <span>Privacy & Data Protection</span>
              </div>
              <p className="text-xs text-gray-600">
                For Meta user data deletion, privacy notices, and security matters:
              </p>
              <a href="mailto:privacy@maeaco.com" className="block text-xs font-bold text-gray-950 hover:text-emerald-700">
                privacy@maeaco.com
              </a>
            </div>

            <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200/80 space-y-2">
              <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
                <Clock className="w-4 h-4" />
                <span>Support Operating Hours</span>
              </div>
              <p className="text-xs text-gray-600">
                Monday to Saturday &bull; 9:30 AM to 6:30 PM IST
              </p>
              <span className="inline-block text-[11px] font-semibold text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded">
                Active Campaign Hours: Extended Election Coverage
              </span>
            </div>
          </div>

          {/* Grievance Redressal Section */}
          <section className="bg-white p-6 rounded-2xl border border-gray-200 space-y-3">
            <div className="flex items-center gap-2 text-gray-950 font-bold text-sm">
              <MapPin className="w-4 h-4 text-emerald-600" />
              <span>Grievance Redressal Officer (Under IT Rules, 2021)</span>
            </div>
            <div className="text-xs sm:text-sm text-gray-700 space-y-1.5 leading-relaxed">
              <p><strong>Designation:</strong> Compliance & Grievance Redressal Officer</p>
              <p><strong>Entity Name:</strong> Maeaco (Operating PolitiAds)</p>
              <p><strong>Platform Domain:</strong> politiads.maeaco.com</p>
              <p><strong>Address:</strong> India Operations Centre, Maeaco Media & Tech</p>
              <p><strong>Grievance Email:</strong> <a href="mailto:privacy@maeaco.com" className="text-emerald-700 font-semibold underline">privacy@maeaco.com</a></p>
              <p className="text-gray-500 text-xs pt-1">
                Any complaint or grievance regarding content, electoral disclaimer compliance, or data privacy is acknowledged within 24 hours and addressed within 15 days in accordance with applicable Indian laws.
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
