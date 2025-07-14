import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Trash2, Edit, UserPlus, Building, Database, Users, ShieldCheck, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface Tenant {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  user_count: number;
  subdomain?: string;
  default_currency: string;
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  tenant_id: number;
  tenant_name: string;
  created_at: string;
}

interface DatabaseStatus {
  tenant_id: number;
  tenant_name: string;
  database_name: string;
  status: string;
  message?: string;
  error?: string;
}

const SuperAdminDashboard: React.FC = () => {
  const { user } = useAuth();

  // Check if user is super admin BEFORE any hooks are called
  if (!user?.is_superuser) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Alert className="max-w-md">
          <ShieldCheck className="h-4 w-4" />
          <AlertDescription>
            You need super admin access to view this page.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <SuperAdminDashboardContent user={user} />;
};

// Separate component for the main dashboard content
const SuperAdminDashboardContent: React.FC<{ user: any }> = ({ user }) => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [databases, setDatabases] = useState<DatabaseStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('tenants');
  
  // Form states
  const [showCreateTenant, setShowCreateTenant] = useState(false);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [createTenantForm, setCreateTenantForm] = useState({
    name: '',
    email: '',
    default_currency: 'USD'
  });
  const [createUserForm, setCreateUserForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'user',
    password: '',
    tenant_id: ''
  });

  const fetchTenants = async () => {
    try {
      const response = await fetch('/api/v1/super-admin/tenants', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch tenants');
      const data = await response.json();
      setTenants(data);
    } catch (err) {
      setError('Failed to fetch tenants');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/v1/super-admin/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError('Failed to fetch users');
    }
  };

  const fetchDatabaseOverview = async () => {
    try {
      const response = await fetch('/api/v1/super-admin/database/overview', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch database overview');
      const data = await response.json();
      setDatabases(data.databases || []);
    } catch (err) {
      setError('Failed to fetch database overview');
    }
  };

  const handleCreateTenant = async () => {
    try {
      const response = await fetch('/api/v1/super-admin/tenants', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(createTenantForm)
      });
      
      if (!response.ok) throw new Error('Failed to create tenant');
      
      setShowCreateTenant(false);
      setCreateTenantForm({ name: '', email: '', default_currency: 'USD' });
      fetchTenants();
    } catch (err) {
      setError('Failed to create tenant');
    }
  };

  const handleCreateUser = async () => {
    try {
      const response = await fetch(`/api/v1/super-admin/users?tenant_id=${createUserForm.tenant_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(createUserForm)
      });
      
      if (!response.ok) throw new Error('Failed to create user');
      
      setShowCreateUser(false);
      setCreateUserForm({ email: '', first_name: '', last_name: '', role: 'user', password: '', tenant_id: '' });
      fetchUsers();
    } catch (err) {
      setError('Failed to create user');
    }
  };

  const handleDeleteTenant = async (tenantId: number) => {
    if (!confirm('Are you sure you want to delete this tenant? This will delete all associated data.')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/super-admin/tenants/${tenantId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to delete tenant');
      
      fetchTenants();
    } catch (err) {
      setError('Failed to delete tenant');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/super-admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to delete user');
      
      fetchUsers();
    } catch (err) {
      setError('Failed to delete user');
    }
  };

  const handleRecreateDatabase = async (tenantId: number) => {
    if (!confirm('Are you sure you want to recreate this database? This will DELETE ALL DATA.')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/super-admin/tenants/${tenantId}/database/recreate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to recreate database');
      
      fetchDatabaseOverview();
    } catch (err) {
      setError('Failed to recreate database');
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTenants(), fetchUsers(), fetchDatabaseOverview()]);
      setLoading(false);
    };
    
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading super admin dashboard...</p>
        </div>
      </div>
    );
  }

  const totalUsers = users.length;
  const activeTenants = tenants.filter(t => t.is_active).length;
  const healthyDatabases = databases.filter(db => db.status === 'connected').length;
  const superUsers = users.filter(u => u.is_superuser).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Super Admin Dashboard</h1>
          <p className="text-gray-600">Manage all tenants, users, and databases</p>
        </div>

        {error && (
          <Alert className="mb-6" variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Tenants</p>
                  <p className="text-2xl font-bold">{tenants.length}</p>
                </div>
                <Building className="h-8 w-8 text-blue-500" />
              </div>
              <p className="text-sm text-gray-500 mt-2">{activeTenants} active</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Users</p>
                  <p className="text-2xl font-bold">{totalUsers}</p>
                </div>
                <Users className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-sm text-gray-500 mt-2">{superUsers} super users</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Databases</p>
                  <p className="text-2xl font-bold">{databases.length}</p>
                </div>
                <Database className="h-8 w-8 text-purple-500" />
              </div>
              <p className="text-sm text-gray-500 mt-2">{healthyDatabases} healthy</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">System Status</p>
                  <p className="text-2xl font-bold text-green-600">Healthy</p>
                </div>
                <ShieldCheck className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-sm text-gray-500 mt-2">All systems operational</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="tenants">Tenants</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="databases">Databases</TabsTrigger>
          </TabsList>
          
          <TabsContent value="tenants" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Tenants Management</CardTitle>
                  <Dialog open={showCreateTenant} onOpenChange={setShowCreateTenant}>
                    <DialogTrigger asChild>
                      <Button>
                        <Building className="h-4 w-4 mr-2" />
                        Create Tenant
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Create New Tenant</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="tenant-name">Organization Name</Label>
                          <Input
                            id="tenant-name"
                            value={createTenantForm.name}
                            onChange={(e) => setCreateTenantForm(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="Enter organization name"
                          />
                        </div>
                        <div>
                          <Label htmlFor="tenant-email">Email</Label>
                          <Input
                            id="tenant-email"
                            type="email"
                            value={createTenantForm.email}
                            onChange={(e) => setCreateTenantForm(prev => ({ ...prev, email: e.target.value }))}
                            placeholder="Enter email"
                          />
                        </div>
                        <div>
                          <Label htmlFor="tenant-currency">Default Currency</Label>
                          <Select value={createTenantForm.default_currency} onValueChange={(value) => setCreateTenantForm(prev => ({ ...prev, default_currency: value }))}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="USD">USD</SelectItem>
                              <SelectItem value="EUR">EUR</SelectItem>
                              <SelectItem value="GBP">GBP</SelectItem>
                              <SelectItem value="JPY">JPY</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <Button onClick={handleCreateTenant} className="w-full">Create Tenant</Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Users</TableHead>
                      <TableHead>Currency</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tenants.map((tenant) => (
                      <TableRow key={tenant.id}>
                        <TableCell className="font-medium">{tenant.name}</TableCell>
                        <TableCell>{tenant.email}</TableCell>
                        <TableCell>{tenant.user_count}</TableCell>
                        <TableCell>{tenant.default_currency}</TableCell>
                        <TableCell>
                          <Badge variant={tenant.is_active ? "default" : "secondary"}>
                            {tenant.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(tenant.created_at).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button size="sm" variant="outline">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleDeleteTenant(tenant.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="users" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Users Management</CardTitle>
                  <Dialog open={showCreateUser} onOpenChange={setShowCreateUser}>
                    <DialogTrigger asChild>
                      <Button>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Create User
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Create New User</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="user-email">Email</Label>
                          <Input
                            id="user-email"
                            type="email"
                            value={createUserForm.email}
                            onChange={(e) => setCreateUserForm(prev => ({ ...prev, email: e.target.value }))}
                            placeholder="Enter email"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="user-first-name">First Name</Label>
                            <Input
                              id="user-first-name"
                              value={createUserForm.first_name}
                              onChange={(e) => setCreateUserForm(prev => ({ ...prev, first_name: e.target.value }))}
                              placeholder="First name"
                            />
                          </div>
                          <div>
                            <Label htmlFor="user-last-name">Last Name</Label>
                            <Input
                              id="user-last-name"
                              value={createUserForm.last_name}
                              onChange={(e) => setCreateUserForm(prev => ({ ...prev, last_name: e.target.value }))}
                              placeholder="Last name"
                            />
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="user-tenant">Tenant</Label>
                          <Select value={createUserForm.tenant_id} onValueChange={(value) => setCreateUserForm(prev => ({ ...prev, tenant_id: value }))}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select tenant" />
                            </SelectTrigger>
                            <SelectContent>
                              {tenants.map(tenant => (
                                <SelectItem key={tenant.id} value={tenant.id.toString()}>
                                  {tenant.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="user-role">Role</Label>
                          <Select value={createUserForm.role} onValueChange={(value) => setCreateUserForm(prev => ({ ...prev, role: value }))}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="user">User</SelectItem>
                              <SelectItem value="viewer">Viewer</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="user-password">Password</Label>
                          <Input
                            id="user-password"
                            type="password"
                            value={createUserForm.password}
                            onChange={(e) => setCreateUserForm(prev => ({ ...prev, password: e.target.value }))}
                            placeholder="Enter password"
                          />
                        </div>
                        <Button onClick={handleCreateUser} className="w-full">Create User</Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Tenant</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">
                          {user.first_name} {user.last_name}
                          {user.is_superuser && (
                            <Badge variant="outline" className="ml-2">Super</Badge>
                          )}
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{user.tenant_name}</TableCell>
                        <TableCell>
                          <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                            {user.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={user.is_active ? "default" : "secondary"}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button size="sm" variant="outline">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleDeleteUser(user.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="databases" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Database Management</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tenant</TableHead>
                      <TableHead>Database</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {databases.map((db) => (
                      <TableRow key={db.tenant_id}>
                        <TableCell className="font-medium">{db.tenant_name}</TableCell>
                        <TableCell>{db.database_name}</TableCell>
                        <TableCell>
                          <Badge variant={db.status === 'connected' ? 'default' : 'destructive'}>
                            {db.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{db.message || db.error || '-'}</TableCell>
                        <TableCell>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleRecreateDatabase(db.tenant_id)}
                          >
                            <Database className="h-4 w-4 mr-2" />
                            Recreate
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SuperAdminDashboard; 