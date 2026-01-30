"use client";

import { Users } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";

export default function SharedPage() {
  return (
    <div className="max-w-7xl mx-auto p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">我的共享</h1>
        <p className="text-sm text-gray-500">管理你分享给社区的 API Keys</p>
      </div>

      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <div className="py-16 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
              <Users className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">尚未共享任何 API Key</h3>
            <p className="text-gray-500 text-sm max-w-md mx-auto">
              开始分享你的 API Keys 给社区，让其他用户也能使用它们进行开发。
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
