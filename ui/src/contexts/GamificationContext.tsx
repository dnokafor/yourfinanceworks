import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useGamification } from '@/hooks/useGamification';
import { CelebrationModal } from '@/components/gamification/CelebrationModal';
import type { 
  Achievement, 
  UserStreak, 
  GamificationResult,
  FinancialEvent 
} from '@/types/gamification';

interface LevelUpData {
  old_level: number;
  new_level: number;
  xp_to_next: number;
}

interface CelebrationData {
  type: 'achievement' | 'level_up' | 'streak_milestone';
  data: Achievement | LevelUpData | UserStreak;
  pointsAwarded?: number;
}

interface GamificationContextValue {
  // Celebration management
  showCelebration: (celebration: CelebrationData) => void;
  
  // Event processing with automatic celebrations
  processFinancialEvent: (event: FinancialEvent) => Promise<GamificationResult | null>;
  
  // Quick actions for common events
  trackExpense: (expenseData: any) => Promise<void>;
  createInvoice: (invoiceData: any) => Promise<void>;
  uploadReceipt: (receiptData: any) => Promise<void>;
  reviewBudget: () => Promise<void>;
  recordPayment: (paymentData: any) => Promise<void>;
}

const GamificationContext = createContext<GamificationContextValue | undefined>(undefined);

export function GamificationProvider({ children }: { children: React.ReactNode }) {
  const { processEvent, canShowGamification } = useGamification();
  const [currentCelebration, setCurrentCelebration] = useState<CelebrationData | null>(null);

  const showCelebration = useCallback((celebration: CelebrationData) => {
    if (canShowGamification) {
      setCurrentCelebration(celebration);
    }
  }, [canShowGamification]);

  const closeCelebration = useCallback(() => {
    setCurrentCelebration(null);
  }, []);

  const processFinancialEvent = useCallback(async (event: FinancialEvent): Promise<GamificationResult | null> => {
    if (!canShowGamification) return null;

    try {
      const result = await processEvent(event);
      
      if (result) {
        // Show celebrations based on the result
        if (result.level_up) {
          showCelebration({
            type: 'level_up',
            data: result.level_up,
            pointsAwarded: result.points_awarded
          });
        } else if (result.achievements_unlocked && result.achievements_unlocked.length > 0) {
          // Show celebration for the first achievement unlocked
          showCelebration({
            type: 'achievement',
            data: result.achievements_unlocked[0],
            pointsAwarded: result.achievements_unlocked[0].reward_xp
          });
        } else if (result.streaks_updated && result.streaks_updated.length > 0) {
          // Check if any streak hit a milestone
          const streakWithMilestone = result.streaks_updated.find(streak => {
            const milestones = [7, 30, 90, 365];
            return milestones.includes(streak.current_length);
          });
          
          if (streakWithMilestone) {
            showCelebration({
              type: 'streak_milestone',
              data: streakWithMilestone,
              pointsAwarded: Math.floor(result.points_awarded * 0.2) // Streak bonus portion
            });
          }
        }
      }
      
      return result;
    } catch (error) {
      console.error('Error processing financial event:', error);
      return null;
    }
  }, [canShowGamification, processEvent, showCelebration]);

  // Quick action helpers
  const trackExpense = useCallback(async (expenseData: any) => {
    await processFinancialEvent({
      user_id: 0, // Will be set by the API
      action_type: 'expense_added',
      timestamp: new Date().toISOString(),
      metadata: {
        amount: expenseData.amount,
        category: expenseData.category,
        has_receipt: !!expenseData.receipt,
        description: expenseData.description
      },
      category: expenseData.category,
      amount: expenseData.amount
    });
  }, [processFinancialEvent]);

  const createInvoice = useCallback(async (invoiceData: any) => {
    await processFinancialEvent({
      user_id: 0,
      action_type: 'invoice_created',
      timestamp: new Date().toISOString(),
      metadata: {
        amount: invoiceData.amount,
        client_id: invoiceData.client_id,
        items_count: invoiceData.items?.length || 0
      },
      amount: invoiceData.amount
    });
  }, [processFinancialEvent]);

  const uploadReceipt = useCallback(async (receiptData: any) => {
    await processFinancialEvent({
      user_id: 0,
      action_type: 'receipt_uploaded',
      timestamp: new Date().toISOString(),
      metadata: {
        expense_id: receiptData.expense_id,
        file_size: receiptData.file_size,
        file_type: receiptData.file_type
      }
    });
  }, [processFinancialEvent]);

  const reviewBudget = useCallback(async () => {
    await processFinancialEvent({
      user_id: 0,
      action_type: 'budget_reviewed',
      timestamp: new Date().toISOString(),
      metadata: {
        review_type: 'manual',
        categories_reviewed: 'all'
      }
    });
  }, [processFinancialEvent]);

  const recordPayment = useCallback(async (paymentData: any) => {
    await processFinancialEvent({
      user_id: 0,
      action_type: 'payment_recorded',
      timestamp: new Date().toISOString(),
      metadata: {
        amount: paymentData.amount,
        invoice_id: paymentData.invoice_id,
        payment_method: paymentData.payment_method
      },
      amount: paymentData.amount
    });
  }, [processFinancialEvent]);

  const contextValue: GamificationContextValue = {
    showCelebration,
    processFinancialEvent,
    trackExpense,
    createInvoice,
    uploadReceipt,
    reviewBudget,
    recordPayment
  };

  return (
    <GamificationContext.Provider value={contextValue}>
      {children}
      
      {/* Celebration Modal */}
      {currentCelebration && (
        <CelebrationModal
          isOpen={true}
          onClose={closeCelebration}
          type={currentCelebration.type}
          data={currentCelebration.data}
          pointsAwarded={currentCelebration.pointsAwarded}
        />
      )}
    </GamificationContext.Provider>
  );
}

export function useGamificationContext() {
  const context = useContext(GamificationContext);
  if (context === undefined) {
    throw new Error('useGamificationContext must be used within a GamificationProvider');
  }
  return context;
}

// Optional hook that returns null if gamification is not available
export function useGamificationContextOptional() {
  const context = useContext(GamificationContext);
  return context || null;
}