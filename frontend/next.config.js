/** @type {import('next').NextConfig} */
const nextConfig = {
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
