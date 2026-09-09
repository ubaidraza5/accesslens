#!/usr/bin/env node
/*
 * Pulls the exact analysis engine shipped inside web/index.html and runs it
 * against the same fixture files the Python test suite uses, then checks
 * the two engines agree on the numbers that matter: company score, company
 * level, total findings, and the severity breakdown. If the JavaScript
 * engine and the Python engine ever disagree, this script fails the build
 * before the mismatch reaches the live demo.
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

const ROOT = path.resolve(__dirname, "..");

function extractEngineScript() {
  const html = fs.readFileSync(path.join(ROOT, "web", "index.html"), "utf-8");
  const match = html.match(
    /<script id="accesslens-engine">([\s\S]*?)<\/script>/
  );
  if (!match) {
    throw new Error(
      "Could not find the accesslens-engine script block in web/index.html"
    );
  }
  const tmpFile = path.join(os.tmpdir(), `accesslens-engine-${Date.now()}.js`);
  fs.writeFileSync(tmpFile, match[1]);
  return tmpFile;
}

function loadFixture(name) {
  return fs.readFileSync(
    path.join(ROOT, "tests", "fixtures", name),
    "utf-8"
  );
}

const CASES = [
  {
    fixture: "sample_company_access.csv",
    label: "Alderbrook Logistics sample, issues expected",
    expect: {
      companyScore: 100,
      companyLevel: "Critical",
      totalFindings: 46,
      findingsBySeverity: { Critical: 5, High: 7, Medium: 3, Low: 31 },
    },
  },
  {
    fixture: "clean_company_access.csv",
    label: "Brightfield Analytics sample, clean",
    expect: {
      companyScore: 0,
      companyLevel: "Clean",
      totalFindings: 0,
      findingsBySeverity: {},
    },
  },
];

function sortedEntries(obj) {
  return Object.entries(obj).sort((a, b) => a[0].localeCompare(b[0]));
}

function main() {
  const enginePath = extractEngineScript();
  const engine = require(enginePath);
  const asOf = new Date(Date.UTC(2026, 8, 9));

  let failures = 0;

  for (const testCase of CASES) {
    const csv = loadFixture(testCase.fixture);
    const records = engine.parseAccessCSV(csv);
    const report = engine.runFullReview(records, asOf);

    const checks = [
      ["companyScore", report.companyScore, testCase.expect.companyScore],
      ["companyLevel", report.companyLevel, testCase.expect.companyLevel],
      ["totalFindings", report.totalFindings, testCase.expect.totalFindings],
      [
        "findingsBySeverity",
        JSON.stringify(sortedEntries(report.findingsBySeverity)),
        JSON.stringify(sortedEntries(testCase.expect.findingsBySeverity)),
      ],
    ];

    console.log(`\n${testCase.label} (${testCase.fixture})`);
    for (const [field, actual, expected] of checks) {
      const ok = String(actual) === String(expected);
      console.log(`  ${ok ? "PASS" : "FAIL"}  ${field}: ${actual}`);
      if (!ok) {
        console.log(`        expected: ${expected}`);
        failures++;
      }
    }
  }

  fs.unlinkSync(enginePath);

  if (failures > 0) {
    console.error(
      `\n${failures} check(s) failed. The web demo does not match the Python engine.`
    );
    process.exit(1);
  }
  console.log("\nAll checks passed, the web demo matches the Python engine.");
}

main();
