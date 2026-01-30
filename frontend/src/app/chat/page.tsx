'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { useAuthStore } from '@/lib/store';
import { apiKeyAPI } from '@/lib/services';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function ChatPageContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [unifiedAPIKeys, setUnifiedAPIKeys] = useState<any[]>([]);
  const [selectedAPIKeyId, setSelectedAPIKeyId] = useState('');
  const [tempToken, setTempToken] = useState<string | null>(null);
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    loadUnifiedAPIKeys();

    // Check if we have a apiKeyId from discovery page
    const apiKeyId = searchParams.get('apiKeyId');
    if (apiKeyId) {
      // For now, we'll create a temporary unified API key or handle this differently
      // In a real implementation, you might want to allow direct usage
      toast({
        title: '提示',
        description: '请先创建统一API Key来使用发现的API Keys',
      });
    }
  }, [isAuthenticated, router, searchParams]);

  const loadUnifiedAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMyUnifiedAPIKeys();
      setUnifiedAPIKeys(response.data.items);
    } catch (error) {
      console.error('Failed to load unified API keys:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedAPIKeyId) {
      toast({
        title: '错误',
        description: '请输入消息并选择API Key',
        variant: 'destructive',
      });
      return;
    }

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const selectedAPIKey = unifiedAPIKeys.find(t => t.id.toString() === selectedAPIKeyId);
      if (!selectedAPIKey) {
        throw new Error('Selected API key not found');
      }

      const response = await apiKeyAPI.consumeChatCompletion(
        {
          model: 'glm-4.7', // Default model
          messages: [...messages, userMessage],
          temperature: 0.7,
          max_tokens: 1000,
        },
        selectedAPIKey.api_key // The api_key field contains the unified API key
      );

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.choices[0].message.content,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.message || '发送消息失败',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <Card className="h-[calc(100vh-12rem)] min-h-[500px] max-h-[800px] flex flex-col">
        <CardHeader>
          <CardTitle>与AI对话</CardTitle>
          <CardDescription>
            选择一个统一 API Key 开始聊天
          </CardDescription>
          <div className="flex gap-4">
            <Select value={selectedAPIKeyId} onValueChange={setSelectedAPIKeyId}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="选择统一API Key" />
              </SelectTrigger>
              <SelectContent>
                {unifiedAPIKeys.map((apiKey) => (
                  <SelectItem key={apiKey.id} value={apiKey.id.toString()}>
                    {apiKey.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col">
          <ScrollArea className="flex-1 pr-4">
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-2 ${
                      message.role === 'user'
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                    AI正在思考...
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="flex gap-2 mt-4">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的消息..."
              disabled={loading || !selectedAPIKeyId}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={loading || !input.trim() || !selectedAPIKeyId}
            >
              {loading ? '发送中...' : '发送'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-64"><div className="text-gray-500">加载中...</div></div>}>
      <ChatPageContent />
    </Suspense>
  );
}