'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
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
  const t = useTranslations('chat');
  const tToast = useTranslations('chat.toast');
  const tCommon = useTranslations('common');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [unifiedAPIKeys, setUnifiedAPIKeys] = useState<any[]>([]);
  const [selectedAPIKeyId, setSelectedAPIKeyId] = useState('');
  const [tempToken, setTempToken] = useState<string | null>(null);
  const { isAuthenticated, setShowLoginDialog } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    loadUnifiedAPIKeys();

    // Check if we have a apiKeyId from discovery page
    const apiKeyId = searchParams.get('apiKeyId');
    if (apiKeyId) {
      // For now, we'll create a temporary unified API key or handle this differently
      // In a real implementation, you might want to allow direct usage
      toast({
        title: tToast('noKeyTitle'),
        description: tToast('noKeyDescription'),
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
        title: tToast('noInputTitle'),
        description: tToast('noInputDescription'),
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
        title: tCommon('error'),
        description: error.response?.data?.message || tToast('sendFailed'),
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
          <CardTitle>{t('title')}</CardTitle>
          <CardDescription>
            {t('description')}
          </CardDescription>
          <div className="flex gap-4">
            <Select value={selectedAPIKeyId} onValueChange={setSelectedAPIKeyId}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder={t('selectApiKey')} />
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
                    {t('thinking')}
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
              placeholder={t('placeholder')}
              disabled={loading || !selectedAPIKeyId}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={loading || !input.trim() || !selectedAPIKeyId}
            >
              {loading ? t('sending') : t('send')}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ChatPage() {
  const tCommon = useTranslations('common');
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-64"><div className="text-gray-500">{tCommon('loading')}</div></div>}>
      <ChatPageContent />
    </Suspense>
  );
}