
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useIsMobile } from "@/hooks/use-mobile";
import { 
  BarChart, 
  ChevronLeft, 
  DollarSign, 
  FileText, 
  Settings, 
  Users 
} from "lucide-react";

export function AppSidebar() {
  const location = useLocation();
  const isMobile = useIsMobile();
  const [open, setOpen] = useState(!isMobile);

  const menuItems = [
    { 
      path: '/', 
      label: 'Dashboard', 
      icon: <BarChart className="w-5 h-5" /> 
    },
    { 
      path: '/clients', 
      label: 'Clients', 
      icon: <Users className="w-5 h-5" /> 
    },
    { 
      path: '/invoices', 
      label: 'Invoices', 
      icon: <FileText className="w-5 h-5" /> 
    },
    { 
      path: '/payments', 
      label: 'Payments', 
      icon: <DollarSign className="w-5 h-5" /> 
    },
    { 
      path: '/settings', 
      label: 'Settings', 
      icon: <Settings className="w-5 h-5" /> 
    }
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <>
      <Sidebar>
        <SidebarHeader className="py-6 px-2 border-b border-sidebar-border">
          <div className="flex justify-center items-center">
            <span className="text-2xl font-bold text-white">InvoiceApp</span>
          </div>
        </SidebarHeader>
        <SidebarContent className="pt-6">
          <SidebarMenu>
            {menuItems.map((item) => (
              <SidebarMenuItem key={item.path}>
                <SidebarMenuButton asChild 
                  className={isActive(item.path) ? "bg-sidebar-accent text-white" : "text-sidebar-foreground/80 hover:text-white"}
                >
                  <Link to={item.path} className="flex items-center gap-3 px-3 py-2">
                    {item.icon}
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarContent>
        <SidebarFooter className="py-4 px-2 border-t border-sidebar-border">
          <div className="flex justify-center">
            <Button variant="outline" size="sm" className="text-white border-sidebar-border">
              Log Out
            </Button>
          </div>
        </SidebarFooter>
      </Sidebar>
      <div className="fixed top-4 left-4 z-50">
        <SidebarTrigger>
          <Button 
            variant="outline" 
            size="icon" 
            className={`rounded-full ${!open ? 'bg-white shadow-md' : 'bg-transparent border-none'}`}
          >
            <ChevronLeft className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`} />
          </Button>
        </SidebarTrigger>
      </div>
    </>
  );
}
