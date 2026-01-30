'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { useAuthStore } from '@/lib/store';
import { tokenAPI } from '@/lib/services';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [unifiedTokens, setUnifiedTokens] = useState<any[]>([]);
  const [selectedTokenId, setSelectedTokenId] = useState('');
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

    loadUnifiedTokens();

    // Check if we have a tokenId from discovery page
    const tokenId = searchParams.get('tokenId');
    if (tokenId) {
      // For now, we'll create a temporary unified token or handle this differently
      // In a real implementation, you might want to allow direct usage
      toast({
        title: '提示',
        description: '请先创建统一token来使用发现的tokens',
      });
    }
  }, [isAuthenticated, router, searchParams]);

  const loadUnifiedTokens = async () => {
    try {
      const response = await tokenAPI.getMyUnifiedTokens();
      setUnifiedTokens(response.data.items);
    } catch (error) {
      console.error('Failed to load unified tokens:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedTokenId) {
      toast({
        title: '错误',
        description: '请输入消息并选择token',
        variant: 'destructive',
      });
      return;
    }

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const selectedToken = unifiedTokens.find(t => t.id.toString() === selectedTokenId);
      if (!selectedToken) {
        throw new Error('Selected token not found');
      }

      const response = await tokenAPI.consumeChatCompletion(
        {
          model: 'glm-4.7', // Default model
          messages: [...messages, userMessage],
          temperature: 0.7,
          max_tokens: 1000,
        },
        selectedToken.token // Assuming the token field contains the unified token
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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">AI 聊天</h1>
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              返回仪表板
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <Card className="h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle>与AI对话</CardTitle>
            <CardDescription>
              使用您的统一token与AI模型进行对话
            </CardDescription>
            <div className="flex gap-4">
              <Select value={selectedTokenId} onValueChange={setSelectedTokenId}>
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="选择统一token" />
                </SelectTrigger>
                <SelectContent>
                  {unifiedTokens.map((token) => (
                    <SelectItem key={token.id} value={token.id.toString()}>
                      {token.name}
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
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      {message.content}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-200 text-gray-900 rounded-lg px-4 py-2">
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
                disabled={loading || !selectedTokenId}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={loading || !input.trim() || !selectedTokenId}
              >
                {loading ? '发送中...' : '发送'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}