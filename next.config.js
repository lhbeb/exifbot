/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Only proxy in local development (not on Vercel)
    // Vercel automatically handles /api routes to Python functions
    if (process.env.NODE_ENV === 'development' && !process.env.VERCEL) {
      const apiPort = process.env.API_PORT || '5001';
      return [
        {
          source: '/api/:path*',
          destination: `http://localhost:${apiPort}/api/:path*`,
        },
      ];
    }
    // Production/Vercel: No rewrites needed
    return [];
  },
};

module.exports = nextConfig;
