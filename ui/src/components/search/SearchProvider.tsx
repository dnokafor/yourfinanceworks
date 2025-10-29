import { createContext, useContext, useState } from "react";
import { useTranslation } from "react-i18next";

interface SearchContextType {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export function SearchProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <SearchContext.Provider value={{ isOpen, setIsOpen }}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  const { t } = useTranslation();
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error(t('search.provider_error'));
  }
  return context;
}
