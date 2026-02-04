/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true,
  },
  // Static export: set NEXT_PUBLIC_BACKEND_URL so API calls go to your backend (e.g. Railway).
};

module.exports = nextConfig;
