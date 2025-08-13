import { useMemo, useState } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CalendarIcon, Upload } from 'lucide-react';
import { format } from 'date-fns';
import { bankStatementApi, BankTransactionEntry } from '@/lib/api';
import { toast } from 'sonner';

const CATEGORY_OPTIONS = [
  'Income', 'Food', 'Transportation', 'Shopping', 'Bills', 'Healthcare', 'Entertainment', 'Financial', 'Travel', 'Other'
];

export default function BankStatements() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<BankTransactionEntry[]>([]);
  const [previewOpen, setPreviewOpen] = useState(false);

  const onUpload = async () => {
    try {
      if (files.length === 0) { toast.error('Select up to 12 PDF files'); return; }
      setLoading(true);
      const resp = await bankStatementApi.uploadAndExtract(files);
      setRows(resp.transactions.map(t => ({
        date: t.date,
        description: t.description,
        amount: t.amount,
        transaction_type: (t.transaction_type === 'debit' || t.transaction_type === 'credit') ? t.transaction_type : (t.amount < 0 ? 'debit' : 'credit'),
        balance: t.balance ?? null,
        category: t.category ?? null,
      })));
      toast.success(`Extracted ${resp.count} transactions`);
    } catch (e: any) {
      toast.error(e?.message || 'Failed to extract transactions');
    } finally {
      setLoading(false);
    }
  };

  const addEmptyRow = () => {
    const today = new Date();
    const iso = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())).toISOString().split('T')[0];
    setRows(prev => ([...prev, { date: iso, description: '', amount: 0, transaction_type: 'debit', balance: null, category: 'Other' }]));
  };

  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Bank Statements</h1>
            <p className="text-muted-foreground">Upload up to 12 PDF statements and review extracted transactions.</p>
          </div>
          <div className="flex items-center gap-2">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <Upload className="w-4 h-4" />
              <input type="file" accept="application/pdf" multiple className="hidden" onChange={(e) => {
                const list = Array.from(e.target.files || []).slice(0, 12);
                setFiles(list);
              }} />
              {files.length > 0 ? `${files.length} file(s)` : 'Select PDFs'}
            </label>
            <Button onClick={onUpload} disabled={loading || files.length === 0}>{loading ? 'Processing...' : 'Process'}</Button>
            <Button variant="outline" onClick={addEmptyRow}>Add Entry</Button>
          </div>
        </div>

        <Card className="slide-in">
          <CardHeader>
            <CardTitle>Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Balance</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Category</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((r, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button variant="outline" className="w-[160px] justify-start text-left font-normal">
                              <CalendarIcon className="mr-2 h-4 w-4" />
                              {r.date ? format(new Date(r.date), 'PPP') : 'Pick a date'}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                              mode="single"
                              selected={r.date ? new Date(r.date) : undefined}
                              onSelect={(d) => {
                                if (!d) return;
                                const iso = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())).toISOString().split('T')[0];
                                setRows(prev => prev.map((x, i) => i === idx ? { ...x, date: iso } : x));
                              }}
                              initialFocus
                            />
                          </PopoverContent>
                        </Popover>
                      </TableCell>
                      <TableCell>
                        <Input value={r.description} onChange={(e) => setRows(prev => prev.map((x, i) => i === idx ? { ...x, description: e.target.value } : x))} />
                      </TableCell>
                      <TableCell>
                        <Input type="number" value={Number(r.amount)} onChange={(e) => setRows(prev => prev.map((x, i) => i === idx ? { ...x, amount: Number(e.target.value) } : x))} />
                      </TableCell>
                      <TableCell>
                        <Input type="number" value={r.balance ?? ''} onChange={(e) => setRows(prev => prev.map((x, i) => i === idx ? { ...x, balance: e.target.value === '' ? null : Number(e.target.value) } : x))} />
                      </TableCell>
                      <TableCell>
                        <Select value={r.transaction_type} onValueChange={(v) => setRows(prev => prev.map((x, i) => i === idx ? { ...x, transaction_type: v as 'debit' | 'credit' } : x))}>
                          <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="debit">debit (expense)</SelectItem>
                            <SelectItem value="credit">credit (income)</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Select value={r.category || 'Other'} onValueChange={(v) => setRows(prev => prev.map((x, i) => i === idx ? { ...x, category: v } : x))}>
                          <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {CATEGORY_OPTIONS.map((c) => (<SelectItem key={c} value={c}>{c}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}


