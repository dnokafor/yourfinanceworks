import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import apiService, { CreateClientData, Client } from '../services/api';
import { SUPPORTED_CURRENCIES, getCurrencySymbol } from '../utils/currencyList';

interface NewClientScreenProps {
  onNavigateBack: () => void;
  onClientAdded: (client: Client) => void;
}

const NewClientScreen: React.FC<NewClientScreenProps> = ({ onNavigateBack, onClientAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    preferred_currency: 'USD',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showCurrencyModal, setShowCurrencyModal] = useState(false);
  const [tenantInfo, setTenantInfo] = useState<{ default_currency: string } | null>(null);

  // Load tenant info on mount
  useEffect(() => {
    const loadTenantInfo = async () => {
      try {
        const info = await apiService.getTenantInfo();
        setTenantInfo(info);
        // Set default currency from tenant if available
        if (info.default_currency && !formData.preferred_currency) {
          setFormData(prev => ({ ...prev, preferred_currency: info.default_currency }));
        }
      } catch (error) {
        console.warn('Failed to load tenant info:', error);
      }
    };

    loadTenantInfo();
  }, []);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setIsLoading(true);
      const clientData: CreateClientData = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim() || undefined,
        address: formData.address.trim() || undefined,
        preferred_currency: formData.preferred_currency,
      };

      const newClient = await apiService.createClient(clientData);
      onClientAdded(newClient);
      Alert.alert('Success', 'Client created successfully!');
      onNavigateBack();
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to create client');
    } finally {
      setIsLoading(false);
    }
  };

  const updateFormData = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={onNavigateBack}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.title}>New Client</Text>
        <TouchableOpacity
          style={[styles.saveButton, isLoading && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.saveButtonText}>Save</Text>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Name *</Text>
            <TextInput
              style={[styles.input, errors.name && styles.inputError]}
              value={formData.name}
              onChangeText={(value) => updateFormData('name', value)}
              placeholder="Enter client name"
              autoCapitalize="words"
            />
            {errors.name && <Text style={styles.errorText}>{errors.name}</Text>}
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Email *</Text>
            <TextInput
              style={[styles.input, errors.email && styles.inputError]}
              value={formData.email}
              onChangeText={(value) => updateFormData('email', value)}
              placeholder="Enter email address"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
            {errors.email && <Text style={styles.errorText}>{errors.email}</Text>}
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Phone</Text>
            <TextInput
              style={styles.input}
              value={formData.phone}
              onChangeText={(value) => updateFormData('phone', value)}
              placeholder="Enter phone number"
              keyboardType="phone-pad"
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Address</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={formData.address}
              onChangeText={(value) => updateFormData('address', value)}
              placeholder="Enter address"
              multiline
              numberOfLines={3}
              textAlignVertical="top"
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Preferred Currency</Text>
            <TouchableOpacity
              style={styles.currencySelector}
              onPress={() => setShowCurrencyModal(true)}
            >
              <View style={styles.currencyDisplay}>
                <Text style={styles.currencySymbol}>
                  {getCurrencySymbol(formData.preferred_currency)}
                </Text>
                <Text style={styles.currencyCode}>{formData.preferred_currency}</Text>
                <Ionicons name="chevron-down" size={16} color="#6B7280" />
              </View>
            </TouchableOpacity>
            <Text style={styles.fieldHint}>
              Select the currency this client prefers for transactions
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Currency Selection Modal */}
      <Modal
        visible={showCurrencyModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCurrencyModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <TouchableOpacity
            style={styles.modalBackdrop}
            activeOpacity={1}
            onPress={() => setShowCurrencyModal(false)}
          >
            <View style={styles.currencyModalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Select Currency</Text>
                <TouchableOpacity onPress={() => setShowCurrencyModal(false)}>
                  <Ionicons name="close" size={24} color="#6B7280" />
                </TouchableOpacity>
              </View>
              <View style={styles.currencyModalBody}>
                <Text style={styles.modalSubtitle}>
                  Choose the preferred currency for this client
                </Text>
                <ScrollView style={styles.currencyList} showsVerticalScrollIndicator={false}>
                  {SUPPORTED_CURRENCIES.map((currency, index) => (
                    <TouchableOpacity
                      key={currency.code}
                      style={[
                        styles.currencyOption,
                        formData.preferred_currency === currency.code && styles.currencyOptionSelected,
                        index === SUPPORTED_CURRENCIES.length - 1 && styles.currencyOptionLast
                      ]}
                      onPress={() => {
                        updateFormData('preferred_currency', currency.code);
                        setShowCurrencyModal(false);
                      }}
                    >
                      <View style={styles.currencyInfo}>
                        <View style={styles.currencySymbolContainer}>
                          <Text style={styles.currencySymbolText}>{currency.symbol}</Text>
                        </View>
                        <View style={styles.currencyDetails}>
                          <Text style={styles.currencyCode}>{currency.code}</Text>
                          <Text style={styles.currencyName}>{currency.name}</Text>
                        </View>
                      </View>
                      {formData.preferred_currency === currency.code && (
                        <Ionicons name="checkmark-circle" size={20} color="#10B981" />
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            </View>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  backButton: { padding: 8 },
  title: { fontSize: 18, fontWeight: 'bold', color: '#111827' },
  saveButton: { backgroundColor: '#007AFF', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  saveButtonDisabled: { backgroundColor: '#ccc' },
  saveButtonText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  content: { flex: 1 },
  form: { padding: 20 },
  inputContainer: { marginBottom: 20 },
  label: { fontSize: 14, fontWeight: '600', color: '#374151', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 8, padding: 12, fontSize: 16, backgroundColor: '#fff' },
  inputError: { borderColor: '#EF4444' },
  textArea: { height: 80 },
  errorText: { color: '#EF4444', fontSize: 12, marginTop: 4 },
  currencySelector: { borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 8, padding: 12, backgroundColor: '#fff' },
  currencyDisplay: { flexDirection: 'row', alignItems: 'center' },
  currencySymbol: { fontSize: 16, color: '#374151', marginRight: 8 },
  currencyCode: { fontSize: 16, color: '#374151', flex: 1 },
  fieldHint: { fontSize: 12, color: '#6B7280', marginTop: 4 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'flex-end' },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end' },
  currencyModalContent: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: '70%', minHeight: '50%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 20, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  modalTitle: { fontSize: 18, fontWeight: '600', color: '#111827' },
  currencyModalBody: { padding: 20, paddingBottom: 40 },
  modalSubtitle: { fontSize: 14, color: '#6B7280', marginBottom: 16, textAlign: 'center' },
  currencyList: { flex: 1 },
  currencyOption: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 16, paddingHorizontal: 4, borderBottomWidth: 1, borderBottomColor: '#F3F4F6' },
  currencyOptionSelected: { backgroundColor: '#F0F9FF', borderRadius: 8, marginHorizontal: -4, paddingHorizontal: 12 },
  currencyOptionLast: { borderBottomWidth: 0 },
  currencyInfo: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  currencySymbolContainer: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F3F4F6', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  currencySymbolText: { fontSize: 16, fontWeight: '600', color: '#374151' },
  currencyDetails: { flex: 1 },
  currencyName: { fontSize: 14, color: '#6B7280' },
});

export default NewClientScreen;