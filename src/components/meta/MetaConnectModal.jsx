import React, { useEffect, useState } from 'react';
import { X, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { integrationsApi } from '../../api/integrations';

export default function MetaConnectModal({ isOpen, onClose, onConnected, target = 'facebook' }) {
  const [assets, setAssets] = useState([]);
  const [selection, setSelection] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [authorized, setAuthorized] = useState(false);
  const [done, setDone] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const instagram = target === 'instagram';
  useEffect(() => {
    if (!isOpen) return undefined;
    let active = true;
    Promise.resolve().then(async () => {
      try {
        const status = await integrationsApi.getMetaStatus();
        if (!active) return;
        setAuthorized(status.authorization_present);
        if (status.authorization_present) {
          const response = await integrationsApi.getMetaAssets(target);
          if (!active) return;
          const choices = (response.available_pages || []).filter(page => !instagram || page.instagram_account_id);
          setAssets(choices);
          setSelection(choices[0]?.id || '');
        }
      } catch (e) { if (active) setError(e.message); }
      finally { if (active) setLoading(false); }
    });
    return () => { active = false; };
  }, [isOpen, target, instagram, attempt]);
  if (!isOpen) return null;
  const authorize = async () => {
    setBusy(true); setError('');
    try {
      const result = await integrationsApi.startMetaAuthorization(target);
      window.location.assign(result.authorization_url);
    } catch (e) { setError(e.message); setBusy(false); }
  };
  const select = async () => {
    setBusy(true); setError('');
    try {
      const response = instagram ? await integrationsApi.selectInstagramAccount(selection) : await integrationsApi.selectMetaPage(selection);
      setDone(response);
      onConnected?.(response);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <div className="fixed inset-0 z-50 bg-gray-950/60 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="meta-connect-title">
    <div className="bg-white rounded-3xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto space-y-4 shadow-2xl">
      <div className="flex justify-between items-center"><h2 id="meta-connect-title" className="font-bold text-lg">Connect {instagram ? 'Instagram' : 'Facebook Page'}</h2><button aria-label="Close connection dialog" onClick={onClose}><X className="w-5 h-5" /></button></div>
      {error && <div role="alert" className="bg-red-50 text-red-700 rounded-xl p-3 text-sm flex gap-2"><AlertCircle className="w-4 h-4 shrink-0" />{error}</div>}
      {done ? <p className="text-green-800 flex gap-2"><CheckCircle2 className="w-5 h-5" />{instagram ? `Instagram @${done.instagram_username} connected.` : `Facebook Page ${done.page_name} connected.`} Provider advertising approval remains separate.</p> : <>
        <p className="text-sm text-gray-600">{instagram ? 'Connect the professional Instagram account linked to your selected Facebook Page. Connect Facebook first.' : 'Authorize access on Facebook, then select a Page you manage. Your Facebook password and access token are never entered here.'}</p>
        {loading ? <p role="status" className="flex gap-2"><RefreshCw className="animate-spin w-4 h-4" />Checking available accounts…</p> : <>
          {assets.length > 0 ? <fieldset className="space-y-2"><legend className="font-semibold text-sm">Select {instagram ? 'Instagram account' : 'Facebook Page'}</legend>{assets.map(page => <label key={page.id} className="flex gap-3 border rounded-xl p-3 cursor-pointer"><input type="radio" name="meta-page" checked={selection === page.id} onChange={() => setSelection(page.id)} /><span>{instagram ? `@${page.instagram_username || page.instagram_account_id}` : page.name}<span className="block text-xs text-gray-500">{instagram ? `Linked Page: ${page.name}` : `Page ID: ${page.id}`}</span></span></label>)}</fieldset> : authorized && <p className="text-sm text-amber-800">{instagram ? 'No eligible Instagram account was returned for your selected Page. Check its professional account link and granted permissions.' : 'No managed Pages were returned. Grant Page access on Facebook and authorize again.'}</p>}
          <div className="flex gap-2 flex-wrap">
            <button disabled={busy} onClick={authorize} className="bg-blue-600 text-white rounded-full px-5 py-2 disabled:opacity-50">{busy ? 'Connecting…' : authorized ? 'Authorize again on Facebook' : 'Continue with Facebook'}</button>
            {assets.length > 0 && <button disabled={busy || !selection} onClick={select} className="bg-emerald-600 text-white rounded-full px-5 py-2 disabled:opacity-50">Connect selected {instagram ? 'Instagram account' : 'Page'}</button>}
            <button disabled={busy} onClick={() => { setError(''); setLoading(true); setAttempt(n => n + 1); }} className="underline px-2">Refresh</button>
          </div>
        </>}
      </>}
      <p className="text-xs text-gray-500">Only the selected account is linked. Connecting does not publish an ad or start spending.</p>
    </div>
  </div>;
}
