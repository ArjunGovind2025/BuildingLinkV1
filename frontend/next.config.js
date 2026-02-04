/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No output: 'export' — dynamic /jobs/[id] routes require server mode. Deploy to Vercel (or any Node host).
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
