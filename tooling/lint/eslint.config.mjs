import js from "@eslint/js";
import globals from "globals";

export default [
  {
    name: "Repository source exclusions",
    ignores: [
      "docs-viewer/build/mermaid/**",
      "docs-viewer/data/generated/**",
      "docs-viewer/runtime/vendor/**",
      "docs-viewer/scopes/**/published/**",
      "logs/**",
      "node_modules/**",
      "processing/**",
      "site/assets/data/**",
      "site/docs-viewer/runtime/vendor/**",
      "studio/data/canonical/**",
      "studio/data/generated/**",
      "studio/retired/**",
      "var/**"
    ]
  },
  js.configs.recommended,
  {
    name: "Repository direct-browser modules",
    files: [
      "admin-app/app/frontend/js/**/*.js",
      "docs-viewer/runtime/js/**/*.js",
      "shared/frontend/js/**/*.js",
      "site/assets/js/**/*.js",
      "site/docs-viewer/runtime/js/**/*.js",
      "studio/app/frontend/js/**/*.js"
    ],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser
    },
    linterOptions: {
      reportUnusedDisableDirectives: "error"
    },
    rules: {
      "no-empty": ["error", { allowEmptyCatch: true }],
      "no-unused-vars": ["error", {
        argsIgnorePattern: "^_",
        caughtErrors: "none"
      }]
    }
  }
];
