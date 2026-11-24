import React from 'react';

export default function SocialAuthButtons({ onSocialClick }) {
  const handleSocial = (provider) => {
    if (onSocialClick) {
      onSocialClick(provider);
    }
  };

  return (
    <div className="space-y-6">
      {/* Divider */}
      <div className="relative flex items-center justify-center">
        <div className="border-t border-gray-200 w-full"></div>
        <span className="bg-white px-4 text-xs text-gray-400 font-medium whitespace-nowrap">
          or continue with
        </span>
        <div className="border-t border-gray-200 w-full"></div>
      </div>

      {/* 3 Circular Black Buttons */}
      <div className="flex items-center justify-center gap-4">
        {/* Google Button */}
        <button
          type="button"
          onClick={() => handleSocial('Google')}
          title="Continue with Google"
          className="w-12 h-12 rounded-full bg-black hover:bg-neutral-800 text-white flex items-center justify-center transition shadow-xs hover:scale-105 active:scale-95"
        >
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z" />
          </svg>
        </button>

        {/* Apple Button */}
        <button
          type="button"
          onClick={() => handleSocial('Apple')}
          title="Continue with Apple"
          className="w-12 h-12 rounded-full bg-black hover:bg-neutral-800 text-white flex items-center justify-center transition shadow-xs hover:scale-105 active:scale-95"
        >
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.36c.62-.75 1.04-1.8 1.01-2.86-.96.04-2.13.64-2.79 1.41-.58.68-1.1 1.76-.96 2.8.07.01.18.02.26.02.86 0 1.87-.56 2.48-1.37z" />
          </svg>
        </button>

        {/* Facebook / Meta Button */}
        <button
          type="button"
          onClick={() => handleSocial('Facebook')}
          title="Continue with Facebook"
          className="w-12 h-12 rounded-full bg-black hover:bg-neutral-800 text-white flex items-center justify-center transition shadow-xs hover:scale-105 active:scale-95"
        >
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
