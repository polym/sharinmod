const pptxgen = require("pptxgenjs");

// 颜色方案 - Ocean Gradient
const COLORS = {
  darkBlue: "065A82",    // 深蓝 - 主色
  teal: "1C7293",        // 青色 - 次要色
  midnight: "21295C",    // 午夜蓝 - 强调色
  white: "FFFFFF",       // 白色
  lightGray: "F2F2F2",   // 浅灰
  mediumGray: "64748B",  // 中灰
  accent: "0891B2",      // 青色强调
  coral: "F96167"        // 珊瑚红 - 高亮
};

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Sharinmod Team';
pres.title = 'Sharinmod 技术架构';

// ===== Slide 1: 封面页 =====
let slide1 = pres.addSlide();
slide1.background = { color: COLORS.midnight };

// 大标题
slide1.addText("Sharinmod", {
  x: 0.5, y: 1.5, w: 9, h: 1,
  fontSize: 72, fontFace: "Arial Black", bold: true,
  color: COLORS.white, align: "center"
});

slide1.addText("API Token 共享平台技术架构", {
  x: 0.5, y: 2.6, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial",
  color: COLORS.white, align: "center"
});

// 装饰性形状
slide1.addShape(pres.shapes.RECTANGLE, {
  x: 3, y: 3.8, w: 4, h: 0.08,
  fill: { color: COLORS.accent }
});

slide1.addText("FastAPI + Next.js + PostgreSQL + LiteLLM", {
  x: 0.5, y: 4.2, w: 9, h: 0.5,
  fontSize: 18, fontFace: "Arial",
  color: COLORS.lightGray, align: "center"
});

// 版本信息
slide1.addText("2026", {
  x: 0.5, y: 5, w: 9, h: 0.4,
  fontSize: 14, fontFace: "Arial",
  color: COLORS.mediumGray, align: "center"
});

// ===== Slide 2: 项目概述 =====
let slide2 = pres.addSlide();
slide2.background = { color: COLORS.white };

slide2.addText("项目概述", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// 左侧描述
slide2.addText([
  { text: "Sharinmod 是一个现代化的", options: { fontSize: 20, fontFace: "Arial", color: COLORS.darkBlue } },
  { text: "API Token 共享和消费平台", options: { fontSize: 20, fontFace: "Arial", bold: true, color: COLORS.midnight, breakLine: true } },
  { text: "", options: { breakLine: true } },
  { text: "• 支持共享经济模型", options: { fontSize: 16, fontFace: "Arial", color: COLORS.darkBlue, bullet: true, breakLine: true } },
  { text: "• 智能代理（Claw）管理", options: { fontSize: 16, fontFace: "Arial", color: COLORS.darkBlue, bullet: true, breakLine: true } },
  { text: "• 多提供商 AI 模型调度", options: { fontSize: 16, fontFace: "Arial", color: COLORS.darkBlue, bullet: true, breakLine: true } },
  { text: "• Kubernetes Pod 管理", options: { fontSize: 16, fontFace: "Arial", color: COLORS.darkBlue, bullet: true, breakLine: true } }
], { x: 0.5, y: 1.5, w: 5, h: 3.5 });

// 右侧核心特性卡片
const cardProps = {
  fill: { color: "F8FAFC" },
  line: { color: COLORS.accent, width: 0 }
};

// 卡片1
slide2.addShape(pres.shapes.RECTANGLE, { ...cardProps, x: 6, y: 1.5, w: 3.5, h: 0.8 });
slide2.addText("Token 管理", { x: 6.2, y: 1.6, w: 3, h: 0.3, fontSize: 16, bold: true, color: COLORS.midnight });
slide2.addText("AES-256 加密存储", { x: 6.2, y: 1.9, w: 3, h: 0.3, fontSize: 12, color: COLORS.mediumGray });

// 卡片2
slide2.addShape(pres.shapes.RECTANGLE, { ...cardProps, x: 6, y: 2.5, w: 3.5, h: 0.8 });
slide2.addText("智能调度", { x: 6.2, y: 2.6, w: 3, h: 0.3, fontSize: 16, bold: true, color: COLORS.midnight });
slide2.addText("LiteLLM 多提供商", { x: 6.2, y: 2.9, w: 3, h: 0.3, fontSize: 12, color: COLORS.mediumGray });

// 卡片3
slide2.addShape(pres.shapes.RECTANGLE, { ...cardProps, x: 6, y: 3.5, w: 3.5, h: 0.8 });
slide2.addText("OAuth 认证", { x: 6.2, y: 3.6, w: 3, h: 0.3, fontSize: 16, bold: true, color: COLORS.midnight });
slide2.addText("GitHub / GitLab", { x: 6.2, y: 3.9, w: 3, h: 0.3, fontSize: 12, color: COLORS.mediumGray });

// 底部技术栈标签
slide2.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 5, w: 9, h: 0.4,
  fill: { color: COLORS.darkBlue }
});
slide2.addText("容器化部署 • Docker Compose • 水平扩展", {
  x: 0.5, y: 5, w: 9, h: 0.4,
  fontSize: 14, color: COLORS.white, align: "center"
});

// ===== Slide 3: 技术栈 =====
let slide3 = pres.addSlide();
slide3.background = { color: COLORS.white };

slide3.addText("核心技术栈", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// 前端区域
slide3.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.3, w: 3, h: 1.8,
  fill: { color: COLORS.teal }
});
slide3.addText("前端", {
  x: 0.5, y: 1.4, w: 3, h: 0.4,
  fontSize: 20, bold: true, color: COLORS.white, align: "center"
});
slide3.addText([
  { text: "Next.js 14", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "TypeScript", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "Tailwind CSS", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "shadcn/ui", options: { fontSize: 14, color: COLORS.white, breakLine: true } }
], { x: 0.5, y: 2, w: 3, h: 1, align: "center" });

// 后端区域
slide3.addShape(pres.shapes.RECTANGLE, {
  x: 3.7, y: 1.3, w: 3, h: 1.8,
  fill: { color: COLORS.darkBlue }
});
slide3.addText("后端", {
  x: 3.7, y: 1.4, w: 3, h: 0.4,
  fontSize: 20, bold: true, color: COLORS.white, align: "center"
});
slide3.addText([
  { text: "FastAPI", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "Python 3.11", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "SQLModel", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "Alembic", options: { fontSize: 14, color: COLORS.white, breakLine: true } }
], { x: 3.7, y: 2, w: 3, h: 1, align: "center" });

// 基础设施区域
slide3.addShape(pres.shapes.RECTANGLE, {
  x: 6.9, y: 1.3, w: 2.6, h: 1.8,
  fill: { color: COLORS.midnight }
});
slide3.addText("基础设施", {
  x: 6.9, y: 1.4, w: 2.6, h: 0.4,
  fontSize: 20, bold: true, color: COLORS.white, align: "center"
});
slide3.addText([
  { text: "PostgreSQL 15", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "Redis 7", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "LiteLLM", options: { fontSize: 14, color: COLORS.white, breakLine: true } },
  { text: "Nginx", options: { fontSize: 14, color: COLORS.white, breakLine: true } }
], { x: 6.9, y: 2, w: 2.6, h: 1, align: "center" });

// AI 提供商
slide3.addText("支持的 AI 提供商", {
  x: 0.5, y: 3.5, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.midnight
});

const providers = [
  { name: "OpenAI", color: "10A37F" },
  { name: "Anthropic", color: "D97757" },
  { name: "智谱", color: "3B82F6" },
  { name: "Z.AI", color: "8B5CF6" },
  { name: "月之暗面", color: "EC4899" },
  { name: "MiniMax", color: "F59E0B" },
  { name: "OpenRouter", color: "6366F1" },
  { name: "火山引擎", color: "EF4444" }
];

let xPos = 0.5;
providers.forEach((p, i) => {
  slide3.addShape(pres.shapes.RECTANGLE, {
    x: xPos, y: 4.1, w: 1.1, h: 0.5,
    fill: { color: p.color }
  });
  slide3.addText(p.name, {
    x: xPos, y: 4.2, w: 1.1, h: 0.3,
    fontSize: 11, color: COLORS.white, align: "center"
  });
  xPos += 1.2;
});

// ===== Slide 4: 系统架构图 =====
let slide4 = pres.addSlide();
slide4.background = { color: COLORS.white };

slide4.addText("系统架构", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// 用户层
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 4, y: 1, w: 2, h: 0.5,
  fill: { color: COLORS.midnight }, rectRadius: 0.08
});
slide4.addText("用户浏览器", {
  x: 4, y: 1.1, w: 2, h: 0.3,
  fontSize: 14, color: COLORS.white, align: "center"
});

// 箭头
slide4.addShape(pres.shapes.LINE, {
  x: 5, y: 1.5, w: 0, h: 0.3,
  line: { color: COLORS.mediumGray, width: 2, endArrowType: "triangle" }
});

// Nginx 层
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 4, y: 1.8, w: 2, h: 0.5,
  fill: { color: COLORS.accent }, rectRadius: 0.08
});
slide4.addText("Nginx 反向代理", {
  x: 4, y: 1.9, w: 2, h: 0.3,
  fontSize: 14, color: COLORS.white, align: "center"
});

// 分支箭头
slide4.addShape(pres.shapes.LINE, {
  x: 4.5, y: 2.3, w: -0.8, h: 0.3,
  line: { color: COLORS.mediumGray, width: 2, endArrowType: "triangle" }
});
slide4.addShape(pres.shapes.LINE, {
  x: 5.5, y: 2.3, w: 0.8, h: 0.3,
  line: { color: COLORS.mediumGray, width: 2, endArrowType: "triangle" }
});

// Frontend
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 2, y: 2.6, w: 1.8, h: 0.6,
  fill: { color: COLORS.teal }, rectRadius: 0.08
});
slide4.addText("Frontend\nNext.js", {
  x: 2, y: 2.7, w: 1.8, h: 0.5,
  fontSize: 12, color: COLORS.white, align: "center"
});

// Backend
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 6.2, y: 2.6, w: 1.8, h: 0.6,
  fill: { color: COLORS.darkBlue }, rectRadius: 0.08
});
slide4.addText("Backend\nFastAPI", {
  x: 6.2, y: 2.7, w: 1.8, h: 0.5,
  fontSize: 12, color: COLORS.white, align: "center"
});

// Backend 连接线
slide4.addShape(pres.shapes.LINE, {
  x: 5, y: 3.2, w: 0, h: 0.3,
  line: { color: COLORS.mediumGray, width: 2, endArrowType: "triangle" }
});

// 服务层
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 3.5, y: 3.5, w: 3, h: 0.6,
  fill: { color: COLORS.midnight }, rectRadius: 0.08
});
slide4.addText("服务层 (路由/业务逻辑)", {
  x: 3.5, y: 3.6, w: 3, h: 0.4,
  fontSize: 12, color: COLORS.white, align: "center"
});

// 数据层
slide4.addShape(pres.shapes.LINE, {
  x: 5, y: 4.1, w: 0, h: 0.3,
  line: { color: COLORS.mediumGray, width: 2, endArrowType: "triangle" }
});

// 数据库和缓存
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 1.5, y: 4.4, w: 1.5, h: 0.6,
  fill: { color: "336791" }, rectRadius: 0.08
});
slide4.addText("PostgreSQL", {
  x: 1.5, y: 4.5, w: 1.5, h: 0.4,
  fontSize: 12, color: COLORS.white, align: "center"
});

slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 3.3, y: 4.4, w: 1.5, h: 0.6,
  fill: { color: "DC382D" }, rectRadius: 0.08
});
slide4.addText("Redis", {
  x: 3.3, y: 4.5, w: 1.5, h: 0.4,
  fontSize: 12, color: COLORS.white, align: "center"
});

slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 5.1, y: 4.4, w: 1.5, h: 0.6,
  fill: { color: COLORS.accent }, rectRadius: 0.08
});
slide4.addText("LiteLLM", {
  x: 5.1, y: 4.5, w: 1.5, h: 0.4,
  fontSize: 12, color: COLORS.white, align: "center"
});

// 消费者
slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 7, y: 4.4, w: 1.5, h: 0.6,
  fill: { color: COLORS.coral }, rectRadius: 0.08
});
slide4.addText("后台消费者", {
  x: 7, y: 4.5, w: 1.5, h: 0.4,
  fontSize: 12, color: COLORS.white, align: "center"
});

// 外部集成
slide4.addShape(pres.shapes.LINE, {
  x: 5.8, y: 4.7, w: 0, h: 0.5,
  line: { color: COLORS.mediumGray, width: 2, endArrowType: "triangle" }
});

slide4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 4.5, y: 5.2, w: 2.6, h: 0.4,
  fill: { color: COLORS.lightGray }, rectRadius: 0.08
});
slide4.addText("外部 AI 提供商 / OAuth / K8s", {
  x: 4.5, y: 5.25, w: 2.6, h: 0.3,
  fontSize: 10, color: COLORS.midnight, align: "center"
});

// ===== Slide 5: 前端架构 =====
let slide5 = pres.addSlide();
slide5.background = { color: COLORS.white };

slide5.addText("前端架构", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// 技术栈
slide5.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 5.5, h: 0.5,
  fill: { color: COLORS.teal }
});
slide5.addText("Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui", {
  x: 0.5, y: 1.3, w: 5.5, h: 0.3,
  fontSize: 14, color: COLORS.white, align: "center"
});

// 页面列表
slide5.addText("核心页面", {
  x: 0.5, y: 2, w: 4, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.midnight
});

slide5.addText([
  { text: "Dashboard", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "概览页面，显示统计数据", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "Shared Keys", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "共享池管理，创建/编辑/删除", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "Marketplace", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "模型市场，浏览可用模型", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "API Keys", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "密钥管理，添加/编辑个人 Token", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "Usage", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "使用情况，查看 Token 消费", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "Settings", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "用户设置", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "Claws", options: { fontSize: 14, bullet: true, breakLine: true } },
  { text: "龙虾（Claw）管理", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } }
], { x: 0.5, y: 2.5, w: 4, h: 3.5 });

// 右侧架构图
slide5.addShape(pres.shapes.RECTANGLE, {
  x: 5.5, y: 2, w: 4, h: 4,
  fill: { color: "F8FAFC" },
  line: { color: COLORS.accent, width: 2 }
});

slide5.addText("前端组件结构", {
  x: 5.5, y: 2.1, w: 4, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.midnight, align: "center"
});

slide5.addShape(pres.shapes.RECTANGLE, {
  x: 6, y: 2.6, w: 3, h: 0.4,
  fill: { color: COLORS.teal }
});
slide5.addText("src/app (页面)", {
  x: 6, y: 2.65, w: 3, h: 0.3,
  fontSize: 11, color: COLORS.white, align: "center"
});

slide5.addShape(pres.shapes.RECTANGLE, {
  x: 6, y: 3.2, w: 3, h: 0.4,
  fill: { color: COLORS.teal }
});
slide5.addText("src/components (组件)", {
  x: 6, y: 3.25, w: 3, h: 0.3,
  fontSize: 11, color: COLORS.white, align: "center"
});

slide5.addShape(pres.shapes.RECTANGLE, {
  x: 6, y: 3.8, w: 3, h: 0.4,
  fill: { color: COLORS.teal }
});
slide5.addText("src/lib (工具/API)", {
  x: 6, y: 3.85, w: 3, h: 0.3,
  fontSize: 11, color: COLORS.white, align: "center"
});

slide5.addShape(pres.shapes.RECTANGLE, {
  x: 6.5, y: 4.8, w: 2, h: 0.6,
  fill: { color: COLORS.accent }
});
slide5.addText("shadcn/ui\n组件库", {
  x: 6.5, y: 4.85, w: 2, h: 0.5,
  fontSize: 11, color: COLORS.white, align: "center"
});

// ===== Slide 6: 后端架构 =====
let slide6 = pres.addSlide();
slide6.background = { color: COLORS.white };

slide6.addText("后端架构", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// 技术栈
slide6.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 5.5, h: 0.5,
  fill: { color: COLORS.darkBlue }
});
slide6.addText("FastAPI + Python 3.11 + SQLModel + Alembic", {
  x: 0.5, y: 1.3, w: 5.5, h: 0.3,
  fontSize: 14, color: COLORS.white, align: "center"
});

// 路由列表
slide6.addText("核心路由", {
  x: 0.5, y: 2, w: 5, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.midnight
});

slide6.addText([
  { text: "auth / oauth", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "JWT 认证，GitHub/GitLab OAuth", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "user", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "用户管理", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "unified_api_key", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "统一 API Key 管理", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "shared_api_key", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "共享池 Key 管理", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "api_key_usage", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "Token 使用情况追踪", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "models", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "模型目录管理", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } },
  { text: "claw", options: { fontSize: 13, bullet: true, breakLine: true } },
  { text: "Claw (龙虾) 管理", options: { fontSize: 11, indentLevel: 1, breakLine: true, color: COLORS.mediumGray } }
], { x: 0.5, y: 2.5, w: 5, h: 3.5 });

// 右侧服务层
slide6.addShape(pres.shapes.RECTANGLE, {
  x: 6, y: 2, w: 3.5, h: 4,
  fill: { color: "F8FAFC" },
  line: { color: COLORS.accent, width: 2 }
});

slide6.addText("服务层", {
  x: 6, y: 2.1, w: 3.5, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.midnight, align: "center"
});

slide6.addText([
  { text: "认证服务", options: { fontSize: 11, breakLine: true, color: COLORS.darkBlue } },
  { text: "auth_service.py", options: { fontSize: 10, breakLine: true, color: COLORS.mediumGray } },
  { text: "", options: { breakLine: true } },
  { text: "OAuth 服务", options: { fontSize: 11, breakLine: true, color: COLORS.darkBlue } },
  { text: "oauth_service.py", options: { fontSize: 10, breakLine: true, color: COLORS.mediumGray } },
  { text: "", options: { breakLine: true } },
  { text: "Key 管理服务", options: { fontSize: 11, breakLine: true, color: COLORS.darkBlue } },
  { text: "unified_api_key_service.py", options: { fontSize: 10, breakLine: true, color: COLORS.mediumGray } },
  { text: "shared_api_key_service.py", options: { fontSize: 10, breakLine: true, color: COLORS.mediumGray } },
  { text: "", options: { breakLine: true } },
  { text: "Claw 服务", options: { fontSize: 11, breakLine: true, color: COLORS.darkBlue } },
  { text: "claw_service.py", options: { fontSize: 10, breakLine: true, color: COLORS.mediumGray } },
  { text: "k8s_service.py", options: { fontSize: 10, breakLine: true, color: COLORS.mediumGray } }
], { x: 6.2, y: 2.7, w: 3.1, h: 3 });

// ===== Slide 7: 数据模型 =====
let slide7 = pres.addSlide();
slide7.background = { color: COLORS.white };

slide7.addText("数据模型", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// User 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.5, y: 1.2, w: 2, h: 1.5,
  fill: { color: COLORS.darkBlue }, rectRadius: 0.08
});
slide7.addText("User", {
  x: 0.5, y: 1.3, w: 2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• email", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• name", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• oauth_id", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 0.7, y: 1.7, w: 1.6, h: 0.9 });

// UnifiedAPIKey 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 3, y: 1.2, w: 2.2, h: 1.5,
  fill: { color: COLORS.teal }, rectRadius: 0.08
});
slide7.addText("UnifiedAPIKey", {
  x: 3, y: 1.3, w: 2.2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• id / user_id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• provider", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• encrypted_token", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• is_active", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 3.2, y: 1.7, w: 1.8, h: 0.9 });

// SharedAPIKey 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 5.7, y: 1.2, w: 2, h: 1.5,
  fill: { color: COLORS.accent }, rectRadius: 0.08
});
slide7.addText("SharedAPIKey", {
  x: 5.7, y: 1.3, w: 2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• id / owner_id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• pool_tokens", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• max_users", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• unified_key_ids", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 5.9, y: 1.7, w: 1.6, h: 0.9 });

// Claw 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 8.1, y: 1.2, w: 1.4, h: 1.5,
  fill: { color: COLORS.coral }, rectRadius: 0.08
});
slide7.addText("Claw", {
  x: 8.1, y: 1.3, w: 1.4, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• user_id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• claw_type", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• status", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 8.2, y: 1.7, w: 1.2, h: 0.9 });

// APIKeyUsage 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 1.5, y: 3.2, w: 2.2, h: 1.5,
  fill: { color: COLORS.midnight }, rectRadius: 0.08
});
slide7.addText("APIKeyUsage", {
  x: 1.5, y: 3.3, w: 2.2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• id / unified_key_id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• spend", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• prompt_tokens", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• completion_tokens", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 1.7, y: 3.7, w: 1.8, h: 0.9 });

// UsageLog 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 4.2, y: 3.2, w: 2, h: 1.5,
  fill: { color: COLORS.darkBlue }, rectRadius: 0.08
});
slide7.addText("UsageLog", {
  x: 4.2, y: 3.3, w: 2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• id / unified_key_id", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• timestamp", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• model", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• request_response", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 4.4, y: 3.7, w: 1.6, h: 0.9 });

// ProviderConfig 模型
slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 6.7, y: 3.2, w: 2.8, h: 1.5,
  fill: { color: COLORS.teal }, rectRadius: 0.08
});
slide7.addText("ProviderConfig", {
  x: 6.7, y: 3.3, w: 2.8, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white, align: "center"
});
slide7.addText([
  { text: "• provider", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• models (JSON)", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• region / base_url", options: { fontSize: 11, color: COLORS.white, breakLine: true } },
  { text: "• supports_function_calling", options: { fontSize: 11, color: COLORS.white, breakLine: true } }
], { x: 6.9, y: 3.7, w: 2.4, h: 0.9 });

// 关系说明
slide7.addText("关系说明", {
  x: 0.5, y: 5, w: 9, h: 0.4,
  fontSize: 16, bold: true, color: COLORS.midnight
});

slide7.addText([
  { text: "User 1:N UnifiedAPIKey 1:N APIKeyUsage", options: { fontSize: 12, breakLine: true, color: COLORS.darkBlue } },
  { text: "User 1:N SharedAPIKey 1:N UsageLog", options: { fontSize: 12, breakLine: true, color: COLORS.darkBlue } },
  { text: "User 1:N Claw", options: { fontSize: 12, breakLine: true, color: COLORS.darkBlue } }
], { x: 0.5, y: 5.5, w: 9, h: 0.5 });

// ===== Slide 8: 部署架构 =====
let slide8 = pres.addSlide();
slide8.background = { color: COLORS.white };

slide8.addText("部署架构", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.midnight, align: "left"
});

// Docker Compose 服务
slide8.addText("Docker Compose 服务", {
  x: 0.5, y: 1.2, w: 4, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.midnight
});

const services = [
  { name: "frontend", desc: "Next.js 前端服务" },
  { name: "backend", desc: "FastAPI 后端服务" },
  { name: "db", desc: "PostgreSQL 数据库" },
  { name: "redis", desc: "Redis 缓存" },
  { name: "litellm", desc: "LiteLLM 调度服务" },
  { name: "nginx", desc: "反向代理" },
  { name: "litellm-callback-consumer", desc: "回调消费者" },
  { name: "claw-status-consumer", desc: "Claw 状态同步" }
];

let y = 1.8;
services.forEach(s => {
  slide8.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: y, w: 3.5, h: 0.4,
    fill: { color: COLORS.lightGray }
  });
  slide8.addText(s.name, {
    x: 0.7, y: y + 0.05, w: 1.5, h: 0.3,
    fontSize: 12, bold: true, color: COLORS.midnight
  });
  slide8.addText(s.desc, {
    x: 2.2, y: y + 0.05, w: 1.6, h: 0.3,
    fontSize: 11, color: COLORS.mediumGray
  });
  y += 0.5;
});

// 右侧配置管理
slide8.addShape(pres.shapes.RECTANGLE, {
  x: 5, y: 1.2, w: 4.5, h: 2.8,
  fill: { color: "F8FAFC" },
  line: { color: COLORS.accent, width: 2 }
});

slide8.addText("配置管理", {
  x: 5, y: 1.3, w: 4.5, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.midnight, align: "center"
});

slide8.addText([
  { text: "etc/config.yaml", options: { fontSize: 13, bold: true, breakLine: true, color: COLORS.darkBlue } },
  { text: "• app.* - 应用配置", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } },
  { text: "• claw_types.* - Claw 类型", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } },
  { text: "• workspace_* - 工作区存储", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } },
  { text: "• prunc_* - RuntimeClass", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } },
  { text: "", options: { breakLine: true } },
  { text: "环境变量 Fallback", options: { fontSize: 13, bold: true, breakLine: true, color: COLORS.darkBlue } },
  { text: "DATABASE_URI, LITELLM_*", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } },
  { text: "GITHUB_*, GITLAB_*", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } },
  { text: "SHARINMOD_ADMIN_*", options: { fontSize: 11, breakLine: true, indentLevel: 1, color: COLORS.mediumGray } }
], { x: 5.2, y: 1.8, w: 4.1, h: 2 });

// 数据库
slide8.addText("数据库", {
  x: 0.5, y: 4.5, w: 4, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.midnight
});

slide8.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.5, y: 4.95, w: 1.8, h: 0.5,
  fill: { color: "336791" }, rectRadius: 0.08
});
slide8.addText("sharinmod", {
  x: 0.5, y: 5.05, w: 1.8, h: 0.3,
  fontSize: 12, color: COLORS.white, align: "center"
});

slide8.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 2.5, y: 4.95, w: 1.8, h: 0.5,
  fill: { color: "336791" }, rectRadius: 0.08
});
slide8.addText("litellm", {
  x: 2.5, y: 5.05, w: 1.8, h: 0.3,
  fontSize: 12, color: COLORS.white, align: "center"
});

// 外部集成
slide8.addText("外部集成", {
  x: 5, y: 4.5, w: 4.5, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.midnight
});

slide8.addText([
  { text: "• GitHub / GitLab OAuth", options: { fontSize: 13, breakLine: true, color: COLORS.darkBlue } },
  { text: "• LiteLLM (多提供商调度)", options: { fontSize: 13, breakLine: true, color: COLORS.darkBlue } },
  { text: "• Kubernetes (Claw Pod 管理)", options: { fontSize: 13, breakLine: true, color: COLORS.darkBlue } },
  { text: "• 8+ AI 提供商集成", options: { fontSize: 13, breakLine: true, color: COLORS.darkBlue } }
], { x: 5, y: 4.95, w: 4.5, h: 0.8 });

// ===== Slide 9: 总结 =====
let slide9 = pres.addSlide();
slide9.background = { color: COLORS.midnight };

slide9.addText("总结", {
  x: 0.5, y: 0.8, w: 9, h: 0.6,
  fontSize: 44, fontFace: "Arial Black", bold: true,
  color: COLORS.white, align: "center"
});

// 核心特性
slide9.addText("核心特性", {
  x: 0.5, y: 1.6, w: 9, h: 0.4,
  fontSize: 20, bold: true, color: COLORS.lightGray, align: "center"
});

const features = [
  { icon: "🔐", title: "安全加密", desc: "AES-256 加密存储 Token" },
  { icon: "🔄", title: "智能调度", desc: "LiteLLM 多提供商自动切换" },
  { icon: "📊", title: "使用追踪", desc: "详细的 Token 消费统计" },
  { icon: "🐙", title: "Claw 管理", desc: "Kubernetes Pod 动态管理" }
];

let fx = 0.8;
features.forEach(f => {
  slide9.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: fx, y: 2.2, w: 2.1, h: 1.2,
    fill: { color: "FFFFFF", transparency: 10 }, rectRadius: 0.08
  });
  slide9.addText(f.icon, {
    x: fx, y: 2.3, w: 2.1, h: 0.3,
    fontSize: 28, align: "center"
  });
  slide9.addText(f.title, {
    x: fx, y: 2.6, w: 2.1, h: 0.3,
    fontSize: 14, bold: true, color: COLORS.white, align: "center"
  });
  slide9.addText(f.desc, {
    x: fx, y: 2.9, w: 2.1, h: 0.4,
    fontSize: 11, color: COLORS.lightGray, align: "center"
  });
  fx += 2.3;
});

// 技术亮点
slide9.addText("技术亮点", {
  x: 0.5, y: 3.8, w: 9, h: 0.4,
  fontSize: 20, bold: true, color: COLORS.lightGray, align: "center"
});

slide9.addText([
  { text: "容器化部署", options: { fontSize: 14, breakLine: true, color: COLORS.white } },
  { text: "Docker Compose 一键启动，支持水平扩展", options: { fontSize: 11, breakLine: true, color: COLORS.lightGray } },
  { text: "", options: { breakLine: true } },
  { text: "现代化技术栈", options: { fontSize: 14, breakLine: true, color: COLORS.white } },
  { text: "Next.js 14 + FastAPI + PostgreSQL + LiteLLM", options: { fontSize: 11, breakLine: true, color: COLORS.lightGray } },
  { text: "", options: { breakLine: true } },
  { text: "OAuth 认证", options: { fontSize: 14, breakLine: true, color: COLORS.white } },
  { text: "GitHub / GitLab 一键登录", options: { fontSize: 11, breakLine: true, color: COLORS.lightGray } },
  { text: "", options: { breakLine: true } },
  { text: "多提供商支持", options: { fontSize: 14, breakLine: true, color: COLORS.white } },
  { text: "OpenAI, Anthropic, 智谱, Z.AI, 月之暗面, MiniMax, OpenRouter, 火山引擎", options: { fontSize: 11, breakLine: true, color: COLORS.lightGray } }
], { x: 1.5, y: 4.3, w: 7, h: 1.2, align: "center" });

// 生成文件
pres.writeFile({ fileName: "sharinmod-architecture.pptx" });
console.log("PPT 已生成: sharinmod-architecture.pptx");
