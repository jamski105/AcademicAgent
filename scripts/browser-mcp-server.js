#!/usr/bin/env node

/**
 * Browser MCP Server - AcademicAgent
 * MCP (Model Context Protocol) Server für Browser-Automation
 *
 * Usage: node scripts/browser-mcp-server.js
 *
 * Der Server hält einen Browser offen und bietet Tools für:
 * - Navigation
 * - Suche
 * - Extraktion
 * - Screenshots
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { chromium } = require('playwright');
const fs = require('fs').promises;

// ============================================
// Global State
// ============================================
let browser = null;
let page = null;
let context = null;

// ============================================
// MCP Server Setup
// ============================================
const server = new Server(
  {
    name: 'browser-automation-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// ============================================
// Tool: Initialize Browser
// ============================================
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'browser_init':
        return await toolBrowserInit(args);
      case 'browser_navigate':
        return await toolBrowserNavigate(args);
      case 'browser_search':
        return await toolBrowserSearch(args);
      case 'browser_extract':
        return await toolBrowserExtract(args);
      case 'browser_screenshot':
        return await toolBrowserScreenshot(args);
      case 'browser_close':
        return await toolBrowserClose(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// ============================================
// List available tools
// ============================================
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'browser_init',
        description: 'Initialize browser (must be called first)',
        inputSchema: {
          type: 'object',
          properties: {
            headless: {
              type: 'boolean',
              description: 'Run browser in headless mode (default: false)',
            },
          },
        },
      },
      {
        name: 'browser_navigate',
        description: 'Navigate to URL',
        inputSchema: {
          type: 'object',
          properties: {
            url: {
              type: 'string',
              description: 'URL to navigate to',
            },
          },
          required: ['url'],
        },
      },
      {
        name: 'browser_search',
        description: 'Search in database using UI patterns',
        inputSchema: {
          type: 'object',
          properties: {
            database: {
              type: 'string',
              description: 'Database name (e.g., "IEEE Xplore")',
            },
            query: {
              type: 'string',
              description: 'Search query',
            },
            patterns_file: {
              type: 'string',
              description: 'Path to database_patterns.json',
            },
          },
          required: ['database', 'query', 'patterns_file'],
        },
      },
      {
        name: 'browser_extract',
        description: 'Extract metadata from current page',
        inputSchema: {
          type: 'object',
          properties: {
            database: {
              type: 'string',
              description: 'Database name for UI patterns',
            },
            patterns_file: {
              type: 'string',
              description: 'Path to database_patterns.json',
            },
          },
          required: ['database', 'patterns_file'],
        },
      },
      {
        name: 'browser_screenshot',
        description: 'Take screenshot of current page',
        inputSchema: {
          type: 'object',
          properties: {
            output_file: {
              type: 'string',
              description: 'Path to save screenshot',
            },
          },
          required: ['output_file'],
        },
      },
      {
        name: 'browser_close',
        description: 'Close browser',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// ============================================
// Tool Implementations
// ============================================

async function toolBrowserInit(args) {
  const headless = args.headless || false;

  if (browser) {
    return {
      content: [
        {
          type: 'text',
          text: 'Browser already initialized',
        },
      ],
    };
  }

  browser = await chromium.launch({ headless });
  context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  });
  page = await context.newPage();

  return {
    content: [
      {
        type: 'text',
        text: `Browser initialized (headless: ${headless})`,
      },
    ],
  };
}

async function toolBrowserNavigate(args) {
  if (!page) {
    throw new Error('Browser not initialized. Call browser_init first.');
  }

  const { url } = args;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          url: page.url(),
          title: await page.title(),
          status: 'success',
        }, null, 2),
      },
    ],
  };
}

async function toolBrowserSearch(args) {
  if (!page) {
    throw new Error('Browser not initialized. Call browser_init first.');
  }

  const { database, query, patterns_file } = args;

  // Load patterns
  const patterns = JSON.parse(await fs.readFile(patterns_file, 'utf-8'));
  const dbPatterns = patterns.databases[database];

  if (!dbPatterns) {
    throw new Error(`Database not found in patterns: ${database}`);
  }

  // Find search field
  const searchField = await findElement(page, dbPatterns.ui_patterns.search_field);
  if (!searchField) {
    throw new Error('Search field not found');
  }

  // Enter query
  await searchField.fill(query);
  await page.waitForTimeout(1000);

  // Click search button
  const searchButton = await page.locator('button:has-text("Search"), input[type="submit"]').first();
  await searchButton.click();
  await page.waitForTimeout(5000);

  // Extract results
  const results = await extractResults(page, dbPatterns.ui_patterns.results);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          database,
          query,
          resultCount: results.length,
          results: results.slice(0, 20),
        }, null, 2),
      },
    ],
  };
}

async function toolBrowserExtract(args) {
  if (!page) {
    throw new Error('Browser not initialized. Call browser_init first.');
  }

  const { database, patterns_file } = args;

  const patterns = JSON.parse(await fs.readFile(patterns_file, 'utf-8'));
  const dbPatterns = patterns.databases[database];

  const results = await extractResults(page, dbPatterns.ui_patterns.results);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          database,
          resultCount: results.length,
          results,
        }, null, 2),
      },
    ],
  };
}

async function toolBrowserScreenshot(args) {
  if (!page) {
    throw new Error('Browser not initialized. Call browser_init first.');
  }

  const { output_file } = args;
  await page.screenshot({ path: output_file, fullPage: true });

  return {
    content: [
      {
        type: 'text',
        text: `Screenshot saved to: ${output_file}`,
      },
    ],
  };
}

async function toolBrowserClose(args) {
  if (browser) {
    await browser.close();
    browser = null;
    page = null;
    context = null;
  }

  return {
    content: [
      {
        type: 'text',
        text: 'Browser closed',
      },
    ],
  };
}

// ============================================
// Helper Functions
// ============================================

async function findElement(page, elementPattern) {
  for (const selector of elementPattern.selectors || []) {
    try {
      const element = await page.locator(selector).first();
      if ((await element.count()) > 0) {
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
  const resultItems = await page.locator('.result-item, .search-result, article').all();

  for (const item of resultItems.slice(0, 20)) {
    try {
      const title = await extractField(item, resultsPattern.title);
      const authors = await extractField(item, resultsPattern.authors);
      const abstract = await extractField(item, resultsPattern.abstract);
      const doi = await extractField(item, resultsPattern.doi);

      if (title) {
        results.push({ title, authors: authors || 'N/A', abstract: abstract || 'N/A', doi: doi || 'N/A' });
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
      if ((await field.count()) > 0) {
        return await field.innerText();
      }
    } catch (e) {
      // Try next
    }
  }
  return null;
}

// ============================================
// Start Server
// ============================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Browser MCP Server started');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
