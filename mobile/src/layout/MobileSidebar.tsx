import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import AsyncStorage from '@react-native-async-storage/async-storage';
import apiService from '../services/api';

interface Organization {
  id: number;
  name: string;
}

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  tenant_id: number;
  is_superuser?: boolean;
  organizations?: Organization[];
}

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentScreen: string;
  onNavigate: (screen: string) => void;
  onLogout: () => void;
  user: User | null;
}

export function MobileSidebar({ 
  isOpen, 
  onClose, 
  currentScreen, 
  onNavigate, 
  onLogout,
  user 
}: MobileSidebarProps) {
  const { t } = useTranslation();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState<string>('');
  const [showOrgModal, setShowOrgModal] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    if (user) {
      fetchUserOrganizations();
      loadTheme();
    }
  }, [user]);

  const fetchUserOrganizations = async () => {
    try {
      const response = await apiService.getCurrentUser();
      if (response?.organizations && response?.organizations.length > 0) {
        setOrganizations(response?.organizations);
        
        // Get selected tenant from storage or use user's primary tenant
        const selectedTenantId = await AsyncStorage.getItem('selected_tenant_id');
        const orgId = selectedTenantId || user?.tenant_id?.toString() || '';
        setCurrentOrgId(orgId);
      } else {
        // Fallback to single organization
        const fallbackOrg = {
          id: user?.tenant_id || 0,
          name: 'Current Organization'
        };
        setOrganizations([fallbackOrg]);
        setCurrentOrgId(user?.tenant_id?.toString() || '');
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
      // Fallback to single organization
      const fallbackOrg = {
        id: user?.tenant_id || 0,
        name: 'Current Organization'
      };
      setOrganizations([fallbackOrg]);
      setCurrentOrgId(user?.tenant_id?.toString() || '');
    }
  };

  const loadTheme = async () => {
    try {
      const theme = await AsyncStorage.getItem('theme');
      setIsDarkMode(theme === 'dark');
    } catch (error) {
      console.error('Failed to load theme:', error);
    }
  };

  const toggleTheme = async () => {
    try {
      const newTheme = isDarkMode ? 'light' : 'dark';
      await AsyncStorage.setItem('theme', newTheme);
      setIsDarkMode(!isDarkMode);
      // Note: In a real app, you'd need to implement theme switching logic
    } catch (error) {
      console.error('Failed to save theme:', error);
    }
  };

  const handleOrganizationSwitch = async (orgId: string) => {
    if (orgId === currentOrgId) {
      setShowOrgModal(false);
      return;
    }

    try {
      await AsyncStorage.setItem('selected_tenant_id', orgId);
      setCurrentOrgId(orgId);
      setShowOrgModal(false);
      
      // In a real app, you'd need to refresh the app state here
      // For now, we'll just close the modal
    } catch (error) {
      console.error('Failed to switch organization:', error);
    }
  };

  const getCurrentOrgName = () => {
    const org = organizations.find(o => o.id.toString() === currentOrgId);
    return org?.name || 'Current Organization';
  };

  const isAdmin = user?.role === 'admin';
  const isSuperUser = user?.is_superuser;
  const isPrimaryTenant = currentOrgId === user?.tenant_id?.toString();

  const mainMenuItems = [
    { icon: 'home-outline', label: t('navigation.dashboard'), screen: 'dashboard' },
    { icon: 'people-outline', label: t('navigation.clients'), screen: 'clients' },
    { icon: 'document-text-outline', label: t('navigation.invoices'), screen: 'invoices' },
    { icon: 'card-outline', label: t('navigation.payments'), screen: 'payments' },
    { icon: 'receipt-outline', label: t('navigation.expenses'), screen: 'expenses' },
    { icon: 'document-outline', label: t('navigation.bank_statements'), screen: 'statements' },
  ];

  const settingsMenuItems = [
    ...(isAdmin && isPrimaryTenant ? [{
      icon: 'settings-outline',
      label: t('navigation.settings'),
      screen: 'settings'
    }] : []),
    ...(isAdmin ? [{
      icon: 'people-circle-outline',
      label: t('navigation.users'),
      screen: 'users'
    }] : []),
    ...((isAdmin || isSuperUser) ? [{
      icon: 'list-outline',
      label: t('navigation.audit_log'),
      screen: 'auditLog'
    }] : []),
    ...(isSuperUser && isPrimaryTenant ? [{
      icon: 'shield-checkmark-outline',
      label: t('navigation.super_admin'),
      screen: 'superAdmin'
    }] : [])
  ];

  const getUserInitials = () => {
    if (!user) return 'U';
    const first = user.first_name?.trim() || '';
    const last = user.last_name?.trim() || '';
    const name = `${first} ${last}`.trim() || user.email?.split('@')[0] || 'User';
    const parts = name.split(' ').filter(Boolean);
    const initials = parts.length >= 2 ? `${parts[0][0]}${parts[1][0]}` : name.slice(0, 2);
    return initials.toUpperCase();
  };

  const getUserDisplayName = () => {
    if (!user) return 'User';
    const first = user.first_name?.trim() || '';
    const last = user.last_name?.trim() || '';
    const name = `${first} ${last}`.trim();
    return name || user.email?.split('@')[0] || 'User';
  };

  if (!isOpen) return null;

  return (
    <>
      <Modal
        visible={isOpen}
        animationType="slide"
        transparent={true}
        onRequestClose={onClose}
      >
        <View style={styles.overlay}>
          <View style={styles.sidebar}>
            {/* Header */}
            <View style={styles.header}>
              <View style={styles.userInfo}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{getUserInitials()}</Text>
                </View>
                <View style={styles.userDetails}>
                  <Text style={styles.userName}>{getUserDisplayName()}</Text>
                  <Text style={styles.userEmail}>{user?.email}</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                <Ionicons name="close" size={24} color="#374151" />
              </TouchableOpacity>
            </View>

            {/* Organization Selector */}
            {organizations.length > 0 && (
              <View style={styles.orgSection}>
                <Text style={styles.orgLabel}>
                  Organization {organizations.length > 1 ? `(${organizations.length} available)` : ''}
                </Text>
                <TouchableOpacity 
                  style={styles.orgSelector}
                  onPress={() => organizations.length > 1 && setShowOrgModal(true)}
                >
                  <Ionicons name="business-outline" size={20} color="#374151" />
                  <Text style={styles.orgName}>{getCurrentOrgName()}</Text>
                  {organizations.length > 1 && (
                    <Ionicons name="chevron-down" size={16} color="#9CA3AF" />
                  )}
                </TouchableOpacity>
              </View>
            )}

            <ScrollView style={styles.menuContainer} showsVerticalScrollIndicator={false}>
              {/* Main Menu */}
              <View style={styles.menuSection}>
                {mainMenuItems.map((item) => (
                  <TouchableOpacity
                    key={item.screen}
                    style={[
                      styles.menuItem,
                      currentScreen === item.screen && styles.menuItemActive
                    ]}
                    onPress={() => {
                      onNavigate(item.screen);
                      onClose();
                    }}
                  >
                    <Ionicons 
                      name={item.icon as any} 
                      size={20} 
                      color={currentScreen === item.screen ? '#3B82F6' : '#6B7280'} 
                    />
                    <Text style={[
                      styles.menuItemText,
                      currentScreen === item.screen && styles.menuItemTextActive
                    ]}>
                      {item.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Settings Menu */}
              {settingsMenuItems.length > 0 && (
                <View style={styles.menuSection}>
                  <View style={styles.separator} />
                  {settingsMenuItems.map((item) => (
                    <TouchableOpacity
                      key={item.screen}
                      style={[
                        styles.menuItem,
                        currentScreen === item.screen && styles.menuItemActive
                      ]}
                      onPress={() => {
                        onNavigate(item.screen);
                        onClose();
                      }}
                    >
                      <Ionicons 
                        name={item.icon as any} 
                        size={20} 
                        color={currentScreen === item.screen ? '#3B82F6' : '#6B7280'} 
                      />
                      <Text style={[
                        styles.menuItemText,
                        currentScreen === item.screen && styles.menuItemTextActive
                      ]}>
                        {item.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </ScrollView>

            {/* Footer */}
            <View style={styles.footer}>
              <TouchableOpacity style={styles.themeToggle} onPress={toggleTheme}>
                <Ionicons 
                  name={isDarkMode ? 'sunny-outline' : 'moon-outline'} 
                  size={20} 
                  color="#6B7280" 
                />
                <Text style={styles.themeToggleText}>
                  {isDarkMode ? 'Light Mode' : 'Dark Mode'}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
                <Ionicons name="log-out-outline" size={20} color="#EF4444" />
                <Text style={styles.logoutText}>{t('auth.logout')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Organization Selection Modal */}
      <Modal
        visible={showOrgModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowOrgModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Select Organization</Text>
            
            {organizations.map((org) => (
              <TouchableOpacity
                key={org.id}
                style={[
                  styles.orgOption,
                  org.id.toString() === currentOrgId && styles.orgOptionActive
                ]}
                onPress={() => handleOrganizationSwitch(org.id.toString())}
              >
                <Text style={styles.orgOptionText}>
                  {org.name}
                  {org.id === user?.tenant_id && (
                    <Text style={styles.homeIndicator}> (Home)</Text>
                  )}
                </Text>
                {org.id.toString() === currentOrgId && (
                  <Ionicons name="checkmark" size={20} color="#10B981" />
                )}
              </TouchableOpacity>
            ))}

            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowOrgModal(false)}
            >
              <Text style={styles.modalCloseButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  sidebar: {
    backgroundColor: '#FFFFFF',
    height: '90%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  userEmail: {
    fontSize: 14,
    color: '#6B7280',
  },
  closeButton: {
    padding: 8,
  },
  orgSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  orgLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  orgSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  orgName: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },
  menuContainer: {
    flex: 1,
  },
  menuSection: {
    paddingVertical: 8,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    gap: 12,
  },
  menuItemActive: {
    backgroundColor: '#EFF6FF',
    borderRightWidth: 3,
    borderRightColor: '#3B82F6',
  },
  menuItemText: {
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '500',
  },
  menuItemTextActive: {
    color: '#3B82F6',
    fontWeight: '600',
  },
  separator: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 20,
    marginVertical: 8,
  },
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 8,
  },
  themeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    gap: 12,
  },
  themeToggleText: {
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '500',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    gap: 12,
  },
  logoutText: {
    fontSize: 16,
    color: '#EF4444',
    fontWeight: '600',
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
  orgOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  orgOptionActive: {
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#3B82F6',
  },
  orgOptionText: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
    flex: 1,
  },
  homeIndicator: {
    color: '#3B82F6',
    fontSize: 14,
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