import React, { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";
import { toast } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";

const ROLES = ["admin", "user", "viewer"];

type User = {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

type Invite = {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_accepted: boolean;
  expires_at: string;
  created_at: string;
  invited_by?: string;
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteForm, setInviteForm] = useState({
    email: "",
    first_name: "",
    last_name: "",
    role: "user",
  });
  const [inviting, setInviting] = useState(false);
  const [activationModal, setActivationModal] = useState<{
    isOpen: boolean;
    invite: Invite | null;
  }>({ isOpen: false, invite: null });
  const [activationForm, setActivationForm] = useState({
    password: "",
    first_name: "",
    last_name: "",
  });
  const [activating, setActivating] = useState(false);

  // Get current user id from localStorage
  let currentUserId: number | null = null;
  try {
    const user = JSON.parse(localStorage.getItem("user") || "null");
    currentUserId = user?.id ?? null;
  } catch {
    currentUserId = null;
  }

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get("/auth/users");
      // The API returns the array directly, not wrapped in a data property
      setUsers(Array.isArray(res) ? res : []);
    } catch (e: any) {
      console.error("Failed to load users:", e);
      toast.error("Failed to load users");
      setUsers([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const fetchInvites = async () => {
    try {
      const res = await api.get("/auth/invites");
      // The API returns the array directly, not wrapped in a data property
      setInvites(Array.isArray(res) ? res : []);
    } catch (e: any) {
      console.error("Failed to load invites:", e);
      toast.error("Failed to load invites");
      setInvites([]); // Set empty array on error
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchInvites();
  }, []);

  const handleInviteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setInviteForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviting(true);
    try {
      await api.post("/auth/invite", inviteForm);
      toast.success("Invite sent!");
      setInviteForm({ email: "", first_name: "", last_name: "", role: "user" });
      fetchInvites();
    } catch (err: any) {
      console.error("Failed to send invite:", err);
      toast.error(err?.response?.data?.detail || "Failed to send invite");
    } finally {
      setInviting(false);
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await api.put(`/auth/users/${userId}/role`, { role: newRole });
      toast.success("Role updated");
      fetchUsers();
    } catch (err: any) {
      console.error("Failed to update role:", err);
      toast.error(err?.response?.data?.detail || "Failed to update role");
    }
  };

  const getInviteStatus = (invite: Invite) => {
    if (invite.is_accepted) return "Accepted";
    const now = new Date();
    const expiresAt = new Date(invite.expires_at);
    if (expiresAt < now) return "Expired";
    return "Pending";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Accepted": return "text-green-600";
      case "Expired": return "text-red-600";
      case "Pending": return "text-yellow-600";
      default: return "text-gray-600";
    }
  };

  const openActivationModal = (invite: Invite) => {
    setActivationModal({ isOpen: true, invite });
    setActivationForm({
      password: "",
      first_name: invite.first_name || "",
      last_name: invite.last_name || "",
    });
  };

  const closeActivationModal = () => {
    setActivationModal({ isOpen: false, invite: null });
    setActivationForm({
      password: "",
      first_name: "",
      last_name: "",
    });
  };

  const handleActivationFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setActivationForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleActivateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activationModal.invite) return;
    
    setActivating(true);
    try {
      await api.post(`/auth/invites/${activationModal.invite.id}/activate`, activationForm);
      toast.success("User activated successfully!");
      closeActivationModal();
      fetchUsers();
      fetchInvites();
    } catch (err: any) {
      console.error("Failed to activate user:", err);
      toast.error(err?.response?.data?.detail || "Failed to activate user");
    } finally {
      setActivating(false);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-3xl mx-auto py-8">
          <h1 className="text-2xl font-bold mb-6">Organization Users</h1>
          <div className="text-center py-8">Loading...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-2xl font-bold mb-6">Organization Users</h1>

        <section className="mb-10">
          <h2 className="font-semibold mb-2">Invite User</h2>
          <form className="flex flex-wrap gap-2 items-end" onSubmit={handleInvite}>
            <Input
              name="email"
              type="email"
              placeholder="Email"
              value={inviteForm.email}
              onChange={handleInviteChange}
              required
              className="w-48"
            />
            <Input
              name="first_name"
              placeholder="First Name"
              value={inviteForm.first_name}
              onChange={handleInviteChange}
              className="w-36"
            />
            <Input
              name="last_name"
              placeholder="Last Name"
              value={inviteForm.last_name}
              onChange={handleInviteChange}
              className="w-36"
            />
            <Select
              value={inviteForm.role}
              onValueChange={(role: string) => setInviteForm((prev) => ({ ...prev, role }))}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Role" />
              </SelectTrigger>
              <SelectContent>
                {ROLES.map((role) => (
                  <SelectItem key={role} value={role}>
                    {role.charAt(0).toUpperCase() + role.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button type="submit" disabled={inviting}>
              {inviting ? "Inviting..." : "Invite"}
            </Button>
          </form>
        </section>

        <section className="mb-10">
          <h2 className="font-semibold mb-2">All Invites</h2>
          <table className="w-full border text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-2 text-left">Email</th>
                <th className="p-2 text-left">Name</th>
                <th className="p-2 text-left">Role</th>
                <th className="p-2 text-left">Status</th>
                <th className="p-2 text-left">Invited By</th>
                <th className="p-2 text-left">Expires</th>
                <th className="p-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(!invites || invites.length === 0) && (
                <tr>
                  <td colSpan={7} className="text-center py-4 text-gray-400">
                    No invites found
                  </td>
                </tr>
              )}
              {invites && invites.map((invite) => {
                const status = getInviteStatus(invite);
                return (
                  <tr key={invite.id} className="border-t">
                    <td className="p-2">{invite.email}</td>
                    <td className="p-2">{[invite.first_name, invite.last_name].filter(Boolean).join(" ") || "-"}</td>
                    <td className="p-2">{invite.role}</td>
                    <td className={`p-2 font-semibold ${getStatusColor(status)}`}>{status}</td>
                    <td className="p-2">{invite.invited_by || "-"}</td>
                    <td className="p-2">{new Date(invite.expires_at).toLocaleString()}</td>
                    <td className="p-2">
                      {status === "Pending" && (
                        <Button
                          onClick={() => openActivationModal(invite)}
                          size="sm"
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Activate
                        </Button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        <section>
          <h2 className="font-semibold mb-2">Current Users</h2>
          <table className="w-full border text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-2 text-left">Email</th>
                <th className="p-2 text-left">Name</th>
                <th className="p-2 text-left">Role</th>
                <th className="p-2 text-left">Status</th>
                <th className="p-2 text-left">Created</th>
                <th className="p-2 text-left">Change Role</th>
              </tr>
            </thead>
            <tbody>
              {(!users || users.length === 0) && (
                <tr>
                  <td colSpan={6} className="text-center py-4 text-gray-400">
                    No users found
                  </td>
                </tr>
              )}
              {users && users.map((user) => (
                <tr key={user.id} className="border-t">
                  <td className="p-2">{user.email}</td>
                  <td className="p-2">{[user.first_name, user.last_name].filter(Boolean).join(" ") || "-"}</td>
                  <td className="p-2">{user.role}</td>
                  <td className="p-2">{user.is_active ? "Active" : "Inactive"}</td>
                  <td className="p-2">{new Date(user.created_at).toLocaleString()}</td>
                  <td className="p-2">
                    <Select
                      value={user.role}
                      onValueChange={(role: string) => handleRoleChange(user.id, role)}
                      disabled={user.id === currentUserId}
                    >
                      <SelectTrigger className="w-28">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ROLES.map((role) => (
                          <SelectItem key={role} value={role}>
                            {role.charAt(0).toUpperCase() + role.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>

      {/* Activation Modal */}
      {activationModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold mb-4">
              Activate User: {activationModal.invite?.email}
            </h2>
            <form onSubmit={handleActivateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Password</label>
                <Input
                  type="password"
                  name="password"
                  value={activationForm.password}
                  onChange={handleActivationFormChange}
                  placeholder="Enter password for user"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">First Name</label>
                <Input
                  type="text"
                  name="first_name"
                  value={activationForm.first_name}
                  onChange={handleActivationFormChange}
                  placeholder="First name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Last Name</label>
                <Input
                  type="text"
                  name="last_name"
                  value={activationForm.last_name}
                  onChange={handleActivationFormChange}
                  placeholder="Last name"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={closeActivationModal}
                  disabled={activating}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={activating}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {activating ? "Activating..." : "Activate User"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
} 