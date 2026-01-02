import React from "react";
import { SearchStatus } from "@/components/search/SearchStatus";

interface SearchSettingsTabProps {
    isAdmin: boolean;
}

export const SearchSettingsTab: React.FC<SearchSettingsTabProps> = ({ isAdmin }) => {
    return (
        <div className="space-y-6">
            <SearchStatus />
        </div>
    );
};
