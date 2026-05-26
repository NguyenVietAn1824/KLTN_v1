/** @type {import('next').NextConfig} */
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:3334';

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/proxy/:path*',
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
