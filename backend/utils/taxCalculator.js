/**
 * Tax Calculator - Regional tax rate computation
 * Supports VAT (Europe), GST (India/Australia), Sales Tax (US/Canada), etc.
 * 
 * Usage:
 * const { taxRate, taxAmount, totalWithTax } = calculateTax({
 *   amount: 100,
 *   country: 'PK',
 *   state: null, // US only
 * });
 */

const TAX_RATES = {
  // Europe (VAT - Value Added Tax)
  'AT': { rate: 20, type: 'VAT', name: 'Austria' },
  'BE': { rate: 21, type: 'VAT', name: 'Belgium' },
  'BG': { rate: 20, type: 'VAT', name: 'Bulgaria' },
  'HR': { rate: 25, type: 'VAT', name: 'Croatia' },
  'CY': { rate: 19, type: 'VAT', name: 'Cyprus' },
  'CZ': { rate: 21, type: 'VAT', name: 'Czech Republic' },
  'DK': { rate: 25, type: 'VAT', name: 'Denmark' },
  'EE': { rate: 20, type: 'VAT', name: 'Estonia' },
  'FI': { rate: 24, type: 'VAT', name: 'Finland' },
  'FR': { rate: 20, type: 'VAT', name: 'France' },
  'DE': { rate: 19, type: 'VAT', name: 'Germany' },
  'GR': { rate: 24, type: 'VAT', name: 'Greece' },
  'HU': { rate: 27, type: 'VAT', name: 'Hungary' },
  'IE': { rate: 23, type: 'VAT', name: 'Ireland' },
  'IT': { rate: 22, type: 'VAT', name: 'Italy' },
  'LV': { rate: 21, type: 'VAT', name: 'Latvia' },
  'LT': { rate: 21, type: 'VAT', name: 'Lithuania' },
  'LU': { rate: 17, type: 'VAT', name: 'Luxembourg' },
  'MT': { rate: 18, type: 'VAT', name: 'Malta' },
  'NL': { rate: 21, type: 'VAT', name: 'Netherlands' },
  'PL': { rate: 23, type: 'VAT', name: 'Poland' },
  'PT': { rate: 23, type: 'VAT', name: 'Portugal' },
  'RO': { rate: 19, type: 'VAT', name: 'Romania' },
  'SK': { rate: 20, type: 'VAT', name: 'Slovakia' },
  'SI': { rate: 22, type: 'VAT', name: 'Slovenia' },
  'ES': { rate: 21, type: 'VAT', name: 'Spain' },
  'SE': { rate: 25, type: 'VAT', name: 'Sweden' },
  'GB': { rate: 20, type: 'VAT', name: 'United Kingdom' },
  'CH': { rate: 7.7, type: 'VAT', name: 'Switzerland' },
  'NO': { rate: 25, type: 'VAT', name: 'Norway' },

  // South Asia (GST)
  'IN': { rate: 18, type: 'GST', name: 'India', note: 'varies 5-28%' },
  'PK': { rate: 17, type: 'GST', name: 'Pakistan' },
  'BD': { rate: 15, type: 'VAT', name: 'Bangladesh' },
  'LK': { rate: 15, type: 'VAT', name: 'Sri Lanka' },

  // Middle East (VAT)
  'AE': { rate: 5, type: 'VAT', name: 'United Arab Emirates' },
  'SA': { rate: 15, type: 'VAT', name: 'Saudi Arabia' },
  'KW': { rate: 0, type: 'VAT', name: 'Kuwait', note: 'No VAT' },
  'QA': { rate: 5, type: 'VAT', name: 'Qatar' },
  'BH': { rate: 10, type: 'VAT', name: 'Bahrain' },
  'OM': { rate: 9, type: 'VAT', name: 'Oman' },
  'JO': { rate: 16, type: 'VAT', name: 'Jordan' },
  'LB': { rate: 10, type: 'VAT', name: 'Lebanon' },

  // Asia-Pacific
  'AU': { rate: 10, type: 'GST', name: 'Australia' },
  'NZ': { rate: 15, type: 'GST', name: 'New Zealand' },
  'SG': { rate: 8, type: 'GST', name: 'Singapore' },
  'MY': { rate: 6, type: 'SST', name: 'Malaysia' },
  'TH': { rate: 7, type: 'VAT', name: 'Thailand' },
  'PH': { rate: 12, type: 'VAT', name: 'Philippines' },
  'ID': { rate: 11, type: 'VAT', name: 'Indonesia' },
  'VN': { rate: 10, type: 'VAT', name: 'Vietnam' },
  'JP': { rate: 10, type: 'VAT', name: 'Japan' },
  'KR': { rate: 10, type: 'VAT', name: 'South Korea' },
  'HK': { rate: 0, type: 'VAT', name: 'Hong Kong', note: 'No VAT' },
  'TW': { rate: 5, type: 'VAT', name: 'Taiwan' },

  // Americas
  'CA': { rate: 5, type: 'GST', name: 'Canada', note: 'PST/HST varies 5-15%' },
  'MX': { rate: 16, type: 'VAT', name: 'Mexico' },
  'BR': { rate: 17, type: 'VAT', name: 'Brazil', note: 'varies 7-28%' },
  'AR': { rate: 21, type: 'VAT', name: 'Argentina' },
  'CL': { rate: 19, type: 'VAT', name: 'Chile' },
  'CO': { rate: 19, type: 'VAT', name: 'Colombia' },
  'PE': { rate: 18, type: 'VAT', name: 'Peru' },

  // USA (State-based Sales Tax - examples)
  'US': { rate: 0, type: 'Sales Tax', name: 'United States', note: 'See state rates' },
};

// US State Sales Tax Rates (approximate, subject to change)
const US_STATE_TAX_RATES = {
  'AL': 4.0, 'AK': 0, 'AZ': 5.6, 'AR': 6.5, 'CA': 7.25,
  'CO': 2.9, 'CT': 6.35, 'DE': 0, 'FL': 6.0, 'GA': 4.0,
  'HI': 4.0, 'ID': 6.0, 'IL': 6.25, 'IN': 7.0, 'IA': 6.0,
  'KS': 5.7, 'KY': 6.0, 'LA': 4.45, 'ME': 5.5, 'MD': 6.0,
  'MA': 6.25, 'MI': 6.0, 'MN': 6.875, 'MS': 7.0, 'MO': 4.225,
  'MT': 0, 'NE': 5.5, 'NV': 6.85, 'NH': 0, 'NJ': 6.625,
  'NM': 5.125, 'NY': 4.0, 'NC': 4.75, 'ND': 5.0, 'OH': 5.75,
  'OK': 4.5, 'OR': 0, 'PA': 6.0, 'RI': 7.0, 'SC': 6.0,
  'SD': 4.2, 'TN': 7.0, 'TX': 6.25, 'UT': 4.85, 'VT': 6.0,
  'VA': 5.3, 'WA': 6.5, 'WV': 6.0, 'WI': 5.0, 'WY': 4.0,
};

/**
 * Calculate tax based on country and optional state
 * @param {Object} options
 * @param {number} options.amount - Amount in currency
 * @param {string} options.country - ISO 3166-1 alpha-2 country code (e.g., 'PK', 'US', 'DE')
 * @param {string} options.state - State/Province code (for US: 'CA', 'NY', etc.)
 * @param {string} options.billingAddress - Full billing address for EU VAT reversal checks
 * @returns {Object} Tax calculation result
 */
export const calculateTax = ({ amount, country, state = null, billingAddress = null, currency = 'USD' }) => {
  if (!amount || amount <= 0) {
    return {
      amount: 0,
      rate: 0,
      type: 'NONE',
      country,
      currency: currency.toUpperCase(),
      inclusive: false,
      total: 0,
    };
  }

  let taxRate;
  let taxType;
  let note = '';
  let isInclusive = false;

  // Handle USA state-based tax
  if (country === 'US' && state) {
    taxRate = US_STATE_TAX_RATES[state.toUpperCase()] || 0;
    taxType = 'Sales Tax';
  } else if (TAX_RATES[country]) {
    const countryTax = TAX_RATES[country];
    taxRate = countryTax.rate;
    taxType = countryTax.type;
    note = countryTax.note || '';

    // EU VAT is typically inclusive (prices shown include tax)
    isInclusive = countryTax.type === 'VAT' && country !== 'GB';
  } else {
    // Unknown country - no tax
    taxRate = 0;
    taxType = 'UNKNOWN';
  }

  const taxAmount = (amount * taxRate) / 100;
  const totalWithTax = amount + taxAmount;

  return {
    taxRate,
    taxAmount: parseFloat(taxAmount.toFixed(2)),
    amount: parseFloat(amount.toFixed(2)),
    total: parseFloat(totalWithTax.toFixed(2)),
    type: taxType,
    country,
    state: state || null,
    isInclusive, // True if tax is included in displayed price
    note,
    breakdown: {
      subtotal: parseFloat(amount.toFixed(2)),
      tax: parseFloat(taxAmount.toFixed(2)),
      total: parseFloat(totalWithTax.toFixed(2)),
    },
  };
};

/**
 * Get tax information for a country
 * @param {string} country - ISO 3166-1 alpha-2 country code
 * @returns {Object|null} Tax info or null if not found
 */
export const getTaxInfo = (country) => {
  return TAX_RATES[country] || null;
};

/**
 * Get all available country tax rates
 * @returns {Object} All tax rates
 */
export const getAllTaxRates = () => {
  return TAX_RATES;
};

/**
 * Get US state tax rates
 * @returns {Object} US state tax rates
 */
export const getUSStateTaxRates = () => {
  return US_STATE_TAX_RATES;
};

/**
 * Format tax for display
 * @param {Object} taxResult - Result from calculateTax()
 * @param {string} currency - Currency symbol
 * @returns {string} Formatted tax string
 */
export const formatTaxDisplay = (taxResult, currency = '$') => {
  if (taxResult.taxAmount === 0) return 'No tax';
  return `${currency}${taxResult.taxAmount.toFixed(2)} (${taxResult.type}: ${taxResult.taxRate}%)`;
};
