import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export type StatusType = 'draft' | 'pending' | 'paid' | 'overdue' | 'partially_paid' | 'completed' | 'failed' | 'cancelled' | 'processing' | 'recorded' | 'sent';

interface StatusIndicatorProps {
  status: StatusType;
  size?: 'small' | 'medium' | 'large';
  showText?: boolean;
  customText?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  size = 'medium',
  showText = true,
  customText,
}) => {
  const getStatusConfig = (status: StatusType) => {
    switch (status) {
      case 'paid':
      case 'completed':
        return {
          backgroundColor: '#D1FAE5',
          textColor: '#065F46',
          borderColor: '#10B981',
          icon: '✓',
        };
      case 'pending':
      case 'processing':
        return {
          backgroundColor: '#FEF3C7',
          textColor: '#92400E',
          borderColor: '#F59E0B',
          icon: '⏳',
        };
      case 'overdue':
      case 'failed':
        return {
          backgroundColor: '#FEE2E2',
          textColor: '#991B1B',
          borderColor: '#EF4444',
          icon: '⚠️',
        };
      case 'partially_paid':
        return {
          backgroundColor: '#E0F2FE',
          textColor: '#0C4A6E',
          borderColor: '#0284C7',
          icon: '⏱️',
        };
      case 'draft':
        return {
          backgroundColor: '#F3F4F6',
          textColor: '#374151',
          borderColor: '#6B7280',
          icon: '📝',
        };
      case 'sent':
        return {
          backgroundColor: '#E0F2FE',
          textColor: '#0C4A6E',
          borderColor: '#0284C7',
          icon: '📤',
        };
      case 'recorded':
        return {
          backgroundColor: '#ECFDF5',
          textColor: '#065F46',
          borderColor: '#10B981',
          icon: '📋',
        };
      case 'cancelled':
        return {
          backgroundColor: '#F3F4F6',
          textColor: '#6B7280',
          borderColor: '#9CA3AF',
          icon: '❌',
        };
      default:
        return {
          backgroundColor: '#F3F4F6',
          textColor: '#374151',
          borderColor: '#6B7280',
          icon: '•',
        };
    }
  };

  const formatStatusText = (status: StatusType): string => {
    if (customText) return customText;

    return status
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const config = getStatusConfig(status);
  const displayText = formatStatusText(status);

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          container: {
            paddingHorizontal: 8,
            paddingVertical: 4,
            borderRadius: 12,
          },
          text: { fontSize: 10 },
          icon: { fontSize: 10 },
        };
      case 'large':
        return {
          container: {
            paddingHorizontal: 16,
            paddingVertical: 8,
            borderRadius: 20,
          },
          text: { fontSize: 14 },
          icon: { fontSize: 14 },
        };
      default: // medium
        return {
          container: {
            paddingHorizontal: 12,
            paddingVertical: 6,
            borderRadius: 16,
          },
          text: { fontSize: 12 },
          icon: { fontSize: 12 },
        };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <View style={[
      styles.container,
      sizeStyles.container,
      { backgroundColor: config.backgroundColor, borderColor: config.borderColor }
    ]}>
      <Text style={[styles.icon, sizeStyles.icon]}>{config.icon}</Text>
      {showText && (
        <Text style={[
          styles.text,
          sizeStyles.text,
          { color: config.textColor }
        ]}>
          {displayText}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  icon: {
    marginRight: 4,
    fontWeight: '600',
  },
  text: {
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});

export default StatusIndicator;
