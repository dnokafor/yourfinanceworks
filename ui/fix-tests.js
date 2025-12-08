#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Script to automatically fix common test patterns
 */

// Patterns to fix
const patterns = [
  {
    name: 'Loading state timing',
    pattern: /it\(['"](.*?)['"], async \(\) => \{\s*render\(<.* \/>\);\s*(?:expect\(screen\.getByText\()/g,
    replacement: (match, testName) => {
      return `it('${testName}', async () => {
    render(<ApprovalReportsPage />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading|Loading/i)).not.toBeInTheDocument();
    });

    expect(screen.getByText(`;
    }
  },
  {
    name: 'Duplicate text elements - Approver',
    pattern: /expect\(screen\.getByText\(['"]Approver['"]\)\)\.toBeInTheDocument\(\);/g,
    replacement: `expect(screen.getByLabelText('Approver')).toBeInTheDocument();`
  },
  {
    name: 'Duplicate text elements - Category',
    pattern: /expect\(screen\.getByText\(['"]Category['"]\)\)\.toBeInTheDocument\(\);/g,
    replacement: `expect(screen.getByLabelText('Category')).toBeInTheDocument();`
  },
  {
    name: 'Missing import for waitFor',
    pattern: /import \{ screen, fireEvent \} from '@testing-library\/react';/g,
    replacement: `import { screen, fireEvent, waitFor } from '@testing-library/react';`
  }
];

function fixFile(filePath) {
  console.log(`Processing ${filePath}...`);

  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;

  for (const { name, pattern, replacement } of patterns) {
    if (pattern.test(content)) {
      console.log(`  Applying fix: ${name}`);
      content = content.replace(pattern, replacement);
      modified = true;
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  ✅ Fixed ${filePath}`);
  } else {
    console.log(`  ⚪ No changes needed for ${filePath}`);
  }
}

function findTestFiles(dir) {
  const files = [];

  function scan(directory) {
    const items = fs.readdirSync(directory);

    for (const item of items) {
      const fullPath = path.join(directory, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        scan(fullPath);
      } else if (stat.isFile() && item.endsWith('.test.tsx') && item !== 'ApprovalReportsPage.test.tsx') {
        files.push(fullPath);
      }
    }
  }

  scan(dir);
  return files;
}

// Main execution
const testDir = path.join(__dirname, 'src/components/__tests__');
console.log('🔧 Starting automated test fixes...');
console.log(`📁 Scanning directory: ${testDir}`);

const testFiles = findTestFiles(testDir);
console.log(`📋 Found ${testFiles.length} test files to process`);

testFiles.forEach(fixFile);

console.log('✅ Test fix script completed!');
console.log('\n💡 Next steps:');
console.log('1. Run tests to see improvements: npm run test');
console.log('2. Review any remaining failures manually');
console.log('3. Consider creating more specific mocks if needed');
