import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  ...(process.env.FIELDWEAVER_STATIC_EXPORT === "true" ? { output: "export" as const } : {}),
};

export default nextConfig;
