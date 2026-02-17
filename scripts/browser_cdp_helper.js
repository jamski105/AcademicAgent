#!/usr/bin/env node

/**
 * Browser CDP Helper - Connect to existing Chrome via DevTools Protocol
 *
 * Usage:
 *   1. Start Chrome with: bash scripts/start_chrome_debug.sh
 *   2. Run commands: node scripts/browser_cdp_helper.js <action> <args...>
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;

const CDP_URL = process.env.PLAYWRIGHT_CDP_URL || 'http://localhost:9222';

async function main() {
  const action = process.argv[2];
  const args = process.argv.slice(3);

  if (!action) {
    console.error('Usage: node browser_cdp_helper.js <action> <args...>');
    console.error('Actions: navigate, search, extract, screenshot, inject');
    console.error('');
    console.error('Example:');
    console.error('  node browser_cdp_helper.js navigate "https://ieeexplore.ieee.org"');
    process.exit(1);
  }

  try {
    // Connect to existing Chrome via CDP
    const browser = await chromium.connectOverCDP(CDP_URL);
    const contexts = browser.contexts();

    if (contexts.length === 0) {
      console.error('No browser contexts found. Open a tab in Chrome first.');
      process.exit(1);
    }

    const context = contexts[0];
    const pages = context.pages();

    let page;
    if (pages.length === 0) {
      // Create new page
      page = await context.newPage();
    } else {
      // Use existing page (current tab)
      page = pages[0];
    }

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
      case 'inject':
        await actionInject(page, args);
        break;
      case 'status':
        await actionStatus(page, args);
        break;
      default:
        console.error(`Unknown action: ${action}`);
        process.exit(1);
    }

    // Don't close browser (it's the user's Chrome)
    await browser.close();
  } catch (error) {
    console.error('Error:', error.message);
    console.error('');
    console.error('Troubleshooting:');
    console.error('  1. Is Chrome running with debug port?');
    console.error('     bash scripts/start_chrome_debug.sh');
    console.error('  2. Check if port 9222 is open:');
    console.error('     curl http://localhost:9222/json/version');
    process.exit(1);
  }
}

// ============================================
// Actions
// ============================================

async function actionNavigate(page, args) {
  const [url] = args;

  if (!url) {
    console.error('Usage: navigate <url>');
    process.exit(1);
  }

  console.log(`Navigating to: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });

  const result = {
    url: page.url(),
    title: await page.title(),
    status: 'success'
  };

  console.log(JSON.stringify(result, null, 2));
}

async function actionSearch(page, args) {
  const [patternsFile, database, searchString] = args;

  if (!patternsFile || !database || !searchString) {
    console.error('Usage: search <patternsFile> <database> <searchString>');
    process.exit(1);
  }

  // Load patterns
  const patterns = JSON.parse(await fs.readFile(patternsFile, 'utf-8'));
  const dbPatterns = patterns.databases[database];

  if (!dbPatterns) {
    console.error(`Database not found: ${database}`);
    process.exit(1);
  }

  console.log(`Searching in ${database}: "${searchString}"`);

  // Find search field
  const searchField = await findElement(page, dbPatterns.ui_patterns.search_field);
  if (!searchField) {
    console.error('Search field not found!');
    process.exit(1);
  }

  // Fill and submit
  await searchField.fill(searchString);
  await page.waitForTimeout(1000);

  const searchButton = await page.locator('button:has-text("Search"), input[type="submit"]').first();
  await searchButton.click();
  await page.waitForTimeout(5000);

  // Extract results
  const results = await extractResults(page, dbPatterns.ui_patterns.results);

  console.log(JSON.stringify({
    database,
    searchString,
    resultCount: results.length,
    results: results.slice(0, 20)
  }, null, 2));
}

async function actionExtract(page, args) {
  const [patternsFile, database] = args;

  const patterns = JSON.parse(await fs.readFile(patternsFile, 'utf-8'));
  const dbPatterns = patterns.databases[database];

  const results = await extractResults(page, dbPatterns.ui_patterns.results);

  console.log(JSON.stringify({
    database,
    url: page.url(),
    resultCount: results.length,
    results
  }, null, 2));
}

async function actionScreenshot(page, args) {
  const [outputFile] = args;

  if (!outputFile) {
    console.error('Usage: screenshot <outputFile>');
    process.exit(1);
  }

  await page.screenshot({ path: outputFile, fullPage: true });
  console.log(`Screenshot saved: ${outputFile}`);
}

async function actionInject(page, args) {
  const [scriptFile] = args;

  if (!scriptFile) {
    console.error('Usage: inject <scriptFile>');
    process.exit(1);
  }

  const script = await fs.readFile(scriptFile, 'utf-8');
  const result = await page.evaluate(script);

  console.log(JSON.stringify({ result }, null, 2));
}

async function actionStatus(page, args) {
  const result = {
    url: page.url(),
    title: await page.title(),
    status: 'connected'
  };

  console.log(JSON.stringify(result, null, 2));
}

// ============================================
// Helpers
// ============================================

async function findElement(page, elementPattern) {
  for (const selector of elementPattern.selectors || []) {
    try {
      const element = await page.locator(selector).first();
      if (await element.count() > 0) {
        return element;
      }
    } catch (e) {
      // Try next
    }
  }
  return null;
}

async function extractResults(page, resultsPattern) {
  const results = [];
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
      // Skip
    }
  }

  return results;
}

async function extractField(element, fieldPattern) {
  for (const selector of fieldPattern.selectors || []) {
    try {
      const field = await element.locator(selector).first();
      if (await field.count() > 0) {
        return await field.innerText();
      }
    } catch (e) {
      // Try next
    }
  }
  return null;
}

// ============================================
// Run
// ============================================

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
