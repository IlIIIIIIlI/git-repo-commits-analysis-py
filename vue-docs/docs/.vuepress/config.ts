// docs/.vuepress/config.ts
import { defineUserConfig } from "vuepress";
import { defaultTheme } from "@vuepress/theme-default";
import { viteBundler } from "@vuepress/bundler-vite";
import { registerComponentsPlugin } from "@vuepress/plugin-register-components";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineUserConfig({
  lang: "en-US",
  title: "GitHub Analysis Reports",
  description: "Repository Analysis and Reports",

  theme: defaultTheme({
    logo: "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
    navbar: [
      { text: "Home", link: "/" },
      { text: "Structure", link: "/structure/" },
      { text: "Reports", link: "/reports/" },
    ],
  }),

  bundler: viteBundler({
    viteOptions: {
      resolve: {
        alias: {
          "@": path.resolve(__dirname),
        },
      },
      server: {
        proxy: {
          "/api": {
            target: "http://localhost:8000",
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ""),
          },
        },
      },
    },
  }),

  plugins: [
    registerComponentsPlugin({
      componentsDir: path.resolve(__dirname, "./components"),
    }),
  ],
});
