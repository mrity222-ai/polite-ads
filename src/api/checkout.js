import { integrationsApi } from './integrations';

let sdkPromise;
function loadCheckout() {
  if (window.Razorpay) return Promise.resolve();
  if (!sdkPromise) sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    const timeout = window.setTimeout(() => { script.remove(); sdkPromise = null; reject(new Error('Payment checkout timed out. Please retry.')); }, 30000);
    script.onload = () => { window.clearTimeout(timeout); if (window.Razorpay) resolve(); else { sdkPromise = null; reject(new Error('Payment checkout is unavailable.')); } };
    script.onerror = () => { window.clearTimeout(timeout); script.remove(); sdkPromise = null; reject(new Error('Could not load secure payment checkout.')); };
    document.head.appendChild(script);
  });
  return sdkPromise;
}

export async function checkout(itemType, itemId, amountPaise = null) {
  const order = await integrationsApi.createPaymentOrder(itemType, itemId, amountPaise);
  if (order.mock) throw new Error('Gateway simulation mode: no real checkout or payment has been made. Configure Razorpay test credentials and disable gateway mock mode to test checkout.');
  if (!order.key_id) throw new Error('Payment provider key is not configured.');
  await loadCheckout();
  return new Promise((resolve, reject) => {
    let completed = false;
    const fail = error => { if (!completed) { completed = true; reject(error); } };
    const widget = new window.Razorpay({
      key: order.key_id, amount: order.amount_paise, currency: order.currency,
      order_id: order.razorpay_order_id, name: 'PolitiAds', description: itemType === 'campaign_budget' ? 'Campaign funding' : 'Subscription',
      prefill: { name: order.user_name || '', email: order.user_email || '', contact: order.user_mobile || '' },
      handler: async response => {
        if (completed) return;
        completed = true;
        try { resolve(await integrationsApi.verifyPayment(response.razorpay_order_id, response.razorpay_payment_id, response.razorpay_signature)); }
        catch (e) { reject(new Error(`Payment confirmation pending: ${e.message}. Refresh payment history before paying again.`)); }
      },
      modal: { ondismiss: () => fail(new Error('Checkout closed. Check payment history before retrying if your bank was charged.')) },
      theme: { color: '#047857' },
    });
    widget.on('payment.failed', response => { widget.close(); fail(new Error(response.error?.description || 'Payment failed.')); });
    widget.open();
  });
}
