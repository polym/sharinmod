/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  // 关闭所有开发环境指示器（生产构建时）
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: 'bottom-right',
  },

  // 生产环境优化配置
  reactStrictMode: false,
  swcMinify: true,

  // 关闭 source maps（生产环境）
  productionBrowserSourceMaps: false,

  // 压缩优化
  compress: true,

  // 关闭 powered by header
  poweredByHeader: false,
  async redirects() {
    return [
      {
        source: '/login',
        destination: '/shared',
        permanent: false,
      },
    ]
  },
}

module.exports = nextConfig
