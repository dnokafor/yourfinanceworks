import i18n from 'i18next';
import { logger } from '../utils/logger';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Import translation files via symbolic link
import en from './locales/en.json';
import es from './locales/es.json';
import fr from './locales/fr.json';

const resources = {
  en: {
    translation: en,
  },
  es: {
    translation: es,
  },
  fr: {
    translation: fr,
  },
};

const languageDetector = {
  type: 'languageDetector' as const,
  async: true,
  detect: async (callback: (lng: string) => void) => {
    try {
      // Try to get saved language from AsyncStorage
      const savedLanguage = await AsyncStorage.getItem('user-language');
      if (savedLanguage) {
        callback(savedLanguage);
        return;
      }
      
      // Fall back to device locale
      const deviceLanguage = Localization.getLocales?.()?.[0]?.languageCode || 'en';
      callback(deviceLanguage);
    } catch (error) {
      if (__DEV__) logger.error('Error detecting language', error);
      callback('en'); // fallback to English
    }
  },
  init: () => {},
  cacheUserLanguage: async (lng: string) => {
    try {
      await AsyncStorage.setItem('user-language', lng);
    } catch (error) {
      if (__DEV__) console.error('Error saving language:', error);
    }
  },
};

i18n
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // Set English as default language
    fallbackLng: 'en',
    debug: __DEV__,

    interpolation: {
      escapeValue: false, // React Native already escapes values
    },

    react: {
      useSuspense: false,
    },
  })
  .then(() => {
    logger.info('i18n initialized successfully');
    logger.info('Current language', i18n.language);
    logger.debug('Available resources', Object.keys(resources));
  })
  .catch((error) => {
    logger.error('i18n initialization failed', error);
  });

export default i18n;