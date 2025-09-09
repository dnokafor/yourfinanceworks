import { Dimensions, Platform } from 'react-native';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Breakpoints for responsive design
export const breakpoints = {
  small: 375,
  medium: 768,
  large: 1024,
  extraLarge: 1200,
};

// Device type detection
export const isTablet = screenWidth >= breakpoints.medium;
export const isSmallDevice = screenWidth < breakpoints.small;
export const isLargeDevice = screenWidth >= breakpoints.large;

// Responsive scaling functions
export const scale = (size: number): number => {
  const standardWidth = 375; // iPhone 6/7/8 width
  const widthPercent = (size * screenWidth) / standardWidth;
  return Math.round(widthPercent);
};

export const verticalScale = (size: number): number => {
  const standardHeight = 667; // iPhone 6/7/8 height
  const heightPercent = (size * screenHeight) / standardHeight;
  return Math.round(heightPercent);
};

export const moderateScale = (size: number, factor: number = 0.5): number => {
  const scaled = scale(size);
  return scaled + (size - scaled) * factor;
};

// Spacing scale
export const spacing = {
  xs: scale(4),
  sm: scale(8),
  md: scale(16),
  lg: scale(24),
  xl: scale(32),
  xxl: scale(48),
};

// Font size scale
export const fontSize = {
  xs: scale(12),
  sm: scale(14),
  md: scale(16),
  lg: scale(18),
  xl: scale(20),
  xxl: scale(24),
  xxxl: scale(32),
};

// Border radius scale
export const borderRadius = {
  sm: scale(4),
  md: scale(8),
  lg: scale(12),
  xl: scale(16),
  xxl: scale(24),
  full: 9999,
};

// Shadow utilities for different platforms
export const shadow = {
  small: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
    },
    android: {
      elevation: 2,
    },
  }),
  medium: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
    },
    android: {
      elevation: 4,
    },
  }),
  large: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
    },
    android: {
      elevation: 8,
    },
  }),
};

// Grid system for responsive layouts
export const getGridColumns = (): number => {
  if (screenWidth >= breakpoints.extraLarge) return 4;
  if (screenWidth >= breakpoints.large) return 3;
  if (screenWidth >= breakpoints.medium) return 2;
  return 1;
};

export const getColumnWidth = (columns: number = getGridColumns()): number => {
  const totalPadding = spacing.md * 2; // left and right padding
  const gutter = spacing.sm * (columns - 1); // space between columns
  return (screenWidth - totalPadding - gutter) / columns;
};

// Safe area utilities
export const getSafeAreaInsets = () => {
  // This would typically use react-native-safe-area-context
  // For now, return default values
  return {
    top: Platform.OS === 'ios' ? 44 : 24,
    bottom: Platform.OS === 'ios' ? 34 : 24,
    left: 0,
    right: 0,
  };
};

// Orientation utilities
export const isPortrait = screenHeight > screenWidth;
export const isLandscape = screenWidth > screenHeight;

// Dynamic sizing based on orientation
export const getDynamicSize = (portraitSize: number, landscapeSize?: number): number => {
  if (!landscapeSize) {
    return portraitSize;
  }
  return isPortrait ? portraitSize : landscapeSize;
};

export default {
  scale,
  verticalScale,
  moderateScale,
  spacing,
  fontSize,
  borderRadius,
  shadow,
  getGridColumns,
  getColumnWidth,
  isTablet,
  isSmallDevice,
  isLargeDevice,
  isPortrait,
  isLandscape,
  getDynamicSize,
  breakpoints,
};
