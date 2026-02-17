#!/usr/bin/env node

/**
 * Browser Helper - Playwright-Wrapper für AcademicAgent
 * Usage: node scripts/browser_helper.js <action> <args...>
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;

// ============================================
// Main Function
// ============================================
async function main() {
  const action = process.argv[2];
  const args = process.argv.slice(3);

  if (!action) {
    console.error('Usage: node browser_helper.js <action> <args...>');
    console.error('Actions: navigate, search, extract, screenshot');
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: false }); // headless=false für Debugging
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });
  const page = await context.newPage();

  try {
    switch (action) {
      case 'navigate':
        await actionNavigate(page, args);
        break;
      case 'search':
        await actionSearch(page, args);
        break;
      case 'extract':
        await actionExtract(page, args);
        break;
      case 'screenshot':
        await actionScreenshot(page, args);
        break;
      default:
        console.error(`Unknown action: ${action}`);
        process.exit(1);
    }
  } finally {
    await browser.close();
  }
}

// ============================================
// Action: Navigate to URL
// ============================================
async function actionNavigate(page, args) {
  const [url, outputFile] = args;

  if (!url) {
    console.error('Usage: navigate <url> <outputFile>');
    process.exit(1);
  }

  console.log(`Navigating to: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const result = {
    url: page.url(),
    title: await page.title(),
    status: 'success'
  };

  if (outputFile) {
    await fs.writeFile(outputFile, JSON.stringify(result, null, 2));
    console.log(`Result saved to: ${outputFile}`);
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

// ============================================
// Action: Search in Database
// ============================================
async function actionSearch(page, args) {
  const [patternsFile, database, searchString, outputFile] = args;

  if (!patternsFile || !database || !searchString) {
    console.error('Usage: search <patternsFile> <database> <searchString> <outputFile>');
    process.exit(1);
  }

  // Load UI patterns
  const patterns = JSON.parse(await fs.readFile(patternsFile, 'utf-8'));
  const dbPatterns = patterns.databases[database];

  if (!dbPatterns) {
    console.error(`Database not found in patterns: ${database}`);
    process.exit(1);
  }

  console.log(`Searching in ${database}: "${searchString}"`);

  // Try to find search field
  const searchField = await findElement(page, dbPatterns.ui_patterns.search_field);
  if (!searchField) {
    console.error('Search field not found!');
    process.exit(1);
  }

  // Enter search string
  await searchField.fill(searchString);
  await page.waitForTimeout(1000);

  // Click search button
  const searchButton = await page.locator('button:has-text("Search"), input[type="submit"]').first();
  await searchButton.click();
  await page.waitForTimeout(5000);

  // Extract results
  const results = await extractResults(page, dbPatterns.ui_patterns.results);

  const output = {
    database,
    searchString,
    resultCount: results.length,
    results: results.slice(0, 20), // Top 20
    timestamp: new Date().toISOString()
  };

  if (outputFile) {
    await fs.writeFile(outputFile, JSON.stringify(output, null, 2));
    console.log(`Results saved to: ${outputFile}`);
  } else {
    console.log(JSON.stringify(output, null, 2));
  }
}

// ============================================
// Action: Extract Metadata from Results Page
// ============================================
async function actionExtract(page, args) {
  const [patternsFile, database, outputFile] = args;

  const patterns = JSON.parse(await fs.readFile(patternsFile, 'utf-8'));
  const dbPatterns = patterns.databases[database];

  const results = await extractResults(page, dbPatterns.ui_patterns.results);

  const output = {
    database,
    resultCount: results.length,
    results,
    timestamp: new Date().toISOString()
  };

  if (outputFile) {
    await fs.writeFile(outputFile, JSON.stringify(output, null, 2));
    console.log(`Extracted ${results.length} results to: ${outputFile}`);
  } else {
    console.log(JSON.stringify(output, null, 2));
  }
}

// ============================================
// Action: Take Screenshot
// ============================================
async function actionScreenshot(page, args) {
  const [outputFile] = args;

  if (!outputFile) {
    console.error('Usage: screenshot <outputFile>');
    process.exit(1);
  }

  await page.screenshot({ path: outputFile, fullPage: true });
  console.log(`Screenshot saved to: ${outputFile}`);
}

// ============================================
// Helper: Find Element using Patterns
// ============================================
async function findElement(page, elementPattern) {
  // Try selectors
  for (const selector of elementPattern.selectors || []) {
    try {
      const element = await page.locator(selector).first();
      if (await element.count() > 0) {
        console.log(`Found element with selector: ${selector}`);
        return element;
      }
    } catch (e) {
      // Try next selector
    }
  }

  // Try text markers
  for (const marker of elementPattern.text_markers || []) {
    try {
      const element = await page.locator(`text="${marker}"`).first();
      if (await element.count() > 0) {
        console.log(`Found element with text marker: ${marker}`);
        return element;
      }
    } catch (e) {
      // Try next marker
    }
  }

  return null;
}

// ============================================
// Helper: Extract Results from Page
// ============================================
async function extractResults(page, resultsPattern) {
  const results = [];

  // Find result items (try multiple selectors)
  const resultItems = await page.locator('.result-item, .search-result, article, .c-card').all();

  for (const item of resultItems.slice(0, 20)) {
    try {
      const title = await extractField(item, resultsPattern.title);
      const authors = await extractField(item, resultsPattern.authors);
      const abstract = await extractField(item, resultsPattern.abstract);
      const doi = await extractField(item, resultsPattern.doi);

      if (title) {
        results.push({
          title,
          authors: authors || 'N/A',
          abstract: abstract || 'N/A',
          doi: doi || 'N/A'
        });
      }
    } catch (e) {
      console.error(`Error extracting result: ${e.message}`);
    }
  }

  return results;
}

// ============================================
// Helper: Extract Field from Element
// ============================================
async function extractField(element, fieldPattern) {
  for (const selector of fieldPattern.selectors || []) {
    try {
      const field = await element.locator(selector).first();
      if (await field.count() > 0) {
        return await field.innerText();
      }
    } catch (e) {
      // Try next selector
    }
  }
  return null;
}

// ============================================
// Run
// ============================================
main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
