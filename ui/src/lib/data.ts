
// Sample data for the application

// Client data
export const clientData = [
  {
    id: "1",
    name: "Acme Corporation",
    email: "billing@acme.com",
    phone: "(555) 123-4567",
    address: "123 Main Street, Anytown, CA 12345",
    balance: 1250.75
  },
  {
    id: "2",
    name: "Globex Industries",
    email: "accounts@globex.com",
    phone: "(555) 987-6543",
    address: "456 Tech Avenue, Silicon Valley, CA 94024",
    balance: 3540.20
  },
  {
    id: "3",
    name: "Stark Enterprises",
    email: "finance@stark.com",
    phone: "(555) 333-2222",
    address: "789 Innovation Drive, Future City, NY 10001",
    balance: 0
  },
  {
    id: "4",
    name: "Wayne Industries",
    email: "accounts@wayne.com",
    phone: "(555) 888-9999",
    address: "1 Wayne Tower, Gotham City, NJ 07101",
    balance: 5250.00
  },
  {
    id: "5",
    name: "Daily Planet",
    email: "billing@dailyplanet.com",
    phone: "(555) 111-7890",
    address: "42 Press Street, Metropolis, IL 60007",
    balance: 825.50
  }
];

// Invoice data
export const invoiceData = [
  {
    id: "1",
    number: "INV-001",
    client: "Acme Corporation",
    clientId: "1",
    date: "2025-04-01",
    dueDate: "2025-05-01",
    amount: 750.00,
    status: "paid",
    items: [
      { description: "Website Development", quantity: 1, price: 750.00 }
    ]
  },
  {
    id: "2",
    number: "INV-002",
    client: "Acme Corporation",
    clientId: "1",
    date: "2025-04-15",
    dueDate: "2025-05-15",
    amount: 500.75,
    status: "pending",
    items: [
      { description: "Hosting Services (Annual)", quantity: 1, price: 420.00 },
      { description: "SSL Certificate", quantity: 1, price: 80.75 }
    ]
  },
  {
    id: "3",
    number: "INV-003",
    client: "Globex Industries",
    clientId: "2",
    date: "2025-04-10",
    dueDate: "2025-05-10",
    amount: 3540.20,
    status: "pending",
    items: [
      { description: "Custom Software Development", quantity: 40, price: 85.00 },
      { description: "Project Management", quantity: 5, price: 75.00 }
    ]
  },
  {
    id: "4",
    number: "INV-004",
    client: "Stark Enterprises",
    clientId: "3",
    date: "2025-03-28",
    dueDate: "2025-04-28",
    amount: 1200.00,
    status: "paid",
    items: [
      { description: "UI/UX Design", quantity: 12, price: 100.00 }
    ]
  },
  {
    id: "5",
    number: "INV-005",
    client: "Wayne Industries",
    clientId: "4",
    date: "2025-04-05",
    dueDate: "2025-05-05",
    amount: 5250.00,
    status: "pending",
    items: [
      { description: "Security System Implementation", quantity: 1, price: 4500.00 },
      { description: "Staff Training", quantity: 5, price: 150.00 }
    ]
  },
  {
    id: "6",
    number: "INV-006",
    client: "Daily Planet",
    clientId: "5",
    date: "2025-04-18",
    dueDate: "2025-05-18",
    amount: 825.50,
    status: "overdue",
    items: [
      { description: "Digital Marketing Campaign", quantity: 1, price: 750.00 },
      { description: "Social Media Management", quantity: 1, price: 75.50 }
    ]
  },
  {
    id: "7",
    number: "INV-007",
    client: "Acme Corporation",
    clientId: "1",
    date: "2025-03-15",
    dueDate: "2025-04-15",
    amount: 350.00,
    status: "overdue",
    items: [
      { description: "Maintenance Services", quantity: 5, price: 70.00 }
    ]
  }
];

// Payment data
export const paymentData = [
  {
    id: "1",
    invoiceId: "1",
    client: "Acme Corporation",
    amount: 750.00,
    date: "2025-04-20",
    method: "Credit Card"
  },
  {
    id: "2",
    invoiceId: "4",
    client: "Stark Enterprises",
    amount: 1200.00,
    date: "2025-04-15",
    method: "Bank Transfer"
  }
];

// Dashboard statistics
export const dashboardStats = {
  totalIncome: 1950.00,
  pendingInvoices: 10115.45,
  totalClients: 5,
  invoicesPaid: 2,
  invoicesPending: 3,
  invoicesOverdue: 2
};
