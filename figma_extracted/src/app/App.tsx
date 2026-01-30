import { useState } from 'react';
import { Store, Users, Key, BarChart3, Grid, Sparkles, Radio, User } from 'lucide-react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/app/components/ui/select';
import { Badge } from '@/app/components/ui/badge';

export default function App() {
  const [activeTab, setActiveTab] = useState('marketplace');

  return (
    <div className="flex h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50">
      {/* Sidebar */}
      <div className="w-56 bg-white border-r border-purple-100 flex flex-col p-4">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-6 px-2">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            SM
          </div>
          <span className="font-semibold text-gray-900">SharinMod</span>
        </div>

        {/* Organization Selector */}
        <div className="mb-4">
          <div className="text-xs text-gray-500 mb-2 px-2">Organization</div>
          <button className="w-full px-3 py-2 bg-purple-50 hover:bg-purple-100 rounded-lg text-left text-sm flex items-center justify-between transition-colors">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-purple-600" />
              <span>Personal</span>
            </div>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Launch Button */}
        <Button className="w-full mb-4 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white shadow-lg shadow-purple-200">
          <Sparkles className="w-4 h-4 mr-2" />
          Launch an App
        </Button>

        {/* Navigation */}
        <nav className="flex-1 space-y-1">
          <NavItem 
            icon={<Store className="w-4 h-4" />} 
            label="广场" 
            active={activeTab === 'marketplace'}
            onClick={() => setActiveTab('marketplace')}
          />
          <NavItem 
            icon={<Users className="w-4 h-4" />} 
            label="我的共享"
            active={activeTab === 'shared'}
            onClick={() => setActiveTab('shared')}
          />
          <NavItem 
            icon={<Key className="w-4 h-4" />} 
            label="API Keys"
            active={activeTab === 'apikeys'}
            onClick={() => setActiveTab('apikeys')}
          />
          <NavItem 
            icon={<BarChart3 className="w-4 h-4" />} 
            label="使用情况"
            active={activeTab === 'usage'}
            onClick={() => setActiveTab('usage')}
          />
          
          <div className="pt-4 mt-4 border-t border-gray-200">
            <NavItem 
              icon={<Grid className="w-4 h-4" />} 
              label="Activity"
              active={false}
              onClick={() => {}}
            />
            <NavItem 
              icon={<Radio className="w-4 h-4" />} 
              label="Grafana"
              active={false}
              onClick={() => {}}
            />
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-purple-100 px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Grid className="w-5 h-5 text-gray-400" />
              <nav className="flex items-center gap-6 text-sm">
                <a href="#" className="flex items-center gap-2 text-purple-600 font-medium">
                  <Grid className="w-4 h-4" />
                  Dashboard
                </a>
                <a href="#" className="flex items-center gap-2 text-gray-600 hover:text-purple-600">
                  <Sparkles className="w-4 h-4" />
                  What's New
                </a>
                <a href="#" className="flex items-center gap-2 text-gray-600 hover:text-purple-600">
                  <Store className="w-4 h-4" />
                  Resources
                </a>
                <a href="#" className="flex items-center gap-2 text-gray-600 hover:text-purple-600">
                  <User className="w-4 h-4" />
                  Account
                </a>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Area */}
        <div className="flex-1 overflow-auto">
          <div className="max-w-7xl mx-auto p-8">
            <div className="flex gap-8">
              {/* API Keys Section */}
              <div className="flex-1">
                <div className="mb-6">
                  <h1 className="text-2xl font-semibold text-gray-900 mb-2">广场</h1>
                  <p className="text-sm text-gray-500">发现社区共享的 API Keys</p>
                </div>

                <Card className="bg-white shadow-sm border-purple-100">
                  <div className="p-6">
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

                    {/* Empty State */}
                    <div className="py-16 text-center">
                      <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                        <Key className="w-8 h-8 text-purple-600" />
                      </div>
                      <p className="text-gray-500 text-sm">暂无可用的 API Keys</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Recent Activity Sidebar */}
              <div className="w-80">
                <Card className="bg-gradient-to-br from-purple-50 to-white shadow-sm border-purple-100">
                  <div className="p-6">
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
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

function NavItem({ icon, label, active, onClick }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-3 transition-all
        ${active 
          ? 'bg-gradient-to-r from-purple-100 to-purple-50 text-purple-700' 
          : 'text-gray-600 hover:bg-purple-50 hover:text-purple-600'
        }
      `}
    >
      {icon}
      {label}
    </button>
  );
}

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
