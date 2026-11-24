import React from 'react';

export default function AuthIllustration({
  headline = "Make your work easier and organized with PolitiAds"
}) {
  return (
    <div className="hidden lg:flex flex-col justify-between items-center bg-[#f2f8f4] rounded-[36px] p-10 xl:p-14 min-h-[640px] h-full relative overflow-hidden select-none border border-emerald-50/60 shadow-xs">
      
      {/* Top Floating Badge / Sparkle decoration */}
      <div className="w-full flex justify-between items-center z-10">
        <span className="text-[11px] font-bold tracking-wider text-emerald-800 bg-white/80 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-emerald-100 shadow-2xs">
          ⚡ Hyperlocal Campaign AI
        </span>
        <span className="text-[11px] font-bold text-gray-500 bg-emerald-100/60 px-3 py-1 rounded-full">
          v2.0 Active
        </span>
      </div>

      {/* Main Illustration Area */}
      <div className="relative my-auto w-full max-w-[420px] flex items-center justify-center">
        
        {/* Soft Background Energy Rings / Thought Clouds */}
        <svg
          className="absolute inset-0 w-full h-full text-emerald-200/50 pointer-events-none"
          viewBox="0 0 400 400"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray="4 6"
        >
          <path d="M 120 180 C 100 120, 160 80, 200 90 C 240 80, 300 110, 290 170 C 310 200, 290 260, 250 280 C 210 300, 150 290, 130 250 Z" />
          <path d="M 90 200 C 70 150, 120 110, 160 110" opacity="0.6" />
          <path d="M 280 140 C 320 170, 310 230, 270 250" opacity="0.6" />
        </svg>

        {/* Floating Avatar 1 (Top-Left) */}
        <div className="absolute top-2 left-4 z-20 animate-bounce duration-1000" style={{ animationDuration: '4s' }}>
          <div className="w-12 h-12 rounded-full bg-emerald-100 border-2 border-white shadow-md flex items-center justify-center text-lg overflow-hidden ring-4 ring-emerald-50">
            <svg viewBox="0 0 36 36" fill="none" className="w-10 h-10 text-emerald-900">
              <circle cx="18" cy="18" r="18" fill="#d1fae5" />
              {/* Guy avatar face with spiked hair and happy smile */}
              <path d="M12 12 Q14 7 18 9 Q21 6 23 10 Q26 12 24 16 L12 16 Z" fill="#0f172a" />
              <circle cx="18" cy="20" r="7" fill="#fde68a" />
              <circle cx="15.5" cy="19.5" r="1" fill="#0f172a" />
              <circle cx="20.5" cy="19.5" r="1" fill="#0f172a" />
              <path d="M16 23 Q18 25 20 23" stroke="#0f172a" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
          </div>
        </div>

        {/* Floating Avatar 2 (Right Side) */}
        <div className="absolute top-24 right-0 z-20 animate-pulse" style={{ animationDuration: '3.5s' }}>
          <div className="w-11 h-11 rounded-full bg-white border-2 border-emerald-200 shadow-md flex items-center justify-center overflow-hidden ring-4 ring-emerald-50">
            <svg viewBox="0 0 36 36" fill="none" className="w-9 h-9">
              <circle cx="18" cy="18" r="18" fill="#e0e7ff" />
              {/* Woman avatar face */}
              <circle cx="18" cy="19" r="6.5" fill="#fde68a" />
              <path d="M12 14 Q18 10 24 14 Q25 20 23 23 L13 23 Z" fill="#1e1b4b" />
              <circle cx="16" cy="18.5" r="1" fill="#0f172a" />
              <circle cx="20" cy="18.5" r="1" fill="#0f172a" />
              <circle cx="18" cy="22" r="1.5" fill="#0f172a" />
            </svg>
          </div>
        </div>

        {/* Floating Task & Metrics Card (Left-bottom of illustration) */}
        <div className="absolute -bottom-2 -left-3 z-30 bg-white/95 backdrop-blur-md p-4 rounded-2xl border border-gray-100 shadow-xl max-w-[170px] transform -rotate-1 hover:rotate-0 transition-transform duration-300">
          <div className="space-y-1 mb-2.5">
            <h5 className="font-bold text-gray-900 text-xs tracking-tight">Canva Design</h5>
            <p className="text-[10px] text-gray-400 font-medium">10 Task</p>
          </div>

          <div className="flex items-center justify-between gap-2 pt-1 border-t border-gray-100">
            <span className="text-[9px] font-bold text-gray-700 bg-gray-100 px-2.5 py-1 rounded-full">
              Design
            </span>

            {/* Circular Progress (84%) */}
            <div className="relative w-8 h-8 flex items-center justify-center">
              <svg className="w-8 h-8 transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-gray-200"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-emerald-500"
                  strokeDasharray="84, 100"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span className="absolute text-[8px] font-extrabold text-gray-900">84%</span>
            </div>
          </div>
        </div>

        {/* Central Meditation Character SVG */}
        <div className="relative z-10 py-6">
          <svg
            className="w-72 h-72 sm:w-80 sm:h-80 drop-shadow-sm"
            viewBox="0 0 320 320"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Soft Green Clouds in background */}
            <path
              d="M 60 160 C 50 110, 110 90, 140 100 C 160 70, 220 70, 240 100 C 270 90, 310 120, 300 170 C 315 210, 280 250, 250 240"
              stroke="#86efac"
              strokeWidth="3"
              strokeLinecap="round"
              fill="none"
            />

            {/* Character Head & Hair */}
            <circle cx="160" cy="95" r="24" fill="#ffffff" stroke="#111827" strokeWidth="3" />
            <path
              d="M 140 95 C 136 78, 150 68, 160 68 C 172 68, 184 76, 180 95 C 174 88, 168 86, 160 88 C 150 90, 144 94, 140 95 Z"
              fill="#111827"
            />
            {/* Face details: Calm peaceful eyes and gentle smile */}
            <path d="M 151 94 Q 155 98 159 94" stroke="#111827" strokeWidth="2" strokeLinecap="round" fill="none" />
            <path d="M 163 94 Q 167 98 171 94" stroke="#111827" strokeWidth="2" strokeLinecap="round" fill="none" />
            <path d="M 158 103 Q 161 106 164 103" stroke="#111827" strokeWidth="2" strokeLinecap="round" fill="none" />

            {/* Torso with Mint Green Sweater */}
            <path
              d="M 136 122 Q 160 126 186 122 L 202 186 Q 160 196 120 186 Z"
              fill="#86efac"
              stroke="#111827"
              strokeWidth="3"
              strokeLinejoin="round"
            />

            {/* White Heart on Sweater */}
            <path
              d="M 161 146 C 161 141, 154 136, 148 141 C 143 145, 144 152, 161 163 C 178 152, 179 145, 174 141 C 168 136, 161 141, 161 146 Z"
              fill="none"
              stroke="#ffffff"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Black outline waist band */}
            <path d="M 120 186 Q 160 196 202 186" stroke="#111827" strokeWidth="5" strokeLinecap="round" />

            {/* Left Arm in Meditation Mudra */}
            <path
              d="M 136 126 Q 100 148 104 178"
              fill="none"
              stroke="#86efac"
              strokeWidth="16"
              strokeLinecap="round"
            />
            <path
              d="M 136 126 Q 100 148 104 178"
              fill="none"
              stroke="#111827"
              strokeWidth="3"
              strokeLinecap="round"
            />
            {/* Left Hand */}
            <circle cx="106" cy="180" r="9" fill="#ffffff" stroke="#111827" strokeWidth="3" />
            <path d="M 103 174 Q 108 170 113 176" stroke="#111827" strokeWidth="2.5" strokeLinecap="round" />

            {/* Right Arm in Meditation Mudra */}
            <path
              d="M 186 126 Q 222 148 218 178"
              fill="none"
              stroke="#86efac"
              strokeWidth="16"
              strokeLinecap="round"
            />
            <path
              d="M 186 126 Q 222 148 218 178"
              fill="none"
              stroke="#111827"
              strokeWidth="3"
              strokeLinecap="round"
            />
            {/* Right Hand */}
            <circle cx="216" cy="180" r="9" fill="#ffffff" stroke="#111827" strokeWidth="3" />
            <path d="M 219 174 Q 214 170 209 176" stroke="#111827" strokeWidth="2.5" strokeLinecap="round" />

            {/* Crossed Legs (White Pants) */}
            <path
              d="M 120 188 C 96 210, 80 236, 128 250 C 160 258, 176 250, 186 244 L 202 188"
              fill="#ffffff"
              stroke="#111827"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            <path
              d="M 202 188 C 226 210, 242 236, 194 250 C 162 258, 146 250, 136 244 L 120 188"
              fill="#ffffff"
              stroke="#111827"
              strokeWidth="3"
              strokeLinejoin="round"
            />

            {/* Pant seam folds */}
            <path d="M 160 196 L 160 240" stroke="#111827" strokeWidth="2.5" strokeLinecap="round" />
            <path d="M 132 222 Q 150 230 168 222" stroke="#9ca3af" strokeWidth="2" strokeLinecap="round" fill="none" />

            {/* Feet */}
            <ellipse cx="132" cy="254" rx="8" ry="5" fill="#ffffff" stroke="#111827" strokeWidth="2.5" />
            <ellipse cx="188" cy="254" rx="8" ry="5" fill="#ffffff" stroke="#111827" strokeWidth="2.5" />
          </svg>
        </div>
      </div>

      {/* Bottom Section: Carousel Dots & Headline */}
      <div className="w-full text-center space-y-4 z-10 pt-4">
        
        {/* Pagination Dots [ ○  ●  ○ ] */}
        <div className="flex items-center justify-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-gray-300"></span>
          <span className="w-6 h-2 rounded-full bg-black"></span>
          <span className="w-2 h-2 rounded-full bg-gray-300"></span>
        </div>

        {/* Slogan Headline */}
        <h3 className="text-xl xl:text-2xl font-bold text-gray-900 tracking-tight max-w-sm mx-auto leading-snug">
          {headline}
        </h3>
      </div>
    </div>
  );
}
