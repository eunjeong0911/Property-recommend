const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'img.peterpanz.com',
      },
      {
        protocol: 'https',
        hostname: 'cdn.peterpanz.com',
      },
    ],
  },
}

module.exports = nextConfig
