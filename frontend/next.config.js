/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: 'bottom-right',
  },
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
