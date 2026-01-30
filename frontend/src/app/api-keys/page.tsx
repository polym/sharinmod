"use client";

import { Key, Plus } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ApiKeysPage() {
  return (
    <div className="max-w-7xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">API Keys</h1>
          <p className="text-sm text-gray-500">管理你的 API 密钥</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          添加 API Key
        </Button>
      </div>

      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <div className="py-16 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
              <Key className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无 API Keys</h3>
            <p className="text-gray-500 text-sm max-w-md mx-auto mb-4">
              添加你的 API Keys 开始使用。支持 OpenAI, Anthropic, Google 等主流供应商。
            </p>
            <Button variant="outline">
              <Plus className="w-4 h-4 mr-2" />
              添加第一个 API Key
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
