"use client";

import { useEffect, useState } from 'react';
import { Key } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";

type APIKeyRead = {
  id: number;
  name: string;
  provider: string;
};

interface ActivityItemProps {
  user: string;
  action: string;
  time: string;
}

function ActivityItem({ user, action, time }: ActivityItemProps) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
        {user.charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm">
          <span className="font-medium text-gray-900">{user}</span>
          {' '}
          <span className="text-gray-600">{action}</span>
        </p>
        <p className="text-xs text-gray-500 mt-0.5">{time}</p>
      </div>
    </div>
  );
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function MarketplacePage() {
  const [apiKeys, setAPIKeys] = useState<APIKeyRead[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // TODO: Replace with actual sharinmod API endpoints
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
      <div className="max-w-7xl mx-auto p-8">
        <div className="text-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-8">
        <div className="text-center py-16">
          <div className="text-red-600 mb-4">⚠️ {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <div className="flex gap-8">
        {/* API Keys Section */}
        <div className="flex-1">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-gray-900 mb-2">广场</h1>
            <p className="text-sm text-gray-500">发现社区共享的 API Keys</p>
          </div>

          <Card className="bg-white shadow-sm">
            <CardContent className="p-6">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-1">发现可用的 API Keys</h2>
                <p className="text-sm text-gray-500">浏览社区分享的 API Keys，使用它们进行API调用或构建应用</p>
              </div>

              {/* Filter */}
              <div className="mb-6">
                <Select defaultValue="all">
                  <SelectTrigger className="w-64">
                    <SelectValue placeholder="选择分类" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                    <SelectItem value="google">Google</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Empty State or API Keys List */}
              {apiKeys && apiKeys.length === 0 ? (
                <div className="py-16 text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                    <Key className="w-8 h-8 text-purple-600" />
                  </div>
                  <p className="text-gray-500 text-sm">暂无可用的 API Keys</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {apiKeys?.map((key) => (
                    <div key={key.id} className="p-4 border border-purple-100 rounded-lg">
                      <p className="font-medium">{key.name}</p>
                      <p className="text-sm text-gray-500">{key.provider}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity Sidebar */}
        <div className="w-80 hidden xl:block">
          <Card className="bg-gradient-to-br from-purple-50 to-white shadow-sm">
            <CardContent className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Recent Activity</h3>
              
              <div className="space-y-4">
                <ActivityItem 
                  user="xinmada"
                  action="deployed"
                  time="over 2 years ago"
                />
                <ActivityItem 
                  user="xinmada"
                  action="deployed"
                  time="over 2 years ago"
                />
                <ActivityItem 
                  user="libchat"
                  action="updated"
                  time="over 2 years ago"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
