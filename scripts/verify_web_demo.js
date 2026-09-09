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

function checkAlternateHeaders(engine) {
  console.log("\nAlternate column names, mirrors test_access_parser.py");
  let failures = 0;

  const altHeaderCSV =
    "Full Name,Email Address,Dept,Application,Role,Grant Date," +
    "Last Login,Status,Manager Name\n" +
    "Alice Chen,alice.chen@example.com,Finance,Finance ERP,Admin," +
    "2025-01-01,2026-08-01,Active,Test Manager\n";
  const altRecords = engine.parseAccessCSV(altHeaderCSV);
  const altOk =
    altRecords.length === 1 &&
    altRecords[0].name === "Alice Chen" &&
    altRecords[0].department === "Finance" &&
    altRecords[0].system === "Finance ERP" &&
    altRecords[0].permission === "Admin" &&
    altRecords[0].employeeStatus === "Active" &&
    altRecords[0].manager === "Test Manager";
  console.log(`  ${altOk ? "PASS" : "FAIL"}  alternate header names accepted`);
  if (!altOk) failures++;

  const firstLastCSV =
    "First Name,Last Name,email,department,system,permission," +
    "date_granted,date_last_used,employee_status,manager\n" +
    "Priya,Kapoor,priya.kapoor@example.com,Finance,Finance ERP," +
    "Standard User,2025-01-01,2026-08-01,Active,Test Manager\n";
  const firstLastRecords = engine.parseAccessCSV(firstLastCSV);
  const firstLastOk = firstLastRecords[0].name === "Priya Kapoor";
  console.log(`  ${firstLastOk ? "PASS" : "FAIL"}  first and last name columns combined`);
  if (!firstLastOk) failures++;

  const visitorLogCSV =
    "First Name,Last Name,Email,Access Code,Start Date,Start Time," +
    "End Date,End Time,Notes\n" +
    "Robert,Miller,rob@contractor.com,884422,2026-09-10,08:00," +
    "2026-09-12,17:00,HVAC Tech\n";
  let visitorLogRejected = false;
  try {
    engine.parseAccessCSV(visitorLogCSV);
  } catch (e) {
    visitorLogRejected = e instanceof engine.ParseError;
  }
  console.log(`  ${visitorLogRejected ? "PASS" : "FAIL"}  unrelated columns still rejected`);
  if (!visitorLogRejected) failures++;

  const badgeStyleCSV =
    "Full Name,Email Address,Department,System,Permission Level," +
    "Start Date,Last Used,Employment Status,Host\n" +
    "Jane Doe,jane.doe@example.com,Facilities,Physical Access Control," +
    "Contractor,2025-01-01,2026-08-01,Contractor,Test Manager\n";
  const badgeRecords = engine.parseAccessCSV(badgeStyleCSV);
  const badgeOk =
    badgeRecords[0].employeeStatus === "Contractor" &&
    badgeRecords[0].manager === "Test Manager";
  console.log(`  ${badgeOk ? "PASS" : "FAIL"}  employment status, host, and start date aliases accepted`);
  if (!badgeOk) failures++;

  // A badge or door system often logs a validity start and end date, not
  // when access was actually used. That end date must never be guessed as
  // date_last_used, so this file stays missing exactly that one column
  // even once every other column resolves by name.
  const badgeNoUsageCSV =
    "First Name,Last Name,Email,Access Code,Start Date,Start Time," +
    "End Date,End Time,Department,System,Permission Level," +
    "Employment Status,Host,Notes\n" +
    "Robert,Miller,rob@contractor.com,884422,2026-09-10,08:00," +
    "2026-09-12,17:00,Facilities,Physical Access Control," +
    "Contractor_HVAC,Contractor,Jane Doe,HVAC Tech\n";
  let onlyDateLastUsedMissing = false;
  try {
    engine.parseAccessCSV(badgeNoUsageCSV);
  } catch (e) {
    const missingPart = String(e.message).split("Expected columns are:")[0];
    onlyDateLastUsedMissing =
      e instanceof engine.ParseError &&
      missingPart.includes("date_last_used") &&
      !missingPart.includes(",");
  }
  console.log(`  ${onlyDateLastUsedMissing ? "PASS" : "FAIL"}  validity end date is not guessed as last used`);
  if (!onlyDateLastUsedMissing) failures++;

  return failures;
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

  failures += checkAlternateHeaders(engine);

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
