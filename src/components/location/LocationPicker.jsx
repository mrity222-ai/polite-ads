import React, { useState } from 'react';
import { MapPin, Navigation, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * Reusable LocationPicker Component
 * Uses HTML5 Geolocation API with graceful fallbacks for denial, timeout, or manual entry.
 */
export default function LocationPicker({
  location,
  onChange,
  label = "Election Area GPS Location",
  required = false
}) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(location?.lat ? 'detected' : 'idle');
  const [errorMsg, setErrorMsg] = useState('');

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg("Geolocation is not supported by your browser. Please enter coordinates manually.");
      setStatus('error');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    setStatus('requesting');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          lat: position.coords.latitude.toFixed(4),
          lng: position.coords.longitude.toFixed(4),
          accuracy: Math.round(position.coords.accuracy || 25)
        };
        onChange(coords);
        setLoading(false);
        setStatus('detected');
      },
      (error) => {
        setLoading(false);
        setStatus('error');
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setErrorMsg("Location access denied. You can proceed with default constituency coordinates.");
            break;
          case error.POSITION_UNAVAILABLE:
            setErrorMsg("GPS position unavailable. Please ensure location is enabled on your device.");
            break;
          case error.TIMEOUT:
            setErrorMsg("Location request timed out. Please try again.");
            break;
          default:
            setErrorMsg("Unable to retrieve location. Default coordinates applied.");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-semibold text-gray-800">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        {status === 'detected' && (
          <span className="text-[11px] text-emerald-700 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Accuracy: ±{location?.accuracy || 25}m
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleGetCurrentLocation}
          disabled={loading}
          className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 border ${
            status === 'detected'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900 hover:bg-emerald-100'
              : 'bg-white border-gray-300 text-gray-800 hover:bg-gray-50'
          }`}
        >
          {loading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-600" />
              Detecting GPS Location...
            </>
          ) : status === 'detected' ? (
            <>
              <Navigation className="w-3.5 h-3.5 text-emerald-600" />
              GPS: {location?.lat}, {location?.lng} (Tap to Re-detect)
            </>
          ) : (
            <>
              <MapPin className="w-3.5 h-3.5 text-gray-500" />
              Use Current GPS Location
            </>
          )}
        </button>
      </div>

      {errorMsg && (
        <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-800 flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
