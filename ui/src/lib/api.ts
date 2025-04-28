import { toast } from 'sonner';

const API_BASE_URL = 'http://localhost:8000/api';

// Type definitions
export interface Client {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  balance: number;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id?: number;
  description: string;
  quantity: number;
  price: number;
  invoice_id?: number;
}

export interface Invoice {
  id: number;
  number: string;
  client_id: number;
  client_name?: string;
  date: string;
  due_date: string;
  amount: number;
  status: string;
  notes?: string;
  items: InvoiceItem[];
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  invoice_id: number;
  invoice_number?: string;
  client_name?: string;
  amount: number;
  date: string;
  method: string;
  created_at: string;
  updated_at: string;
}

// Add settings types
export interface CompanyInfo {
  name: string;
  email: string;
  phone: string;
  address: string;
  tax_id: string;
  logo?: string;
}

export interface InvoiceSettings {
  prefix: string;
  next_number: string;
  terms: string;
  notes?: string;
  send_copy: boolean;
  auto_reminders: boolean;
}

export interface Settings {
  company_info: CompanyInfo;
  invoice_settings: InvoiceSettings;
}

// Generic API request function with error handling
async function apiRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  try {
    console.log(`Making API request to ${url}`, options);
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      // Try to parse error response
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        // If JSON parsing fails, use status text
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }

      // Better handle validation errors (422)
      if (response.status === 422 && errorData.detail) {
        // Format validation errors nicely
        if (Array.isArray(errorData.detail)) {
          // Format validation errors from FastAPI
          const errorMessages = errorData.detail.map((err: any) => {
            const field = err.loc.slice(1).join('.');
            return `${field}: ${err.msg}`;
          }).join('; ');
          
          console.error('Validation error:', errorMessages);
          toast.error(`Validation error: ${errorMessages}`);
          throw new Error(`Validation error: ${errorMessages}`);
        } else {
          // Handle other error detail formats
          console.error('API error:', errorData.detail);
          toast.error(String(errorData.detail));
          throw new Error(String(errorData.detail));
        }
      }

      // Handle other errors
      const errorMessage = errorData.detail || `Error: ${response.status} ${response.statusText}`;
      toast.error(errorMessage);
      throw new Error(errorMessage);
    }

    // For DELETE requests with 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json() as T;
  } catch (error) {
    console.error('API request failed:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    toast.error(`Request failed: ${errorMessage}`);
    throw error;
  }
}

// Client API methods
export const clientApi = {
  getClients: () => apiRequest<Client[]>('/clients/'),
  getClient: (id: number) => apiRequest<Client>(`/clients/${id}`),
  createClient: (client: Omit<Client, 'id' | 'created_at' | 'updated_at'>) => 
    apiRequest<Client>('/clients/', {
      method: 'POST',
      body: JSON.stringify(client),
    }),
  updateClient: (id: number, client: Partial<Client>) => 
    apiRequest<Client>(`/clients/${id}`, {
      method: 'PUT',
      body: JSON.stringify(client),
    }),
  deleteClient: (id: number) => 
    apiRequest(`/clients/${id}`, {
      method: 'DELETE',
    }),
};

// Invoice API methods
export const invoiceApi = {
  getInvoices: (status?: string) => {
    const queryParams = status ? `?status=${status}` : '';
    return apiRequest<Invoice[]>(`/invoices/${queryParams}`);
  },
  getInvoice: async (id: number) => {
    try {
      // Get invoice data
      const invoice = await apiRequest<Invoice>(`/invoices/${id}`);
      
      console.log("API response for invoice:", invoice);
      
      // Initialize items array if missing
      if (!invoice.items) {
        invoice.items = [];
        console.warn("Invoice API response didn't include items array");
      }
      
      // If items exist but they're coming in an unexpected format, handle it
      if (invoice.items && !Array.isArray(invoice.items)) {
        console.warn("Items property exists but is not an array:", invoice.items);
        invoice.items = [];
      }
      
      // For debugging - log what we're returning
      console.log("Returning invoice with items:", invoice.items);
      
      return invoice;
    } catch (error) {
      console.error("Error fetching invoice:", error);
      throw error;
    }
  },
  createInvoice: (invoice: {
    number: string;
    client_id: number;
    date: string;
    due_date: string;
    items: {
      description: string;
      quantity: number;
      price: number;
    }[];
    notes?: string;
  }) => 
    apiRequest<Invoice>('/invoices/', {
      method: 'POST',
      body: JSON.stringify(invoice),
    }),
  updateInvoice: (id: number, invoice: Partial<Invoice>) => 
    apiRequest<Invoice>(`/invoices/${id}`, {
      method: 'PUT',
      body: JSON.stringify(invoice),
    }),
  updateInvoiceItems: (id: number, items: InvoiceItem[]) => 
    apiRequest<Invoice>(`/invoices/${id}/items`, {
      method: 'PUT',
      body: JSON.stringify(items.map(item => ({
        description: item.description,
        quantity: item.quantity,
        price: item.price
      }))),
    }),
  deleteInvoice: (id: number) => 
    apiRequest(`/invoices/${id}`, {
      method: 'DELETE',
    }),
};

// Payment API methods
export const paymentApi = {
  getPayments: () => apiRequest<Payment[]>('/payments/'),
  getPayment: (id: number) => apiRequest<Payment>(`/payments/${id}`),
  createPayment: (payment: {
    invoice_id: number;
    amount: number;
    date: string;
    method: string;
  }) => 
    apiRequest<Payment>('/payments/', {
      method: 'POST',
      body: JSON.stringify(payment),
    }),
  updatePayment: (id: number, payment: Partial<Payment>) => 
    apiRequest<Payment>(`/payments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payment),
    }),
  deletePayment: (id: number) => 
    apiRequest(`/payments/${id}`, {
      method: 'DELETE',
    }),
};

// Dashboard API
export const dashboardApi = {
  getStats: async () => {
    try {
      const [clients, invoices, payments] = await Promise.all([
        clientApi.getClients(),
        invoiceApi.getInvoices(),
        paymentApi.getPayments(),
      ]);
      
      const totalClients = clients.length;
      const totalIncome = payments.reduce((sum, payment) => sum + payment.amount, 0);
      const pendingInvoices = invoices
        .filter(invoice => invoice.status === 'pending' || invoice.status === 'overdue')
        .reduce((sum, invoice) => sum + invoice.amount, 0);
      
      const invoicesPaid = invoices.filter(invoice => invoice.status === 'paid').length;
      const invoicesPending = invoices.filter(invoice => invoice.status === 'pending').length;
      const invoicesOverdue = invoices.filter(invoice => invoice.status === 'overdue').length;
      
      return {
        totalIncome,
        pendingInvoices,
        totalClients,
        invoicesPaid,
        invoicesPending,
        invoicesOverdue,
      };
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      return {
        totalIncome: 0,
        pendingInvoices: 0,
        totalClients: 0,
        invoicesPaid: 0,
        invoicesPending: 0,
        invoicesOverdue: 0,
      };
    }
  }
};

// Settings API methods
export const settingsApi = {
  getSettings: () => apiRequest<Settings>('/settings/'),
  updateSettings: (settings: Partial<Settings>) => 
    apiRequest<Settings>('/settings/', {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
}; 