import { readFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(scriptDirectory, "..");
const repoRoot = resolve(packageRoot, "../../..");
const packageManifest = JSON.parse(await readFile(join(packageRoot, "package.json"), "utf8"));
const devDependencies = packageManifest.devDependencies || {};
const cliVersion = String(devDependencies["@mermaid-js/mermaid-cli"] || "");
const browserVersion = String(devDependencies.mermaid || "");
const exactVersionPattern = /^\d+\.\d+\.\d+$/;

if (!exactVersionPattern.test(browserVersion) || browserVersion !== cliVersion) {
  throw new Error("Mermaid CLI and browser dependencies must use the same exact version");
}

const installedManifest = JSON.parse(
  await readFile(join(packageRoot, "node_modules/mermaid/package.json"), "utf8")
);
if (installedManifest.version !== browserVersion) {
  throw new Error(
    `Installed Mermaid ${installedManifest.version || "unknown"} does not match package version ${browserVersion}`
  );
}

const outputRoot = join(
  repoRoot,
  "docs-viewer/runtime/vendor/mermaid",
  browserVersion
);
const outputs = [
  {
    source: join(packageRoot, "node_modules/mermaid/dist/mermaid.min.js"),
    target: join(outputRoot, "mermaid.min.js")
  },
  {
    source: join(packageRoot, "node_modules/mermaid/LICENSE"),
    target: join(outputRoot, "LICENSE")
  }
];
const checkOnly = process.argv.includes("--check");

async function syncOutput({ source, target }) {
  const sourceBytes = await readFile(source);
  let targetBytes = null;
  try {
    targetBytes = await readFile(target);
  } catch (error) {
    if (error && error.code !== "ENOENT") throw error;
  }
  if (targetBytes && sourceBytes.equals(targetBytes)) return false;
  if (checkOnly) {
    throw new Error(`Mermaid browser asset is not synchronized: ${relative(repoRoot, target)}`);
  }
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, sourceBytes);
  return true;
}

const changed = [];
for (const output of outputs) {
  if (await syncOutput(output)) changed.push(relative(repoRoot, output.target));
}

if (checkOnly) {
  console.log(`Mermaid browser asset ${browserVersion} is synchronized`);
} else if (changed.length) {
  console.log(`Synchronized Mermaid browser asset ${browserVersion}: ${changed.join(", ")}`);
} else {
  console.log(`Mermaid browser asset ${browserVersion} is unchanged`);
}
