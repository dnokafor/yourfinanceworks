import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  ActivityIndicator,
  Modal,
  RefreshControl,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import apiService, { Expense } from '../services/api';

interface ExpensesScreenProps {
  onNavigateBack: () => void;
  onNavigateToNewExpense: () => void;
  onNavigateToEditExpense: (expense: Expense) => void;
}

const EXPENSE_CATEGORIES = [
  'General', 'Office Supplies', 'Travel', 'Meals', 'Transportation',
  'Marketing', 'Software', 'Equipment', 'Utilities', 'Professional Services'
];

const ExpensesScreen: React.FC<ExpensesScreenProps> = ({
  onNavigateBack,
  onNavigateToNewExpense,
  onNavigateToEditExpense,
}) => {
  const { t } = useTranslation();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showCategoryModal, setShowCategoryModal] = useState(false);

  useEffect(() => {
    fetchExpenses();
  }, [categoryFilter]);

  const fetchExpenses = async () => {
    try {
      setLoading(true);
      const data = await apiService.getExpenses(categoryFilter === 'all' ? undefined : categoryFilter);
      setExpenses(data);
    } catch (error) {
      console.error('Failed to fetch expenses:', error);
      Alert.alert('Error', 'Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchExpenses();
    setRefreshing(false);
  };

  const handleDeleteExpense = async (id: number) => {
    Alert.alert(
      'Delete Expense',
      'Are you sure you want to delete this expense?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiService.deleteExpense(id);
              setExpenses(prev => prev.filter(e => e.id !== id));
              Alert.alert('Success', 'Expense deleted successfully');
            } catch (error) {
              console.error('Failed to delete expense:', error);
              Alert.alert('Error', 'Failed to delete expense');
            }
          },
        },
      ]
    );
  };

  const filteredExpenses = expenses.filter(expense => {
    const matchesSearch = expense.vendor?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         expense.category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         expense.notes?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'recorded': return '#10B981';
      case 'pending': return '#F59E0B';
      case 'completed': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  const CategoryModal = () => (
    <Modal
      visible={showCategoryModal}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowCategoryModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Filter by Category</Text>
          
          <TouchableOpacity
            style={[styles.categoryOption, categoryFilter === 'all' && styles.categoryOptionActive]}
            onPress={() => {
              setCategoryFilter('all');
              setShowCategoryModal(false);
            }}
          >
            <Text style={styles.categoryOptionText}>All Categories</Text>
          </TouchableOpacity>

          {EXPENSE_CATEGORIES.map((category) => (
            <TouchableOpacity
              key={category}
              style={[styles.categoryOption, categoryFilter === category && styles.categoryOptionActive]}
              onPress={() => {
                setCategoryFilter(category);
                setShowCategoryModal(false);
              }}
            >
              <Text style={styles.categoryOptionText}>{category}</Text>
            </TouchableOpacity>
          ))}

          <TouchableOpacity
            style={styles.modalCloseButton}
            onPress={() => setShowCategoryModal(false)}
          >
            <Text style={styles.modalCloseButtonText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading expenses...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={onNavigateBack}>
          <Ionicons name="arrow-back" size={24} color="#374151" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Expenses</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={onNavigateToNewExpense}
        >
          <Ionicons name="add" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Ionicons name="search" size={20} color="#9CA3AF" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search expenses..."
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowCategoryModal(true)}
        >
          <Ionicons name="filter" size={20} color="#374151" />
          <Text style={styles.filterButtonText}>
            {categoryFilter === 'all' ? 'All' : categoryFilter}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {filteredExpenses.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="receipt-outline" size={64} color="#9CA3AF" />
            <Text style={styles.emptyStateText}>No expenses found</Text>
            <Text style={styles.emptyStateSubtext}>
              {searchQuery || categoryFilter !== 'all' 
                ? 'Try adjusting your search or filter'
                : 'Create your first expense to get started'
              }
            </Text>
          </View>
        ) : (
          <View style={styles.expensesList}>
            {filteredExpenses.map((expense) => (
              <View key={expense.id} style={styles.expenseCard}>
                <View style={styles.expenseHeader}>
                  <View style={styles.expenseInfo}>
                    <Text style={styles.expenseVendor}>
                      {expense.vendor || 'Unknown Vendor'}
                    </Text>
                    <Text style={styles.expenseCategory}>{expense.category}</Text>
                  </View>
                  <View style={styles.expenseAmount}>
                    <Text style={styles.expenseAmountText}>
                      {formatCurrency(expense.amount, expense.currency)}
                    </Text>
                    <View style={[styles.statusBadge, { backgroundColor: getStatusColor(expense.status) }]}>
                      <Text style={styles.statusText}>{expense.status}</Text>
                    </View>
                  </View>
                </View>
                
                <View style={styles.expenseDetails}>
                  <Text style={styles.expenseDate}>
                    {formatDate(expense.expense_date)}
                  </Text>
                  {expense.notes && (
                    <Text style={styles.expenseNotes} numberOfLines={2}>
                      {expense.notes}
                    </Text>
                  )}
                </View>

                <View style={styles.expenseActions}>
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => onNavigateToEditExpense(expense)}
                  >
                    <Ionicons name="create-outline" size={16} color="#3B82F6" />
                    <Text style={styles.actionButtonText}>Edit</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.actionButton, styles.deleteButton]}
                    onPress={() => handleDeleteExpense(expense.id)}
                  >
                    <Ionicons name="trash-outline" size={16} color="#EF4444" />
                    <Text style={[styles.actionButtonText, styles.deleteButtonText]}>Delete</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      <CategoryModal />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  addButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    gap: 12,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: '#111827',
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    gap: 4,
  },
  filterButtonText: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  expensesList: {
    padding: 20,
  },
  expenseCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  expenseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  expenseInfo: {
    flex: 1,
  },
  expenseVendor: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  expenseCategory: {
    fontSize: 14,
    color: '#6B7280',
  },
  expenseAmount: {
    alignItems: 'flex-end',
  },
  expenseAmountText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    color: '#FFFFFF',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  expenseDetails: {
    marginBottom: 12,
  },
  expenseDate: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 4,
  },
  expenseNotes: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  expenseActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#F3F4F6',
    gap: 4,
  },
  actionButtonText: {
    fontSize: 14,
    color: '#3B82F6',
    fontWeight: '500',
  },
  deleteButton: {
    backgroundColor: '#FEF2F2',
  },
  deleteButtonText: {
    color: '#EF4444',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 80,
    paddingHorizontal: 40,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    width: '80%',
    maxHeight: '70%',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 20,
    textAlign: 'center',
  },
  categoryOption: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  categoryOptionActive: {
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#3B82F6',
  },
  categoryOptionText: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  modalCloseButton: {
    backgroundColor: '#F3F4F6',
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  modalCloseButtonText: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default ExpensesScreen;