"use client";

import * as React from "react";
import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Copy, Check } from "lucide-react";
import { useToast } from "@/components/ui/toast";
import { modelAPI } from "@/lib/services";
import type { ModelInfo } from "@/types/model";
import { useTranslations } from "next-intl";

// Constants
const COPY_FEEDBACK_DURATION = 1500; // ms
const DIALOG_MAX_HEIGHT = "85vh";
const BASE_URL_PLACEHOLDER = "https://your-domain.com";
const LOCAL_STORAGE_KEY = "sharinmod-last-selected-model";

interface QuickCallDialogProps {
  children?: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  initialModelName?: string;
}

export function QuickCallDialog({
  children,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
  initialModelName,
}: QuickCallDialogProps) {
  const t = useTranslations('quickCall');
  const tToast = useTranslations('quickCall.toast');
  const tAria = useTranslations('quickCall.ariaLabels');

  // 受控/非受控模式
  const isControlled = controlledOpen !== undefined;
  const [internalOpen, setInternalOpen] = useState(false);
  const open = isControlled ? controlledOpen : internalOpen;
  const setOpen = isControlled ? controlledOnOpenChange! : setInternalOpen;

  const [copiedTab, setCopiedTab] = useState<string | null>(null);
  const [baseUrl, setBaseUrl] = useState(BASE_URL_PLACEHOLDER);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);

  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    // Get base URL on client side
    if (typeof window !== "undefined") {
      setBaseUrl(window.location.origin);
    }
  }, []);

  // 加载模型列表并初始化选中模型
  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await modelAPI.getModels();
        const modelList = response.data.items;
        setModels(modelList);

        if (modelList.length > 0) {
          let targetModel: ModelInfo | undefined;

          // 优先级: initialModelName > localStorage > 第一个模型
          if (initialModelName) {
            targetModel = modelList.find((model: ModelInfo) => model.model_name === initialModelName);
          }

          if (!targetModel && typeof window !== "undefined") {
            try {
              const lastModelName = localStorage.getItem(LOCAL_STORAGE_KEY);
              if (lastModelName) {
                targetModel = modelList.find((model: ModelInfo) => model.model_name === lastModelName);
              }
            } catch (e) {
              console.warn("localStorage access failed:", e);
            }
          }

          if (!targetModel) {
            targetModel = modelList[0];
          }

          setSelectedModel(targetModel ?? null);
        }
      } catch (error) {
        console.error("Failed to load models:", error);
        toast({
          title: tToast('loadFailed'),
          description: tToast('loadFailedDesc'),
          variant: "destructive",
        });
      } finally {
        setLoadingModels(false);
      }
    };

    if (open) {
      loadModels();
    }
  }, [open, initialModelName, toast, tToast]);

  const resetCopyState = (): void => {
    setTimeout(() => setCopiedTab(null), COPY_FEEDBACK_DURATION);
  };

  const handleCopy = async (code: string, tabId: string): Promise<void> => {
    const legacyCopy = (): boolean => {
      let textArea: HTMLTextAreaElement | null = null;
      try {
        textArea = document.createElement("textarea");
        textArea.value = code;
        textArea.style.position = "absolute";
        textArea.style.left = "-9999px";
        textArea.style.top = (window.pageYOffset || document.documentElement.scrollTop) + "px";
        textArea.setAttribute("readonly", "");
        textArea.style.border = "0";
        textArea.style.padding = "0";
        textArea.style.margin = "0";
        textArea.style.fontSize = "16px";
        textArea.style.width = "1px";
        textArea.style.height = "1px";

        const dialogContent = document.querySelector('[role="dialog"]');
        const container = dialogContent || document.body;
        container.appendChild(textArea);

        textArea.contentEditable = "true";
        textArea.readOnly = false;

        const range = document.createRange();
        range.selectNodeContents(textArea);
        const selection = window.getSelection();
        if (selection) {
          selection.removeAllRanges();
          selection.addRange(range);
        }

        textArea.select();
        textArea.setSelectionRange(0, code.length);

        const success = document.execCommand("copy");

        if (selection) {
          selection.removeAllRanges();
        }

        return success;
      } catch (error) {
        console.error("Legacy copy error:", error);
        return false;
      } finally {
        if (textArea && textArea.parentNode) {
          textArea.parentNode.removeChild(textArea);
        }
      }
    };

    const isSecureContext = window.isSecureContext;

    if (isSecureContext) {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(code);
          setCopiedTab(tabId);
          resetCopyState();
          return;
        }
      } catch (err) {
        console.warn("Clipboard API failed, falling back to execCommand:", err);
      }
    }

    const success = legacyCopy();
    if (success) {
      setCopiedTab(tabId);
      resetCopyState();
    } else {
      toast({
        title: tToast('copyFailed'),
        description: tToast('copyFailedDesc'),
        variant: "destructive",
      });
    }
  };

  const handleCreateAPIKey = (): void => {
    try {
      router.push("/api-keys");
      setOpen(false);
    } catch (err) {
      console.error("Navigation failed:", err);
      toast({
        title: tToast('navigationFailed'),
        description: tToast('navigationFailedDesc'),
        variant: "destructive",
      });
    }
  };

  const handleModelChange = (model_name: string): void => {
    const model = models.find((m) => m.model_name === model_name);
    if (model) {
      setSelectedModel(model);
      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, model_name);
      } catch (e) {
        console.warn("localStorage access failed:", e);
      }
    }
  };

  // 获取当前选中的模型名称，降级到默认值
  const currentModelName = selectedModel?.model_name || "gpt-4";

  // Memoize code examples
  const claudeCodeExample = useMemo(
    () => `{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<API_KEY>",
    "ANTHROPIC_BASE_URL": "${baseUrl}/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "${currentModelName}",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "${currentModelName}",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "${currentModelName}"
  }
}`,
    [baseUrl, currentModelName]
  );

  const openaiPythonExample = useMemo(
    () => `from openai import OpenAI

client = OpenAI(
    api_key="<API_KEY>",
    base_url="${baseUrl}/api/openai"
)

response = client.chat.completions.create(
    model="${currentModelName}",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)`,
    [baseUrl, currentModelName]
  );

  const openaiCurlExample = useMemo(
    () => `curl ${baseUrl}/api/openai/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer <API_KEY>" \\
  -d '{
    "model": "${currentModelName}",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'`,
    [baseUrl, currentModelName]
  );

  const anthropicPythonExample = useMemo(
    () => `from anthropic import Anthropic

client = Anthropic(
    api_key="<API_KEY>",
    base_url="${baseUrl}/api/anthropic"
)

message = client.messages.create(
    model="${currentModelName}",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(message.content[0].text)`,
    [baseUrl, currentModelName]
  );

  const anthropicCurlExample = useMemo(
    () => `curl ${baseUrl}/api/anthropic/v1/messages \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: <API_KEY>" \\
  -H "anthropic-version: 2023-06-01" \\
  -d '{
    "model": "${currentModelName}",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'`,
    [baseUrl, currentModelName]
  );

  const CodeBlock = ({
    code,
    tabId,
  }: {
    code: string;
    tabId: string;
  }): JSX.Element => (
    <div className="relative">
      <div className="relative bg-gray-100 dark:bg-gray-800 rounded-lg p-4 overflow-x-auto">
        <pre className="font-mono text-sm text-gray-800 dark:text-gray-200">
          <code>{code}</code>
        </pre>
        <button
          onClick={() => handleCopy(code, tabId)}
          className="absolute top-2 right-2 p-2 rounded-md bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          aria-label={copiedTab === tabId ? tAria('copied') : tAria('copyCode')}
          role="button"
          type="button"
        >
          {copiedTab === tabId ? (
            <Check className="w-4 h-4 text-green-600" />
          ) : (
            <Copy className="w-4 h-4 text-gray-600 dark:text-gray-300" />
          )}
        </button>
      </div>
    </div>
  );

  // 如果是受控模式，children 为可选
  const dialogTrigger = isControlled ? undefined : children ? <DialogTrigger asChild>{children}</DialogTrigger> : undefined;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {dialogTrigger}
      <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto top-[15%] translate-y-0">
        <DialogHeader>
          <div className="flex items-center justify-between pr-8">
            <div className="flex flex-col">
              <DialogTitle>{t('title')}</DialogTitle>
              <DialogDescription>
                {t('description')}
              </DialogDescription>
            </div>
            {/* 模型选择器 */}
            {!loadingModels && models.length > 0 && (
              <Select
                value={selectedModel?.model_name || ""}
                onValueChange={handleModelChange}
              >
                <SelectTrigger className="w-48 h-8 text-sm">
                  <SelectValue placeholder={t('selectModel')} />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.model_name} value={model.model_name}>
                      {model.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </DialogHeader>

        <Tabs defaultValue="claude-code" className="w-full">
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1">
            <TabsTrigger value="claude-code" className="text-xs truncate">
              {t('tabs.claudeCode')}
            </TabsTrigger>
            <TabsTrigger value="openai-python" className="text-xs truncate">
              <span className="hidden sm:inline">OpenAI: </span>Python
            </TabsTrigger>
            <TabsTrigger value="openai-curl" className="text-xs truncate">
              <span className="hidden sm:inline">OpenAI: </span>cURL
            </TabsTrigger>
            <TabsTrigger value="anthropic-python" className="text-xs truncate">
              <span className="hidden sm:inline">Anthropic: </span>Python
            </TabsTrigger>
            <TabsTrigger value="anthropic-curl" className="text-xs truncate">
              <span className="hidden sm:inline">Anthropic: </span>cURL
            </TabsTrigger>
          </TabsList>

          <TabsContent value="claude-code" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                {t('sections.claudeCode.title')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4"
                dangerouslySetInnerHTML={{
                  __html: t('sections.claudeCode.description', {
                    path: '<span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">~/.claude/settings.json</span>',
                    placeholder: '<span class="font-mono text-purple-600">&lt;API_KEY&gt;</span>'
                  }).replace(/<\/?span[^>]*>/g, (match) => match)
                }}
              />
              <CodeBlock code={claudeCodeExample} tabId="claude-code" />
            </div>
          </TabsContent>

          <TabsContent value="openai-python" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                {t('sections.openaiPython.title')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {t('sections.openaiPython.description', { cmd: '<span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">pip install openai</span>' })}
              </p>
              <CodeBlock code={openaiPythonExample} tabId="openai-python" />
            </div>
          </TabsContent>

          <TabsContent value="openai-curl" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                {t('sections.openaiCurl.title')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {t('sections.openaiCurl.description', { placeholder: '<API_KEY>' })}
              </p>
              <CodeBlock code={openaiCurlExample} tabId="openai-curl" />
            </div>
          </TabsContent>

          <TabsContent value="anthropic-python" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                {t('sections.anthropicPython.title')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {t('sections.anthropicPython.description', { cmd: '<span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">pip install anthropic</span>' })}
              </p>
              <CodeBlock code={anthropicPythonExample} tabId="anthropic-python" />
            </div>
          </TabsContent>

          <TabsContent value="anthropic-curl" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                {t('sections.anthropicCurl.title')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {t('sections.anthropicCurl.description', { placeholder: '<API_KEY>' })}
              </p>
              <CodeBlock code={anthropicCurlExample} tabId="anthropic-curl" />
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button
            onClick={handleCreateAPIKey}
            className="bg-purple-500 hover:bg-purple-600 text-white border border-purple-600"
          >
            {t('createApiKey')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
