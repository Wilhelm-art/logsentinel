/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    let apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://backend:8000";
    
    // Auto-fix missing protocols from Vercel dashbaord (e.g. 'api.railway.app' instead of 'https://...')
    if (!apiUrl.startsWith("http")) {
      apiUrl = `https://${apiUrl}`;
    }
    // Auto-fix trailing slashes
    apiUrl = apiUrl.replace(/\/+$/, "");

    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiUrl}/api/v1/:path*`,
      },
    ];
  },
  output: "standalone",
};
export default nextConfig;
