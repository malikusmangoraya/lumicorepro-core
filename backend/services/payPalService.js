/**
 * Legacy alias — re-exports from centralized payment service manager
 */
import paypalService from './payment/paypal.service.js';

export const createPayPalOrder = (data) => paypalService.createOrder(data);
export const capturePayPalOrder = (data) => paypalService.captureOrder(data);
export const verifyPayPalPayment = (data) => paypalService.captureOrder(data);

export default paypalService;