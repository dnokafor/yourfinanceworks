import { AppLayout } from "@/components/layout/AppLayout";
import { ClientForm } from "@/components/clients/ClientForm";

const NewClient = () => {
  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">Add New Client</h1>
          <p className="text-muted-foreground">Create a new client in your system</p>
        </div>
        
        <ClientForm />
      </div>
    </AppLayout>
  );
};

export default NewClient; 