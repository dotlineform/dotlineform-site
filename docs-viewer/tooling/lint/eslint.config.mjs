import js from "@eslint/js";
import globals from "globals";

export default [
  {
    name: "Docs Viewer pilot exclusions",
    ignores: [
      "admin-app/**",
      "docs-viewer/build/mermaid/**",
      "docs-viewer/data/generated/**",
      "docs-viewer/runtime/vendor/**",
      "docs-viewer/scopes/**/published/**",
      "docs-viewer/tests/**",
      "processing/**",
      "site/assets/**",
      "site/docs-viewer/runtime/vendor/**",
      "studio/**"
    ]
  },
  js.configs.recommended,
  {
    name: "Docs Viewer direct-browser modules",
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser
    },
    linterOptions: {
      reportUnusedDisableDirectives: "error"
    }
  }
];
