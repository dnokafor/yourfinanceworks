// Custom currency symbols for cryptocurrencies and other custom currencies
const customCurrencySymbols: { [key: string]: { symbol: string; decimals: number } } = {
  'BTC': { symbol: '₿', decimals: 8 },
  'ETH': { symbol: 'Ξ', decimals: 18 },
  'XRP': { symbol: 'XRP', decimals: 6 },
  'SOL': { symbol: '◎', decimals: 9 },
};

export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  const upperCurrency = currency.toUpperCase();
  
  // Check if it's a custom currency
  if (customCurrencySymbols[upperCurrency]) {
    const info = customCurrencySymbols[upperCurrency];
    const formattedAmount = amount.toFixed(info.decimals);
    return `${info.symbol}${formattedAmount}`;
  }
  
  // Use Intl for standard currencies
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  } catch (error) {
    // Fallback for unknown currencies
    return `${amount.toFixed(2)} ${currency}`;
  }
};

export const formatCurrencyCompact = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(amount);
};

export const getCurrencySymbol = (currency: string = 'USD'): string => {
  const upperCurrency = currency.toUpperCase();
  
  // Check if it's a custom currency
  if (customCurrencySymbols[upperCurrency]) {
    return customCurrencySymbols[upperCurrency].symbol;
  }
  
  // Use Intl for standard currencies
  try {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    });
    
    // Extract the currency symbol from a formatted number
    const parts = formatter.formatToParts(1234.56);
    const symbolPart = parts.find(part => part.type === 'currency');
    return symbolPart ? symbolPart.value : currency;
  } catch (error) {
    // Fallback for unknown currencies
    return currency;
  }
}; 