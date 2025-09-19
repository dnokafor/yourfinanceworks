import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

interface TenantProtectedRouteProps {
  children: React.ReactNode;
  requirePrimaryTenant?: boolean;
  requireSuperUser?: boolean;
  redirectTo?: string;
}

export function TenantProtectedRoute({ 
  children, 
  requirePrimaryTenant = false,
  requireSuperUser = false,
  redirectTo = '/' 
}: TenantProtectedRouteProps) {
  const navigate = useNavigate();
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAccess = () => {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const selectedTenantId = localStorage.getItem('selected_tenant_id');
      const currentTenantId = selectedTenantId || user?.tenant_id?.toString();

      if (requireSuperUser && !user?.is_superuser) {
        toast.error('Super admin access required');
        navigate(redirectTo, { replace: true });
        return;
      }

      if (requirePrimaryTenant && currentTenantId !== user?.tenant_id?.toString()) {
        toast.error('Access restricted to home organization');
        navigate(redirectTo, { replace: true });
        return;
      }

      setIsAuthorized(true);
    };

    checkAccess();
  }, [requirePrimaryTenant, requireSuperUser, navigate, redirectTo]);

  if (isAuthorized === null) {
    return <div>Checking access...</div>;
  }

  return isAuthorized ? <>{children}</> : null;
}