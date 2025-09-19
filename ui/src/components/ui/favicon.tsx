import { useEffect } from 'react';
import { API_BASE_URL } from '@/lib/api';

interface FaviconProps {
  logoUrl?: string;
  companyName?: string;
}

export function Favicon({ logoUrl, companyName }: FaviconProps) {
  useEffect(() => {
    const updateFavicon = () => {
      // Remove existing favicon links
      const existingLinks = document.querySelectorAll('link[rel*="icon"]');
      existingLinks.forEach(link => link.remove());

      if (logoUrl) {
        // Use company logo as favicon
        const link = document.createElement('link');
        link.rel = 'icon';
        link.type = 'image/x-icon';
        link.href = `${API_BASE_URL}${logoUrl}`;
        document.head.appendChild(link);

        // Also add apple-touch-icon for mobile
        const appleLink = document.createElement('link');
        appleLink.rel = 'apple-touch-icon';
        appleLink.href = `${API_BASE_URL}${logoUrl}`;
        document.head.appendChild(appleLink);
      } else {
        // Use default favicon
        const link = document.createElement('link');
        link.rel = 'icon';
        link.type = 'image/x-icon';
        link.href = '/favicon.ico';
        document.head.appendChild(link);
      }

      // Update document title with company name
      if (companyName) {
        document.title = `${companyName} - Invoice Management`;
      } else {
        document.title = 'Invoice Management';
      }
    };

    updateFavicon();
  }, [logoUrl, companyName]);

  return null; // This component doesn't render anything
}