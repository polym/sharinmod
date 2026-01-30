"use client";

import { useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import { CardContent, Card } from "@/components/ui/card";

type UserRead = {
  id: number;
  name: string;
  email: string;
  // Add other fields as needed
};

type APIKeyRead = {
  id: number;
  name: string;
  provider: string;
  // Add other fields as needed
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const SharimodDashboard = () => {
  const [users, setUsers] = useState<UserRead[] | null>(null);
  const [apiKeys, setAPIKeys] = useState<APIKeyRead[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // TODO: Replace with actual sharinmod API endpoints
        // const usersResponse = await fetch(`${API_BASE_URL}/users/`);
        // const apiKeysResponse = await fetch(`${API_BASE_URL}/api-keys/`);

        // For now, show placeholder data
        setUsers([]);
        setAPIKeys([]);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load data. Please check if the backend is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <header className="flex items-center justify-between p-6 border-b dark:border-gray-800">
          <h1 className="text-2xl font-bold">Sharinmod - API Token Sharing Platform</h1>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Loading dashboard...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <header className="flex items-center justify-between p-6 border-b dark:border-gray-800">
          <h1 className="text-2xl font-bold">Sharinmod - API Token Sharing Platform</h1>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-600 mb-4">⚠️ {error}</div>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="flex items-center justify-between p-6 border-b dark:border-gray-800">
        <h1 className="text-2xl font-bold">Sharinmod - API Token Sharing Platform</h1>
        <Button className="dark:border-gray-300" variant="outline">
          Refresh Data
        </Button>
      </header>

      <main className="flex-1 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Users</h2>
              <p className="text-gray-600 dark:text-gray-400">
                Total registered users: {users?.length || 0}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                User management features coming soon...
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Shared API Keys</h2>
              <p className="text-gray-600 dark:text-gray-400">
                Available API keys: {apiKeys?.length || 0}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                API key sharing features coming soon...
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 text-center text-gray-500">
          <p>🚧 This is the initial setup. User registration and API key sharing features will be implemented in upcoming stories.</p>
        </div>
      </main>
    </div>
  );
};

export default function Home() {
  return <SharimodDashboard />;
}
