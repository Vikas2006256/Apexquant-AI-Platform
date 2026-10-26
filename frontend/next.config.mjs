/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === "production" && process.env.GITHUB_PAGES === "true";
const repoName = "Apexquant-AI-Platform";

const nextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
  basePath: isProd ? `/${repoName}` : "",
  assetPrefix: isProd ? `/${repoName}/` : undefined,
  trailingSlash: true,
};

export default nextConfig;
