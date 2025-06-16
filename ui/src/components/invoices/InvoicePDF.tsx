import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import { Invoice } from '@/lib/api';

// Create styles
const styles = StyleSheet.create({
  page: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    padding: 40,
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  companyInfo: {
    fontSize: 12,
    color: '#666',
    marginBottom: 20,
  },
  section: {
    marginBottom: 20,
  },
  row: {
    flexDirection: 'row',
    marginBottom: 5,
  },
  label: {
    width: 100,
    fontSize: 10,
    color: '#666',
  },
  value: {
    flex: 1,
    fontSize: 10,
  },
  table: {
    marginTop: 20,
  },
  tableHeader: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#000',
    paddingBottom: 5,
    marginBottom: 5,
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 5,
  },
  tableCell: {
    fontSize: 10,
  },
  col1: {
    width: '40%',
  },
  col2: {
    width: '15%',
    textAlign: 'right',
  },
  col3: {
    width: '15%',
    textAlign: 'right',
  },
  col4: {
    width: '30%',
    textAlign: 'right',
  },
  total: {
    marginTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#000',
    paddingTop: 10,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 5,
  },
  totalLabel: {
    width: 100,
    fontSize: 10,
    textAlign: 'right',
  },
  totalValue: {
    width: 100,
    fontSize: 10,
    textAlign: 'right',
    fontWeight: 'bold',
  },
  notes: {
    marginTop: 30,
    fontSize: 10,
    color: '#666',
  },
});

interface InvoicePDFProps {
  invoice: Invoice;
  companyName: string;
}

export const InvoicePDF = ({ invoice, companyName }: InvoicePDFProps) => (
  <Document>
    <Page size="A4" style={styles.page}>
      <View style={styles.header}>
        <Text style={styles.title}>INVOICE</Text>
        <Text style={styles.companyInfo}>{companyName}</Text>
      </View>

      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.label}>Invoice Number:</Text>
          <Text style={styles.value}>{invoice.number}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Date:</Text>
          <Text style={styles.value}>{invoice.date}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Due Date:</Text>
          <Text style={styles.value}>{invoice.due_date}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Status:</Text>
          <Text style={styles.value}>{invoice.status}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={[styles.label, { marginBottom: 5 }]}>Bill To:</Text>
        <Text style={styles.value}>{invoice.client_name}</Text>
        <Text style={styles.value}>{invoice.client_email}</Text>
      </View>

      <View style={styles.table}>
        <View style={styles.tableHeader}>
          <Text style={[styles.tableCell, styles.col1]}>Description</Text>
          <Text style={[styles.tableCell, styles.col2]}>Quantity</Text>
          <Text style={[styles.tableCell, styles.col3]}>Price</Text>
          <Text style={[styles.tableCell, styles.col4]}>Amount</Text>
        </View>
        {invoice.items.map((item, index) => (
          <View key={index} style={styles.tableRow}>
            <Text style={[styles.tableCell, styles.col1]}>{item.description}</Text>
            <Text style={[styles.tableCell, styles.col2]}>{item.quantity}</Text>
            <Text style={[styles.tableCell, styles.col3]}>${item.price.toFixed(2)}</Text>
            <Text style={[styles.tableCell, styles.col4]}>${item.amount.toFixed(2)}</Text>
          </View>
        ))}
      </View>

      <View style={styles.total}>
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Subtotal:</Text>
          <Text style={styles.totalValue}>${invoice.amount.toFixed(2)}</Text>
        </View>
        {invoice.paid_amount > 0 && (
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Paid Amount:</Text>
            <Text style={styles.totalValue}>${invoice.paid_amount.toFixed(2)}</Text>
          </View>
        )}
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Balance Due:</Text>
          <Text style={styles.totalValue}>${(invoice.amount - (invoice.paid_amount || 0)).toFixed(2)}</Text>
        </View>
      </View>

      {invoice.notes && (
        <View style={styles.notes}>
          <Text style={[styles.label, { marginBottom: 5 }]}>Notes:</Text>
          <Text>{invoice.notes}</Text>
        </View>
      )}
    </Page>
  </Document>
); 