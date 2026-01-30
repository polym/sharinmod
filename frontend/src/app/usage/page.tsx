"use client";

import { BarChart3 } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";

export default function UsagePage() {
  return (
    <div className="max-w-7xl mx-auto p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">使用情况</h1>
        <p className="text-sm text-gray-500">查看 API 调用统计和用量分析</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-white shadow-sm">
          <CardContent className="p-6">
            <div className="text-sm text-gray-500 mb-1">本月调用次数</div>
            <div className="text-3xl font-semibold text-gray-900">0</div>
            <div className="text-xs text-gray-400 mt-1">上月：0</div>
          </CardContent>
        </Card>

        <Card className="bg-white shadow-sm">
          <CardContent className="p-6">
            <div className="text-sm text-gray-500 mb-1">活跃 API Keys</div>
            <div className="text-3xl font-semibold text-gray-900">0</div>
            <div className="text-xs text-gray-400 mt-1">共 0 个 Keys</div>
          </CardContent>
        </Card>

        <Card className="bg-white shadow-sm">
          <CardContent className="p-6">
            <div className="text-sm text-gray-500 mb-1">共享用量</div>
            <div className="text-3xl font-semibold text-gray-900">0</div>
            <div className="text-xs text-gray-400 mt-1">被使用次数</div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">使用趋势</h2>
          <div className="py-16 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
              <BarChart3 className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-gray-500 text-sm">暂无使用数据</p>
            <p className="text-gray-400 text-xs mt-1">开始使用 API Keys 后这里将显示统计图表</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
