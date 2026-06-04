import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@dw-fx-ledger/shared"],
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://127.0.0.1:8000/:path*"
      }
    ];
  }
};

export default nextConfig;
