import React, { useEffect, useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
import { Label } from './label';
import { currencyApi } from '@/lib/api';

interface Currency {
  id: number;
  code: string;
  name: string;
  symbol: string;
  decimal_places: number;
  is_active: boolean;
}

interface CurrencySelectorProps {
  value: string;
  onValueChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  onCurrenciesLoaded?: () => void;
}

const FALLBACK_CURRENCIES: Currency[] = [
  { id: 1, code: 'USD', name: 'US Dollar', symbol: '$', decimal_places: 2, is_active: true },
];

export function CurrencySelector({
  value,
  onValueChange,
  label = "Currency",
  placeholder = "Select currency",
  disabled = false,
  className = "",
  onCurrenciesLoaded,
}: CurrencySelectorProps) {
  const [currencies, setCurrencies] = useState<Currency[]>(FALLBACK_CURRENCIES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurrencies = async () => {
      setLoading(true);
      try {
        const data = await currencyApi.getSupportedCurrencies();
        if (data.currencies && data.currencies.length > 0) {
          setCurrencies(data.currencies);
        } else {
          setError('No currencies available from API.');
        }
      } catch (err) {
        setError('API unavailable - using default currencies');
      } finally {
        setLoading(false);
        if (onCurrenciesLoaded) {
          onCurrenciesLoaded();
        }
      }
    };

    fetchCurrencies();
  }, [onCurrenciesLoaded]);

  const activeCurrencies = currencies.filter(c => c.is_active);

  const formatCurrency = (currency: Currency) => {
    return `${currency.code} - ${currency.name} (${currency.symbol})`;
  };

  if (loading) {
    return (
      <div className={className}>
        <Select disabled>
          <SelectTrigger>
            <SelectValue placeholder="Loading currencies..." />
          </SelectTrigger>
        </Select>
      </div>
    );
  }

  return (
    <div className={className}>
      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {activeCurrencies.map((currency) => (
            <SelectItem key={currency.code} value={currency.code}>
              {formatCurrency(currency)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && (
        <div className="text-xs text-yellow-600 mt-1">
          {error}
        </div>
      )}
    </div>
  );
}

export default CurrencySelector;
