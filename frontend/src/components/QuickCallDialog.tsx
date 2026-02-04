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
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import { modelAPI } from "@/lib/services";
import type { ModelInfo } from "@/types/model";

// Constants
const COPY_FEEDBACK_DURATION = 1500; // ms
const FALLBACK_TEXTAREA_POSITION = "-999999px";
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
          title: "加载模型失败",
          description: "无法获取模型列表，将使用默认模型",
          variant: "destructive",
        });
      } finally {
        setLoadingModels(false);
      }
    };

    if (open) {
      loadModels();
    }
  }, [open, initialModelName, toast]);

  const resetCopyState = (): void => {
    setTimeout(() => setCopiedTab(null), COPY_FEEDBACK_DURATION);
  };

  const handleCopy = (code: string, tabId: string): void => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText(code)
        .then(() => {
          setCopiedTab(tabId);
          resetCopyState();
        })
        .catch((err) => {
          console.error("Failed to copy:", err);
          toast({
            title: "复制失败",
            description: "您的浏览器不支持剪贴板功能，请手动复制代码",
            variant: "destructive",
          });
        });
    } else {
      toast({
        title: "不支持的浏览器",
        description: "您的浏览器不支持剪贴板 API，请手动复制代码",
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
        title: "跳转失败",
        description: "无法跳转到 API Keys 页面，请稍后重试",
        variant: "destructive",
      });
    }
  };

  const handleModelChange = (model_name: string): void => {
    const model = models.find((m) => m.model_name === model_name);
    if (model) {
      setSelectedModel(model);
      // 保存到 localStorage
      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, model_name);
      } catch (e) {
        console.warn("localStorage access failed:", e);
      }
    }
  };

  // 获取当前选中的模型名称，降级到默认值
  const currentModelName = selectedModel?.model_name || "gpt-4";

  // Memoize code examples to prevent recreation on every render
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

# 初始化客户端
client = OpenAI(
    api_key="<API_KEY>",
    base_url="${baseUrl}/api/openai"
)

# 调用聊天接口
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

# 初始化客户端
client = Anthropic(
    api_key="<API_KEY>",
    base_url="${baseUrl}/api/anthropic"
)

# 调用消息接口
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
    title,
  }: {
    code: string;
    tabId: string;
    title?: string;
  }): JSX.Element => (
    <div className="relative">
      {title && (
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {title}
        </div>
      )}
      <div className="relative bg-gray-100 dark:bg-gray-800 rounded-lg p-4 overflow-x-auto">
        <pre className="font-mono text-sm text-gray-800 dark:text-gray-200">
          <code>{code}</code>
        </pre>
        <button
          onClick={() => handleCopy(code, tabId)}
          className="absolute top-2 right-2 p-2 rounded-md bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          aria-label={copiedTab === tabId ? "已复制" : "复制代码"}
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
              <DialogTitle>快速接入 API</DialogTitle>
              <DialogDescription>
                选择您偏好的工具和语言，复制示例代码即可开始调用 AI 模型
              </DialogDescription>
            </div>
            {/* 模型选择器 - 放在标题行最右侧 */}
            {!loadingModels && models.length > 0 && (
              <Select
                value={selectedModel?.model_name || ""}
                onValueChange={handleModelChange}
              >
                <SelectTrigger className="w-48 h-8 text-sm">
                  <SelectValue placeholder="选择模型" />
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
              Claude Code
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
                配置 Claude Code
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                将以下配置添加到 Claude Code 的 settings.json 文件中，默认位置为 <span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">~/.claude/settings.json</span>。
                使用您创建的 API Key 替换 <span className="font-mono text-purple-600">&lt;API_KEY&gt;</span>。
              </p>
              <CodeBlock code={claudeCodeExample} tabId="claude-code" />
            </div>
          </TabsContent>

          <TabsContent value="openai-python" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                使用 OpenAI Python SDK
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                安装 SDK：<span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">pip install openai</span>
              </p>
              <CodeBlock code={openaiPythonExample} tabId="openai-python" />
            </div>
          </TabsContent>

          <TabsContent value="openai-curl" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                使用 cURL 调用 OpenAI 接口
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                在终端中直接运行此命令，将{" "}
                <span className="font-mono text-purple-600">&lt;API_KEY&gt;</span> 替换为您的密钥。
              </p>
              <CodeBlock code={openaiCurlExample} tabId="openai-curl" />
            </div>
          </TabsContent>

          <TabsContent value="anthropic-python" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                使用 Anthropic Python SDK
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                安装 SDK：<span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">pip install anthropic</span>
              </p>
              <CodeBlock code={anthropicPythonExample} tabId="anthropic-python" />
            </div>
          </TabsContent>

          <TabsContent value="anthropic-curl" className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
                使用 cURL 调用 Anthropic 接口
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                在终端中直接运行此命令，将{" "}
                <span className="font-mono text-purple-600">&lt;API_KEY&gt;</span> 替换为您的密钥。
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
            创建 API Key
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
