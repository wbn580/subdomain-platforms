import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";
import { readFileSync } from "node:fs";

const SITE = process.env.SITE || "zhongjie-paiming";
const cfg = JSON.parse(
  readFileSync(`./sites/${SITE}/site.config.json`, "utf8")
);

export default defineConfig({
  site: `https://${cfg.domain}`,
  outDir: `./dist/${SITE}`,
  integrations: [
    sitemap({
      filter: (page) => {
        if (page.includes("/404")) return false;
        return true;
      },
      changefreq: "weekly",
      priority: 0.7,
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
    define: {
      __SITE_CONFIG__: JSON.stringify(cfg),
    },
  },
  markdown: {
    syntaxHighlight: false,
  },
});
