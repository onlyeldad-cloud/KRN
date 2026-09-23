import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Windows checkouts keep CRLF; Prettier-as-ESLint must not block local start.
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    optimizePackageImports: [
      '@phosphor-icons/react',
      '@phosphor-icons/react/dist/ssr',
    ],
  },
};

export default nextConfig;
