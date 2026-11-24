import React, { useRef, useState } from 'react';
import { Upload, X, AlertCircle, RefreshCw } from 'lucide-react';

/**
 * Reusable ImageUploader Component with Client-side Format & Size Validation
 */
export default function ImageUploader({
  value,
  onChange,
  label = "Upload Image",
  aspectRatio = "square", // 'square' | 'wide'
  maxSizeMB = 5,
  helperText = "PNG, JPG, or WebP up to 5MB"
}) {
  const fileInputRef = useRef(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setErrorMsg('');

    // Check MIME type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setErrorMsg("Invalid file format. Please upload JPG, PNG, or WebP.");
      return;
    }

    // Check File Size
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setErrorMsg(`File size exceeds ${maxSizeMB}MB limit. Please upload a smaller image.`);
      return;
    }

    setIsProcessing(true);
    const reader = new FileReader();
    reader.onload = () => {
      onChange(reader.result, file);
      setIsProcessing(false);
    };
    reader.onerror = () => {
      setErrorMsg("Failed to read image file. Please try another image.");
      setIsProcessing(false);
    };
    reader.readAsDataURL(file);
  };

  const handleRemove = (e) => {
    e.stopPropagation();
    onChange(null, null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-semibold text-gray-800">{label}</label>

      {value ? (
        <div className="relative group rounded-2xl overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center">
          <img
            src={value}
            alt="Preview"
            className={`w-full object-cover ${aspectRatio === 'square' ? 'h-36 sm:h-40' : 'h-28 sm:h-32'}`}
          />
          <div className="absolute inset-0 bg-gray-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 rounded-xl bg-white text-gray-900 text-xs font-bold hover:bg-gray-100 transition shadow"
            >
              Change
            </button>
            <button
              type="button"
              onClick={handleRemove}
              className="p-1.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition shadow"
              title="Remove image"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="cursor-pointer border-2 border-dashed border-gray-200 hover:border-emerald-400 bg-[#fafafa] hover:bg-emerald-50/30 rounded-2xl p-5 text-center transition flex flex-col items-center justify-center space-y-2"
        >
          {isProcessing ? (
            <RefreshCw className="w-6 h-6 animate-spin text-emerald-600" />
          ) : (
            <div className="w-10 h-10 rounded-xl bg-gray-100 text-gray-500 flex items-center justify-center">
              <Upload className="w-5 h-5" />
            </div>
          )}
          <div>
            <p className="text-xs font-bold text-gray-800">Click to upload photo</p>
            <p className="text-[10px] text-gray-500 mt-0.5">{helperText}</p>
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        className="hidden"
      />

      {errorMsg && (
        <div className="p-2 rounded-xl bg-red-50 border border-red-200 text-[11px] text-red-700 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
