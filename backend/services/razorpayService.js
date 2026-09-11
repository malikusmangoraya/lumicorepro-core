/**
 * Legacy alias — re-exports from centralized payment service manager
 */
import razorpayService from './payment/razorpay.service.js';

export const createRazorpayOrder = (data) => razorpayService.createOrder(data);
export const verifyRazorpayPayment = (data) => razorpayService.verifyPayment(data);

export default razorpayService;