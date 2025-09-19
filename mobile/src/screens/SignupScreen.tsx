import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import apiService from '../services/api';

interface SignupFormData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirmPassword: string;
  organization_name: string;
}

interface AvailabilityState {
  isChecking: boolean;
  isAvailable: boolean | null;
  error: string | null;
}

interface SignupScreenProps {
  onSignup: (formData: Omit<SignupFormData, 'confirmPassword'>) => Promise<void>;
  onNavigateToLogin: () => void;
}

const SignupScreen: React.FC<SignupScreenProps> = ({ onSignup, onNavigateToLogin }) => {
  const { t } = useTranslation();
  
  const [formData, setFormData] = useState<SignupFormData>({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    organization_name: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Availability checking state
  const [orgAvailability, setOrgAvailability] = useState<AvailabilityState>({
    isChecking: false,
    isAvailable: null,
    error: null,
  });
  const [emailAvailability, setEmailAvailability] = useState<AvailabilityState>({
    isChecking: false,
    isAvailable: null,
    error: null,
  });
  
  // Refs for debouncing
  const orgTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const emailTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced organization name availability check
  const checkOrgAvailability = useCallback(async (name: string) => {
    if (!name || name.length < 2) {
      setOrgAvailability({
        isChecking: false,
        isAvailable: null,
        error: name.length > 0 && name.length < 2 ? t('auth.signup.availability.org_min_length') : null,
      });
      return;
    }

    setOrgAvailability({
      isChecking: true,
      isAvailable: null,
      error: null,
    });

    try {
      const result = await apiService.checkOrganizationNameAvailability(name);
      setOrgAvailability({
        isChecking: false,
        isAvailable: result.available,
        error: null,
      });
    } catch (error: any) {
      setOrgAvailability({
        isChecking: false,
        isAvailable: null,
        error: t('auth.signup.availability.error_checking'),
      });
    }
  }, [t]);

  // Debounced email availability check
  const checkEmailAvailability = useCallback(async (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email) {
      setEmailAvailability({
        isChecking: false,
        isAvailable: null,
        error: null,
      });
      return;
    }

    if (!emailRegex.test(email)) {
      setEmailAvailability({
        isChecking: false,
        isAvailable: null,
        error: t('auth.signup.availability.valid_email'),
      });
      return;
    }

    setEmailAvailability({
      isChecking: true,
      isAvailable: null,
      error: null,
    });

    try {
      const result = await apiService.checkEmailAvailability(email);
      setEmailAvailability({
        isChecking: false,
        isAvailable: result.available,
        error: null,
      });
    } catch (error: any) {
      setEmailAvailability({
        isChecking: false,
        isAvailable: null,
        error: t('auth.signup.availability.error_checking'),
      });
    }
  }, [t]);

  const handleChange = (field: keyof SignupFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }

    // Handle availability checking with debouncing
    if (field === 'organization_name') {
      // Clear previous timeout
      if (orgTimeoutRef.current) {
        clearTimeout(orgTimeoutRef.current);
      }
      
      // Reset state immediately
      setOrgAvailability({
        isChecking: false,
        isAvailable: null,
        error: null,
      });
      
      // Set new timeout for checking
      orgTimeoutRef.current = setTimeout(() => {
        checkOrgAvailability(value.trim());
      }, 500); // 500ms debounce
    }

    if (field === 'email') {
      // Clear previous timeout
      if (emailTimeoutRef.current) {
        clearTimeout(emailTimeoutRef.current);
      }
      
      // Reset state immediately
      setEmailAvailability({
        isChecking: false,
        isAvailable: null,
        error: null,
      });
      
      // Set new timeout for checking
      emailTimeoutRef.current = setTimeout(() => {
        checkEmailAvailability(value.trim());
      }, 500); // 500ms debounce
    }
  };

  const validateForm = (): boolean => {
    // Check if all fields are filled
    if (!formData.organization_name.trim()) {
      setError('Organization name is required');
      return false;
    }
    if (!formData.first_name.trim()) {
      setError('First name is required');
      return false;
    }
    if (!formData.last_name.trim()) {
      setError('Last name is required');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (!formData.confirmPassword) {
      setError('Please confirm your password');
      return false;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }

    // Validate password strength
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    return true;
  };

  const handleSignup = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      // Remove confirmPassword from the data sent to API
      const { confirmPassword, ...signupData } = formData;
      await onSignup(signupData);
    } catch (error: any) {
      setError(error.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    Alert.alert('Coming Soon', 'Google SSO will be available soon!');
  };

  // Render availability status indicator
  const renderAvailabilityStatus = (availability: AvailabilityState, fieldType: 'org' | 'email') => {
    if (availability.isChecking) {
      return (
        <View style={styles.availabilityContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.availabilityTextChecking}>
            {t('auth.signup.availability.checking')}
          </Text>
        </View>
      );
    }

    if (availability.error) {
      return (
        <View style={styles.availabilityContainer}>
          <Ionicons name="warning" size={16} color="#e74c3c" />
          <Text style={styles.availabilityTextError}>{availability.error}</Text>
        </View>
      );
    }

    if (availability.isAvailable === true) {
      return (
        <View style={styles.availabilityContainer}>
          <Ionicons name="checkmark-circle" size={16} color="#27ae60" />
          <Text style={styles.availabilityTextAvailable}>
            {fieldType === 'org' 
              ? t('auth.signup.availability.org_available')
              : t('auth.signup.availability.email_available')
            }
          </Text>
        </View>
      );
    }

    if (availability.isAvailable === false) {
      return (
        <View style={styles.availabilityContainer}>
          <Ionicons name="close-circle" size={16} color="#e74c3c" />
          <Text style={styles.availabilityTextTaken}>
            {fieldType === 'org' 
              ? t('auth.signup.availability.org_taken')
              : t('auth.signup.availability.email_taken')
            }
          </Text>
          {fieldType === 'org' && (
            <Text style={styles.availabilityTip}>
              {t('auth.signup.tips.org_taken_tip')}
            </Text>
          )}
          {fieldType === 'email' && (
            <Text style={styles.availabilityTip}>
              {t('auth.signup.tips.email_taken_tip')}
            </Text>
          )}
        </View>
      );
    }

    return null;
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Text style={styles.title}>{t('auth.signup.title')}</Text>
          <Text style={styles.subtitle}>
            {t('auth.signup.subtitle')}
          </Text>
        </View>

        <View style={styles.form}>
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Organization Name */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>{t('auth.signup.organization_name')}</Text>
            <View style={styles.inputWithIcon}>
              <Ionicons name="business-outline" size={20} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                style={[styles.input, styles.inputWithIconPadding]}
                value={formData.organization_name}
                onChangeText={(value) => handleChange('organization_name', value)}
                placeholder={t('auth.signup.organization_placeholder')}
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>
            {renderAvailabilityStatus(orgAvailability, 'org')}
          </View>

          {/* First Name */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>{t('auth.signup.first_name')}</Text>
            <TextInput
              style={styles.input}
              value={formData.first_name}
              onChangeText={(value) => handleChange('first_name', value)}
              placeholder={t('auth.signup.first_name_placeholder')}
              autoCapitalize="words"
              autoCorrect={false}
            />
          </View>

          {/* Last Name */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>{t('auth.signup.last_name')}</Text>
            <TextInput
              style={styles.input}
              value={formData.last_name}
              onChangeText={(value) => handleChange('last_name', value)}
              placeholder={t('auth.signup.last_name_placeholder')}
              autoCapitalize="words"
              autoCorrect={false}
            />
          </View>

          {/* Email */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>{t('auth.signup.email_address')}</Text>
            <TextInput
              style={styles.input}
              value={formData.email}
              onChangeText={(value) => handleChange('email', value)}
              placeholder={t('auth.signup.email_placeholder')}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
            {renderAvailabilityStatus(emailAvailability, 'email')}
          </View>

          {/* Password */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>{t('auth.signup.password')}</Text>
            <View style={styles.passwordContainer}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                value={formData.password}
                onChangeText={(value) => handleChange('password', value)}
                placeholder={t('auth.signup.password_placeholder')}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                style={styles.eyeButton}
                onPress={() => setShowPassword(!showPassword)}
              >
                <Ionicons
                  name={showPassword ? 'eye-off' : 'eye'}
                  size={20}
                  color="#666"
                />
              </TouchableOpacity>
            </View>
          </View>

          {/* Confirm Password */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>{t('auth.signup.confirm_password')}</Text>
            <View style={styles.passwordContainer}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                value={formData.confirmPassword}
                onChangeText={(value) => handleChange('confirmPassword', value)}
                placeholder={t('auth.signup.confirm_password_placeholder')}
                secureTextEntry={!showConfirmPassword}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                style={styles.eyeButton}
                onPress={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                <Ionicons
                  name={showConfirmPassword ? 'eye-off' : 'eye'}
                  size={20}
                  color="#666"
                />
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handleSignup}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Create Account</Text>
            )}
          </TouchableOpacity>

          <View style={styles.loginContainer}>
            <Text style={styles.loginText}>Already have an account? </Text>
            <TouchableOpacity onPress={onNavigateToLogin}>
              <Text style={styles.loginLink}>Sign in</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>Or continue with</Text>
            <View style={styles.dividerLine} />
          </View>

          <TouchableOpacity
            style={styles.googleButton}
            onPress={handleGoogleSignup}
          >
            <Ionicons name="logo-google" size={20} color="#4285F4" />
            <Text style={styles.googleButtonText}>Sign up with Google</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  form: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  errorContainer: {
    backgroundColor: '#fee',
    borderColor: '#fcc',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
  },
  errorText: {
    color: '#c33',
    fontSize: 14,
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  inputWithIcon: {
    position: 'relative',
  },
  inputIcon: {
    position: 'absolute',
    left: 12,
    top: 12,
    zIndex: 1,
  },
  inputWithIconPadding: {
    paddingLeft: 40,
  },
  passwordContainer: {
    position: 'relative',
  },
  passwordInput: {
    paddingRight: 50,
  },
  eyeButton: {
    position: 'absolute',
    right: 12,
    top: 12,
    padding: 4,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  loginText: {
    fontSize: 14,
    color: '#666',
  },
  loginLink: {
    fontSize: 14,
    color: '#007AFF',
    textDecorationLine: 'underline',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#ddd',
  },
  dividerText: {
    marginHorizontal: 16,
    fontSize: 12,
    color: '#666',
    textTransform: 'uppercase',
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 16,
    backgroundColor: '#fff',
  },
  googleButtonText: {
    marginLeft: 8,
    fontSize: 16,
    color: '#333',
  },
  availabilityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingHorizontal: 4,
  },
  availabilityTextChecking: {
    fontSize: 12,
    color: '#007AFF',
    marginLeft: 6,
    fontStyle: 'italic',
  },
  availabilityTextAvailable: {
    fontSize: 12,
    color: '#27ae60',
    marginLeft: 6,
    fontWeight: '500',
  },
  availabilityTextTaken: {
    fontSize: 12,
    color: '#e74c3c',
    marginLeft: 6,
    fontWeight: '500',
    flex: 1,
  },
  availabilityTextError: {
    fontSize: 12,
    color: '#e74c3c',
    marginLeft: 6,
    flex: 1,
  },
  availabilityTip: {
    fontSize: 11,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 4,
    marginLeft: 22,
    lineHeight: 16,
  },
});

export default SignupScreen; 