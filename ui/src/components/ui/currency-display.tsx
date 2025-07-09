import React, { useState, useEffect } from 'react';
import { currencyApi } from '@/lib/api';

interface CurrencyDisplayProps {
  amount: number;
  currency: string;
  className?: string;
  showCode?: boolean;
}

interface CurrencyInfo {
  symbol: string;
  decimals: number;
}

// Common currency symbols (fallback)
const fallbackCurrencySymbols: { [key: string]: { symbol: string; decimals: number } } = {
  'USD': { symbol: '$', decimals: 2 },
  'EUR': { symbol: '€', decimals: 2 },
  'GBP': { symbol: '£', decimals: 2 },
  'CAD': { symbol: 'C$', decimals: 2 },
  'AUD': { symbol: 'A$', decimals: 2 },
  'JPY': { symbol: '¥', decimals: 0 },
  'CHF': { symbol: 'CHF', decimals: 2 },
  'CNY': { symbol: '¥', decimals: 2 },
  'INR': { symbol: '₹', decimals: 2 },
  'BRL': { symbol: 'R$', decimals: 2 }
};

export function CurrencyDisplay({ 
  amount, 
  currency, 
  className = "", 
  showCode = false 
}: CurrencyDisplayProps) {
  const [currencyInfo, setCurrencyInfo] = useState<CurrencyInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCurrencyInfo = async () => {
      try {
        const response = await currencyApi.getSupportedCurrencies();
        const currencies = response.currencies || [];
        const foundCurrency = currencies.find(c => c.code === currency.toUpperCase());
        
        if (foundCurrency) {
          setCurrencyInfo({
            symbol: foundCurrency.symbol,
            decimals: foundCurrency.decimal_places
          });
        } else {
          // Use fallback for traditional currencies
          const fallback = fallbackCurrencySymbols[currency.toUpperCase()];
          setCurrencyInfo(fallback || { symbol: currency, decimals: 2 });
        }
      } catch (error) {
        console.error('Failed to fetch currency info:', error);
        // Use fallback
        const fallback = fallbackCurrencySymbols[currency.toUpperCase()];
        setCurrencyInfo(fallback || { symbol: currency, decimals: 2 });
      } finally {
        setLoading(false);
      }
    };

    fetchCurrencyInfo();
  }, [currency]);

  const formatCurrency = (amount: number, currencyCode: string) => {
    if (loading || !currencyInfo) {
      // Show loading state or fallback
      const fallback = fallbackCurrencySymbols[currencyCode.toUpperCase()];
      const info = fallback || { symbol: currencyCode, decimals: 2 };
      const formattedAmount = amount.toFixed(info.decimals);
      return `${info.symbol}${formattedAmount}`;
    }
    
    const formattedAmount = amount.toFixed(currencyInfo.decimals);
    const symbol = currencyInfo.symbol;
    
    if (showCode) {
      return `${symbol}${formattedAmount} ${currencyCode}`;
    }
    return `${symbol}${formattedAmount}`;
  };

  return (
    <span className={className}>
      {formatCurrency(amount, currency)}
    </span>
  );
}

export default CurrencyDisplay; 