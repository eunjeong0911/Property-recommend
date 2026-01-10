const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'standalone',
  reactStrictMode: true,
  eslint: {
    // 빌드 시 ESLint 경고를 무시 (프로덕션 배포용)
    ignoreDuringBuilds: true,
  },
  typescript: {
    // TypeScript 에러도 무시 (필요시)
    ignoreBuildErrors: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'img.peterpanz.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'cdn.peterpanz.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'ic.zigbang.com',
        pathname: '/**',
      },
    ],
    // Zigbang hotlink protection 우회
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  async rewrites() {
    return [
      {
        source: '/rag/:path*',
        destination: process.env.NEXT_PUBLIC_RAG_URL
          ? `${process.env.NEXT_PUBLIC_RAG_URL}/:path*`
          : 'http://127.0.0.1:8001/:path*',
      },
      // Backend API Proxy - Exclude /api/auth/* (NextAuth routes)
      {
        source: '/api/((?!auth).*)',  // Negative lookahead: match /api/* except /api/auth/*
        destination: process.env.NEXT_PUBLIC_API_URL
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/$1`
          : 'http://127.0.0.1:8000/api/$1',
      },
    ];
  },
}

module.exports = nextConfig
