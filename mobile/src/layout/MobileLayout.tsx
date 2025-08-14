import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MobileSidebar } from './MobileSidebar';

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  tenant_id: number;
  is_superuser?: boolean;
}

interface MobileLayoutProps {
  children: React.ReactNode;
  currentScreen: string;
  onNavigate: (screen: string) => void;
  onLogout: () => void;
  user: User | null;
}

export function MobileLayout({ 
  children, 
  currentScreen, 
  onNavigate, 
  onLogout, 
  user 
}: MobileLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <View style={styles.container}>
      {/* Header with menu button */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.menuButton} 
          onPress={() => setSidebarOpen(true)}
        >
          <Ionicons name="menu" size={24} color="#374151" />
        </TouchableOpacity>
      </View>
      
      {/* Main content */}
      <View style={styles.content}>
        {children}
      </View>
      
      {/* Sidebar */}
      <MobileSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentScreen={currentScreen}
        onNavigate={onNavigate}
        onLogout={onLogout}
        user={user}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  menuButton: {
    padding: 8,
    alignSelf: 'flex-start',
  },
  content: {
    flex: 1,
  },
});