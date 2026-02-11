# 语言设置移动到头像下拉菜单实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将「语言设置」从独立位置移动到头像下拉菜单中，使用子菜单形式展示语言选择选项

**Architecture:** 在头像下拉菜单中添加语言子菜单，使用 `DropdownMenuSub` 和 `DropdownMenuRadioItem` 实现语言选择，复用现有的 `useLocaleStore` 状态管理

**Tech Stack:** Next.js, TypeScript, shadcn/ui (dropdown-menu), Zustand (useLocaleStore), next-intl

---

## 变更说明

### 涉及文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `frontend/src/components/header.tsx` | 修改 | 添加语言子菜单到头像下拉菜单 |
| `frontend/src/messages/zh-CN.json` | 修改 | 添加相关翻译 key |
| `frontend/src/messages/en.json` | 修改 | 添加相关翻译 key |

### 注意事项

1. `LanguageSwitcher.tsx` 组件可以保留或删除，因为语言切换功能将集成到头像下拉菜单中
2. 使用 `DropdownMenuRadioGroup` 和 `DropdownMenuRadioItem` 实现单选（语言是互斥的，不能同时选择多个）
3. 需要添加 Globe 图标（从 lucide-react 导入）

---

## Task 1: 添加翻译 key 到 zh-CN.json

**Files:**
- Modify: `frontend/src/messages/zh-CN.json`

**Step 1: 在 `topbar` 部分添加翻译 key**

```json
{
  "topbar": {
    "settings": "设置",
    "logout": "登出",
    "apiKeys": "API Keys",
    "language": "语言",
    "languageSettings": "语言设置"
  },
  ...
}
```

**Step 2: 保存文件**

手动编辑文件，在 `topbar` 对象中添加 `"language": "语言"` 和 `"languageSettings": "语言设置"`。

---

## Task 2: 添加翻译 key 到 en.json

**Files:**
- Modify: `frontend/src/messages/en.json`

**Step 1: 在 `topbar` 部分添加翻译 key**

```json
{
  "topbar": {
    "settings": "Settings",
    "logout": "Logout",
    "apiKeys": "API Keys",
    "language": "Language",
    "languageSettings": "Language Settings"
  },
  ...
}
```

**Step 2: 保存文件**

手动编辑文件，在 `topbar` 对象中添加 `"language": "Language"` 和 `"languageSettings": "Language Settings"`。

---

## Task 3: 修改 header.tsx - 添加语言子菜单

**Files:**
- Modify: `frontend/src/components/header.tsx`

**Step 1: 更新导入语句**

在顶部添加新的导入：

```typescript
import { Settings, LogOut, Zap, Globe } from "lucide-react";
import { localeNames, locales, type Locale } from "@/i18n";
import { useLocaleStore } from "@/lib/store";
```

修改原有的导入，添加 `Globe` 图标，以及从 `@/i18n` 导入语言配置，从 `@/lib/store` 导入 `useLocaleStore`。

原有的导入在第 6 行和第 8 行，需要合并更新。

**Step 2: 在组件中获取 locale 状态**

在 `Header` 绽数中添加状态获取：

```typescript
export function Header() {
  const t = useTranslations('topbar');
  const { user, logout, updateUser, isAuthenticated } = useAuthStore();
  const { locale, setLocale } = useLocaleStore();  // 新增
  const router = useRouter();
  ...
```

在 `useAuthStore()` 后面添加 `const { locale, setLocale } = useLocaleStore();`。

**Step 3: 在 DropdownMenuContent 中添加语言子菜单**

在 `DropdownMenuContent` 中，在 "设置" 菜单项之后添加语言子菜单：

```tsx
<DropdownMenuContent align="end" className="w-48">
  {/* 设置菜单项 */}
  <DropdownMenuItem
    className="cursor-pointer"
    onClick={() => router.push("/settings")}
  >
    <Settings className="mr-2 h-4 w-4" />
    {t('settings')}
  </DropdownMenuItem>

  {/* 语言子菜单 - 新增 */}
  <DropdownMenuSub>
    <DropdownMenuSubTrigger>
      <Globe className="mr-2 h-4 w-4" />
      {t('language')}
    </DropdownMenuSubTrigger>
    <DropdownMenuSubContent>
      <DropdownMenuRadioGroup value={locale} onValueChange={(value) => setLocale(value as Locale)}>
        {locales.map((loc) => (
          <DropdownMenuRadioItem key={loc} value={loc}>
            {localeNames[loc]}
          </DropdownMenuRadioItem>
        ))}
      </DropdownMenuRadioGroup>
    </DropdownMenuSubContent>
  </DropdownMenuSub>

  {/* 分隔线 */}
  <DropdownMenuSeparator />

  {/* 登出菜单项 */}
  <DropdownMenuItem
    className="cursor-pointer text-red-600 focus:text-red-600"
    onClick={handleLogout}
  >
    <LogOut className="mr-2 h-4 w-4" />
    {t('logout')}
  </DropdownMenuItem>
</DropdownMenuContent>
```

**Step 4: 更新 DropdownMenu 导入**

确保导入了子菜单相关的组件：

```typescript
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
```

**完整修改后的 header.tsx 内容：**

```typescript
"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Settings, LogOut, Zap, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore, useLocaleStore } from "@/lib/store";
import { authAPI } from "@/lib/services";
import { useIntervalOnVisible } from "@/hooks/useIntervalOnVisible";
import { UserAvatar } from "@/components/UserAvatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { useTranslations } from "next-intl";
import { localeNames, locales, type Locale } from "@/i18n";

export function Header() {
  const t = useTranslations('topbar');
  const { user, logout, updateUser, isAuthenticated } = useAuthStore();
  const { locale, setLocale } = useLocaleStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/shared');
  };

  // Auto-refresh token balance every 20 seconds when page is visible
  const refreshTokenBalance = async () => {
    const currentUser = useAuthStore.getState().user;
    if (!currentUser) return;
    try {
      const response = await authAPI.getProfile();
      updateUser(response.data);
    } catch (error) {
      console.error('[Header] Failed to refresh token balance:', error);
    }
  };

  useIntervalOnVisible(refreshTokenBalance, isAuthenticated ? 20000 : null);

  return (
    <header className="bg-white border-b border-purple-100 px-8 py-4">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity" aria-label="返回首页">
          <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xs">
            SM
          </div>
          <span className="font-semibold text-gray-900 text-sm">SharinMod</span>
        </Link>

        {/* Token余额显示 + Account Avatar */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="bg-brand-100 gap-1.5 h-8 px-3 rounded-full">
            <Zap className="h-3.5 w-3.5 text-brand-500" />
            <span className={cn(
              "text-sm font-medium",
              (user?.token_balance ?? 0) > 0 ? "text-brand-500" : "text-red-600"
            )}>
              {user?.token_balance ?? 0}
            </span>
          </Button>

          {/* Account Avatar with Dropdown Menu */}
          <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 rounded-full transition-opacity hover:opacity-90"
              aria-label="用户菜单"
            >
              <UserAvatar
                email={user?.email}
                name={user?.name}
                avatar_url={user?.avatar_url}
                className="h-8 w-8"
              />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => router.push("/settings")}
            >
              <Settings className="mr-2 h-4 w-4" />
              {t('settings')}
            </DropdownMenuItem>

            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Globe className="mr-2 h-4 w-4" />
                {t('language')}
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuRadioGroup value={locale} onValueChange={(value) => setLocale(value as Locale)}>
                  {locales.map((loc) => (
                    <DropdownMenuRadioItem key={loc} value={loc}>
                      {localeNames[loc]}
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuSubContent>
            </DropdownMenuSub>

            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer text-red-600 focus:text-red-600"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              {t('logout')}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
```

---

## Task 4: 验证功能

**Step 1: 启动开发服务器**

```bash
cd frontend && npm run dev
```

**Step 2: 测试功能**

1. 打开浏览器访问 `http://localhost:3000`
2. 点击右上角头像打开下拉菜单
3. 应该看到「语言」选项（带 Globe 图标和右箭头）
4. 点击「语言」展开子菜单
5. 应该看到「中文」和「English」两个选项
6. 点击任意语言选项，当前选中的语言应该显示圆点标记
7. 切换语言后，页面其他地方的语言应该相应变化

---

## Task 5: 提交代码

**Step 1: 添加文件到 git**

```bash
git add frontend/src/components/header.tsx frontend/src/messages/zh-CN.json frontend/src/messages/en.json
```

**Step 2: 提交**

```bash
git commit -m "feat: 将语言设置移动到头像下拉菜单中

- 在头像下拉菜单中添加语言子菜单
- 使用 DropdownMenuSub 和 DropdownMenuRadioItem 实现语言选择
- 添加 Globe 图标和相关翻译 key

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 测试检查清单

- [ ] 头像下拉菜单中显示「语言」选项
- [ ] 「语言」选项有 Globe 图标
- [ ] 点击「语言」展开子菜单
- [ ] 子菜单显示「中文」和「English」选项
- [ ] 当前选中的语言有圆点标记
- [ ] 点击语言选项能成功切换语言
- [ ] 切换语言后页面其他地方语言同步变化
- [ ] 没有 TypeScript 编译错误
- [ ] 没有控制台错误
