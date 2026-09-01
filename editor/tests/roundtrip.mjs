#!/usr/bin/env node
/**
 * Round-trip .ppl sources through the editor's parse.js and codegen.js.
 * Prints JSON for pytest to verify with the real PPL compiler.
 *
 * Usage:
 *   node editor/tests/roundtrip.mjs
 *   node editor/tests/roundtrip.mjs path/to/file.ppl
 */

import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { generatePpl } from "../js/codegen.js";
import { parsePpl } from "../js/parse.js";

const here = dirname(fileURLToPath(import.meta.url));
const templatesDir = join(here, "..", "templates");
const fixturesDir = join(here, "fixtures");
const snapshotsDir = join(here, "snapshots");

function roundtripFile(path) {
  const original = readFileSync(path, "utf8");
  const doc = parsePpl(original);
  const source = generatePpl(doc);
  const docAgain = parsePpl(source);
  const sourceAgain = generatePpl(docAgain);
  const app = (doc.children || []).find((child) => child.kind === "app");
  return {
    file: path,
    ok: true,
    application: app?.name || null,
    source,
    stable: source === sourceAgain,
  };
}

function collectPaths(argv) {
  if (argv.length) return argv.map((item) => resolve(item));
  const paths = [];
  for (const dir of [templatesDir, fixturesDir, snapshotsDir]) {
    for (const name of readdirSync(dir)) {
      if (name.endsWith(".ppl")) paths.push(join(dir, name));
    }
  }
  return paths.sort();
}

const results = [];
for (const path of collectPaths(process.argv.slice(2))) {
  try {
    results.push(roundtripFile(path));
  } catch (err) {
    results.push({
      file: path,
      ok: false,
      error: `${err.name || "Error"}: ${err.message}`,
    });
  }
}

const failed = results.filter((item) => !item.ok);
process.stdout.write(JSON.stringify({ results, failed: failed.length }));
process.exit(failed.length ? 1 : 0);
