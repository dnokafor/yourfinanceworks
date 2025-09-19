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
import apiService, { Client, ClientNote } from '../services/api';
import { SUPPORTED_CURRENCIES, getCurrencySymbol } from '../utils/currencyList';

interface EditClientScreenProps {
  client: Client;
  onNavigateBack: () => void;
  onClientUpdated: (client: Client) => void;
  onClientDeleted: (clientId: number) => void;
}

const EditClientScreen: React.FC<EditClientScreenProps> = ({ 
  client, 
  onNavigateBack, 
  onClientUpdated, 
  onClientDeleted 
}) => {
  const [formData, setFormData] = useState({
    name: client.name || '',
    email: client.email || '',
    phone: client.phone || '',
    address: client.address || '',
    preferred_currency: client.preferred_currency || 'USD',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showCurrencyModal, setShowCurrencyModal] = useState(false);
  const [tenantInfo, setTenantInfo] = useState<{ default_currency: string } | null>(null);

  // Notes functionality
  const [clientNotes, setClientNotes] = useState<ClientNote[]>([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [showAddNoteModal, setShowAddNoteModal] = useState(false);
  const [showEditNoteModal, setShowEditNoteModal] = useState(false);
  const [selectedNote, setSelectedNote] = useState<ClientNote | null>(null);
  const [newNoteText, setNewNoteText] = useState('');
  const [editNoteText, setEditNoteText] = useState('');

  // Load tenant info and client notes on mount
  useEffect(() => {
    const loadTenantInfo = async () => {
      try {
        const info = await apiService.getTenantInfo();
        setTenantInfo(info);
      } catch (error) {
        console.warn('Failed to load tenant info:', error);
      }
    };

    const loadClientNotes = async () => {
      try {
        setNotesLoading(true);
        const notes = await apiService.getClientNotes(client.id);
        setClientNotes(notes.sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ));
      } catch (error) {
        console.warn('Failed to load client notes:', error);
      } finally {
        setNotesLoading(false);
      }
    };

    loadTenantInfo();
    loadClientNotes();
  }, [client.id]);

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
      const clientData = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim() || undefined,
        address: formData.address.trim() || undefined,
        preferred_currency: formData.preferred_currency,
      };

      const updatedClient = await apiService.updateClient(client.id, clientData);
      onClientUpdated(updatedClient);
      Alert.alert('Success', 'Client updated successfully!');
      onNavigateBack();
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to update client');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Client',
      `Are you sure you want to delete ${client.name}? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsDeleting(true);
              await apiService.deleteClient(client.id);
              onClientDeleted(client.id);
              Alert.alert('Success', 'Client deleted successfully!');
              onNavigateBack();
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to delete client');
            } finally {
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  };

  const updateFormData = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Note management functions
  const handleAddNote = async () => {
    if (!newNoteText.trim()) return;

    try {
      const newNote = await apiService.createClientNote(client.id, { note: newNoteText.trim() });
      setClientNotes(prev => [newNote, ...prev]);
      setNewNoteText('');
      setShowAddNoteModal(false);
      Alert.alert('Success', 'Note added successfully!');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add note');
    }
  };

  const handleEditNote = async () => {
    if (!selectedNote || !editNoteText.trim()) return;

    try {
      const updatedNote = await apiService.updateClientNote(
        selectedNote.client_id,
        selectedNote.id,
        { note: editNoteText.trim() }
      );
      setClientNotes(prev => prev.map(note =>
        note.id === selectedNote.id ? updatedNote : note
      ));
      setEditNoteText('');
      setSelectedNote(null);
      setShowEditNoteModal(false);
      Alert.alert('Success', 'Note updated successfully!');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to update note');
    }
  };

  const handleDeleteNote = (note: ClientNote) => {
    Alert.alert(
      'Delete Note',
      'Are you sure you want to delete this note?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiService.deleteClientNote(note.client_id, note.id);
              setClientNotes(prev => prev.filter(n => n.id !== note.id));
              Alert.alert('Success', 'Note deleted successfully!');
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to delete note');
            }
          },
        },
      ]
    );
  };

  const openEditNoteModal = (note: ClientNote) => {
    setSelectedNote(note);
    setEditNoteText(note.note);
    setShowEditNoteModal(true);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={onNavigateBack}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.title}>Edit Client</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={[styles.deleteButton, isDeleting && styles.deleteButtonDisabled]}
            onPress={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="trash-outline" size={16} color="#fff" />
            )}
          </TouchableOpacity>
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

          {/* Client Notes Section */}
          <View style={styles.notesSection}>
            <View style={styles.notesHeader}>
              <Text style={styles.sectionTitle}>Client Notes</Text>
              <TouchableOpacity
                style={styles.addNoteButton}
                onPress={() => setShowAddNoteModal(true)}
              >
                <Ionicons name="add" size={20} color="#007AFF" />
                <Text style={styles.addNoteText}>Add Note</Text>
              </TouchableOpacity>
            </View>

            {notesLoading ? (
              <View style={styles.notesLoading}>
                <ActivityIndicator size="small" color="#007AFF" />
                <Text style={styles.loadingText}>Loading notes...</Text>
              </View>
            ) : clientNotes.length === 0 ? (
              <View style={styles.notesEmpty}>
                <Ionicons name="document-text-outline" size={48} color="#9CA3AF" />
                <Text style={styles.emptyText}>No notes yet</Text>
                <Text style={styles.emptySubtext}>Add notes to keep track of important information about this client</Text>
              </View>
            ) : (
              <View style={styles.notesList}>
                {clientNotes.map((note) => (
                  <View key={note.id} style={styles.noteCard}>
                    <View style={styles.noteHeader}>
                      <Text style={styles.noteDate}>
                        {formatDate(note.created_at)}
                      </Text>
                      <View style={styles.noteActions}>
                        <TouchableOpacity
                          style={styles.actionButton}
                          onPress={() => openEditNoteModal(note)}
                        >
                          <Ionicons name="pencil" size={16} color="#007AFF" />
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={[styles.actionButton, styles.noteDeleteButton]}
                          onPress={() => handleDeleteNote(note)}
                        >
                          <Ionicons name="trash" size={16} color="#EF4444" />
                        </TouchableOpacity>
                      </View>
                    </View>
                    <Text style={styles.noteText}>{note.note}</Text>
                    {note.updated_at !== note.created_at && (
                      <Text style={styles.updatedText}>
                        Updated: {formatDate(note.updated_at)}
                      </Text>
                    )}
                  </View>
                ))}
              </View>
            )}
          </View>

          <View style={styles.clientInfo}>
            <Text style={styles.infoLabel}>Client Information</Text>
            <View style={styles.infoRow}>
              <Text style={styles.infoKey}>Balance:</Text>
              <Text style={styles.infoValue}>${client.balance?.toFixed(2) || '0.00'}</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoKey}>Paid Amount:</Text>
              <Text style={styles.infoValue}>${client.paid_amount?.toFixed(2) || '0.00'}</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoKey}>Created:</Text>
              <Text style={styles.infoValue}>{new Date(client.created_at).toLocaleDateString()}</Text>
            </View>
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

      {/* Add Note Modal */}
      <Modal
        visible={showAddNoteModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAddNoteModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <TouchableOpacity
            style={styles.modalBackdrop}
            activeOpacity={1}
            onPress={() => setShowAddNoteModal(false)}
          >
            <View style={styles.noteModalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Add New Note</Text>
                <TouchableOpacity onPress={() => setShowAddNoteModal(false)}>
                  <Ionicons name="close" size={24} color="#6B7280" />
                </TouchableOpacity>
              </View>
              <View style={styles.modalBody}>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  placeholder="Enter your note..."
                  value={newNoteText}
                  onChangeText={setNewNoteText}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                />
                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={[styles.button, styles.cancelButton]}
                    onPress={() => setShowAddNoteModal(false)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.modalSaveButton]}
                    onPress={handleAddNote}
                    disabled={!newNoteText.trim()}
                  >
                    <Text style={styles.saveButtonText}>Add Note</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      </Modal>

      {/* Edit Note Modal */}
      <Modal
        visible={showEditNoteModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowEditNoteModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <TouchableOpacity
            style={styles.modalBackdrop}
            activeOpacity={1}
            onPress={() => setShowEditNoteModal(false)}
          >
            <View style={styles.noteModalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Edit Note</Text>
                <TouchableOpacity onPress={() => setShowEditNoteModal(false)}>
                  <Ionicons name="close" size={24} color="#6B7280" />
                </TouchableOpacity>
              </View>
              <View style={styles.modalBody}>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  placeholder="Enter your note..."
                  value={editNoteText}
                  onChangeText={setEditNoteText}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                />
                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={[styles.button, styles.cancelButton]}
                    onPress={() => setShowEditNoteModal(false)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.modalSaveButton]}
                    onPress={handleEditNote}
                    disabled={!editNoteText.trim()}
                  >
                    <Text style={styles.saveButtonText}>Update Note</Text>
                  </TouchableOpacity>
                </View>
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
  headerActions: { flexDirection: 'row', gap: 8 },
  deleteButton: { backgroundColor: '#EF4444', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  deleteButtonDisabled: { backgroundColor: '#ccc' },
  saveButton: { backgroundColor: '#007AFF', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  saveButtonDisabled: { backgroundColor: '#ccc' },
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
  notesSection: { marginTop: 20, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#E5E7EB' },
  notesHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  addNoteButton: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6, backgroundColor: '#F0F9FF' },
  addNoteText: { fontSize: 14, fontWeight: '600', color: '#007AFF', marginLeft: 4 },
  notesLoading: { padding: 40, alignItems: 'center' },
  notesEmpty: { padding: 40, alignItems: 'center' },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#374151', marginTop: 12, marginBottom: 4 },
  emptySubtext: { fontSize: 14, color: '#6B7280', textAlign: 'center', paddingHorizontal: 20 },
  notesList: { padding: 16 },
  noteCard: { backgroundColor: '#F8FAFC', borderRadius: 8, padding: 12, marginBottom: 12, borderWidth: 1, borderColor: '#E5E7EB' },
  noteHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  noteDate: { fontSize: 12, color: '#6B7280', fontWeight: '500' },
  noteActions: { flexDirection: 'row', gap: 8 },
  actionButton: { padding: 6, borderRadius: 4, backgroundColor: '#F3F4F6' },
  noteDeleteButton: { backgroundColor: '#FEF2F2' },
  noteText: { fontSize: 14, color: '#111827', lineHeight: 20 },
  updatedText: { fontSize: 11, color: '#6B7280', marginTop: 4, fontStyle: 'italic' },
  noteModalContent: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: '70%', minHeight: '40%' },
  modalBody: { padding: 20, paddingBottom: 40 },
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 20 },
  button: { flex: 1, paddingVertical: 12, borderRadius: 8, alignItems: 'center', marginHorizontal: 8 },
  cancelButton: { backgroundColor: '#F3F4F6' },
  modalSaveButton: { backgroundColor: '#10B981' },
  cancelButtonText: { color: '#374151', fontWeight: '600' },
  saveButtonText: { color: '#FFFFFF', fontWeight: '600' },
  loadingText: { marginTop: 8, fontSize: 14, color: '#6B7280' },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#111827' },
  clientInfo: { marginTop: 20, padding: 16, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#E5E7EB' },
  infoLabel: { fontSize: 16, fontWeight: 'bold', color: '#111827', marginBottom: 12 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  infoKey: { fontSize: 14, color: '#6B7280' },
  infoValue: { fontSize: 14, fontWeight: '500', color: '#111827' },
});

export default EditClientScreen;