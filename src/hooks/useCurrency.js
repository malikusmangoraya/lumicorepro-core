import { useContext } from 'react';
import { CurrencyContext } from '../context/CurrencyContext';

/**
 * Hook to use currency context
 * Provides easy access to currency functions and state
 *
 * @returns {Object} Currency context value
 * @throws {Error} If used outside CurrencyProvider
 *
 * @example
 * const { currency, formatPrice, setCurrency } = useCurrency();
 * // Display: "Rs 5,000.00"
 * console.log(formatPrice(100, 'PKR'));
 */
export const useCurrency = () => {
  const context = useContext(CurrencyContext);

  if (!context) {
    throw new Error(
      'useCurrency must be used within CurrencyProvider. ' +
        'Wrap your component tree with <CurrencyProvider> in App.jsx'
    );
  }

  return context;
};
