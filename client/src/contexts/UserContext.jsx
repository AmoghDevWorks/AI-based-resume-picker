import React, { createContext, useContext, useState } from 'react';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
    const [results, setResults] = useState(null);
    const [csvData, setCsvData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    return (
        <UserContext.Provider value={{
            results, setResults,
            csvData, setCsvData,
            loading, setLoading,
            error, setError
        }}>
            {children}
        </UserContext.Provider>
    );
};

export const useUser = () => useContext(UserContext);
