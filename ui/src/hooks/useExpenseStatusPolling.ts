import { useEffect, useRef } from 'react';
import { expenseApi } from '@/lib/api';

export function useExpenseStatusPolling() {
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const trackedExpenses = useRef<Set<number>>(new Set());

  const startPolling = (expenseId: number) => {
    trackedExpenses.current.add(expenseId);
    
    if (!pollingRef.current) {
      pollingRef.current = setInterval(async () => {
        const addNotification = (window as any).addAINotification;
        if (!addNotification) return;

        for (const id of trackedExpenses.current) {
          try {
            const expense = await expenseApi.getExpense(id);
            console.log(`Expense ${id} status:`, expense.analysis_status);
            if (expense.analysis_status === 'done' || expense.analysis_status === 'Done') {
              addNotification('success', 'Expense Analysis Complete', `Expense #${id} has been analyzed and processed.`);
              trackedExpenses.current.delete(id);
            } else if (expense.analysis_status === 'failed' || expense.analysis_status === 'Failed') {
              addNotification('error', 'Expense Analysis Failed', `Expense #${id} analysis failed.`);
              trackedExpenses.current.delete(id);
            }
          } catch (e) {
            console.error(`Error polling expense ${id}:`, e);
            trackedExpenses.current.delete(id);
          }
        }

        if (trackedExpenses.current.size === 0 && pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }, 5000);
    }
  };

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  return { startPolling };
}