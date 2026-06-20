/// <reference types="vite/client" />

interface SiteConfig {
  slug?: string;
  domain: string;
  brand: string;
  tagline: string;
  lang: string;
  bizLine: string;
  theme: string;
  palette: {
    primary: string;
    accent: string;
  };
  font: string;
  author: string;
  chatbot: {
    backend: string;
    botName: string;
  };
  deployTarget: "workers";
  cfProject: string;
  noBrandLink: boolean;
}

declare const __SITE_CONFIG__: SiteConfig;
export const siteConfig: SiteConfig = __SITE_CONFIG__;
