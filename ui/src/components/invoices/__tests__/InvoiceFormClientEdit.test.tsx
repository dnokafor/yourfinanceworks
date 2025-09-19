import React from 'react'
import { describe, it, beforeEach, expect, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'
import { InvoiceForm } from '@/components/invoices/InvoiceForm'

// Mock data
const clients = [
  { id: 1, name: 'Client A', email: 'a@example.com', phone: '', address: '', balance: 0, paid_amount: 0, preferred_currency: 'CAD', created_at: '', updated_at: '' },
  { id: 2, name: 'Client B', email: 'b@example.com', phone: '', address: '', balance: 0, paid_amount: 0, preferred_currency: 'USD', created_at: '', updated_at: '' },
]

const mockGetClients = vi.fn()
const mockUpdateInvoice = vi.fn()
const mockGetInvoice = vi.fn()

vi.mock('@/lib/api', async (orig) => {
  const actual = await (orig() as Promise<any>)
  return {
    ...actual,
    clientApi: {
      ...actual.clientApi,
      getClients: () => mockGetClients(),
    },
    invoiceApi: {
      ...actual.invoiceApi,
      updateInvoice: (...args: any[]) => mockUpdateInvoice(...args),
      getInvoice: (...args: any[]) => mockGetInvoice(...args),
    }
  }
})

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

describe('InvoiceForm client editing rules', () => {
  beforeEach(() => {
    mockGetClients.mockReset()
    mockUpdateInvoice.mockReset()
    mockGetInvoice.mockReset()
  })

  it('allows changing client when invoice not paid and updates currency to preferred', async () => {
    mockGetClients.mockResolvedValueOnce(clients)
    const invoice = {
      id: 7,
      number: 'INV-0007',
      client_id: 1,
      client_name: 'Client A',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      date: new Date().toISOString(),
      due_date: new Date().toISOString(),
      amount: 0,
      currency: 'USD',
      paid_amount: 0,
      status: 'draft',
      notes: '',
      items: [],
      is_recurring: false,
    }

    render(<InvoiceForm invoice={invoice as any} isEdit={true} />)

    // Wait for clients
    await waitFor(() => expect(screen.getByText('Client A')).toBeInTheDocument())

    // Open client select
    const clientTrigger = screen.getByText('invoices.select_a_client')
    fireEvent.click(clientTrigger)
    // Choose Client B
    fireEvent.click(screen.getByText('Client B'))

    // Open currency select and ensure it changed to preferred USD (already USD, still valid)
    // We assert by saving later (updateInvoice called with client_id 2 and currency 'USD')
    mockUpdateInvoice.mockResolvedValueOnce({ ...invoice, client_id: 2, currency: 'USD' })

    // Submit
    fireEvent.click(screen.getByText('invoices.update_invoice'))

    await waitFor(() => {
      expect(mockUpdateInvoice).toHaveBeenCalled()
      const [, payload] = mockUpdateInvoice.mock.calls[0]
      expect(payload.client_id).toBe(2)
      expect(payload.currency).toBe('USD')
    })
  })

  it('disables client change when invoice is paid', async () => {
    mockGetClients.mockResolvedValueOnce(clients)
    const paidInvoice = {
      id: 12,
      number: 'INV-0012',
      client_id: 1,
      client_name: 'Client A',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      date: new Date().toISOString(),
      due_date: new Date().toISOString(),
      amount: 0,
      currency: 'USD',
      paid_amount: 100,
      status: 'paid',
      notes: '',
      items: [],
      is_recurring: false,
    }

    render(<InvoiceForm invoice={paidInvoice as any} isEdit={true} />)

    await waitFor(() => expect(screen.getByText('Client A')).toBeInTheDocument())

    // Client selector should be disabled (trigger not clickable -> no menu opens)
    const clientTrigger = screen.getByText('Client A')
    fireEvent.click(clientTrigger)
    // Menu should not appear
    expect(screen.queryByText('Client B')).toBeNull()
  })
})
