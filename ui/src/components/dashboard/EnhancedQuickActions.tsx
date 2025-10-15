import React from 'react';
import { QuickActions } from './QuickActions';

/**
 * Enhanced version of QuickActions with professional styling
 * This is a wrapper that adds professional styling without causing refresh loops
 */
export function EnhancedQuickActions() {
  return (
    <div className="professional-enhancement">
      <style jsx>{`
        .professional-enhancement {
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
          backdrop-filter: blur(10px);
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          padding: 4px;
        }
        
        .professional-enhancement :global(.card) {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .professional-enhancement :global(button) {
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .professional-enhancement :global(button:hover) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
      `}</style>
      <QuickActions />
    </div>
  );
}