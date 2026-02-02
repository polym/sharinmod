/** @type {import('next').NextConfig} */
const nextConfig = {
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
