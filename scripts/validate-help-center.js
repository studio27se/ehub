#!/usr/bin/env node
/**
 * Help Center Validator
 * 
 * Validates the help center TOC and Markdown files for:
 * - Duplicate IDs
 * - Missing files
 * - Required metadata
 * - Structural integrity
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'js-yaml';
import matter from 'gray-matter';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

// Configuration
const TOC_FILE = path.join(rootDir, 'help-center-toc.yaml');

/**
 * Main validation function
 */
async function validateHelpCenter() {
  console.log('🔍 Starting Help Center validation...\n');

  let hasErrors = false;
  let hasWarnings = false;

  try {
    // Load TOC
    if (!fs.existsSync(TOC_FILE)) {
      console.error('❌ TOC file not found:', TOC_FILE);
      process.exit(1);
    }

    const tocContent = fs.readFileSync(TOC_FILE, 'utf8');
    const toc = yaml.load(tocContent);

    if (!toc || !toc.modules) {
      console.error('❌ Invalid TOC structure: missing modules');
      process.exit(1);
    }

    console.log(`✅ TOC loaded successfully\n`);

    // Track IDs to check for duplicates
    const moduleIds = new Set();
    const articleIds = new Set();

    // Validate modules
    for (const module of toc.modules) {
      console.log(`📂 Validating module: ${module.title || module.id || 'UNNAMED'}`);

      // Check required module fields
      if (!module.id) {
        console.error('  ❌ Module missing required field: id');
        hasErrors = true;
      } else if (moduleIds.has(module.id)) {
        console.error(`  ❌ Duplicate module ID: ${module.id}`);
        hasErrors = true;
      } else {
        moduleIds.add(module.id);
      }

      if (!module.title) {
        console.error(`  ❌ Module ${module.id} missing required field: title`);
        hasErrors = true;
      }

      if (!module.description) {
        console.warn(`  ⚠️  Module ${module.id} missing description`);
        hasWarnings = true;
      }

      if (!module.icon) {
        console.warn(`  ⚠️  Module ${module.id} missing icon`);
        hasWarnings = true;
      }

      // Validate articles
      if (!module.articles || !Array.isArray(module.articles)) {
        console.warn(`  ⚠️  Module ${module.id} has no articles`);
        hasWarnings = true;
        continue;
      }

      for (const article of module.articles) {
        // Check required article fields
        if (!article.id) {
          console.error(`    ❌ Article missing required field: id`);
          hasErrors = true;
        } else if (articleIds.has(article.id)) {
          console.error(`    ❌ Duplicate article ID: ${article.id}`);
          hasErrors = true;
        } else {
          articleIds.add(article.id);
        }

        if (!article.title) {
          console.error(`    ❌ Article ${article.id} missing required field: title`);
          hasErrors = true;
        }

        if (!article.file) {
          console.error(`    ❌ Article ${article.id} missing required field: file`);
          hasErrors = true;
          continue;
        }

        // Check if file exists
        const articlePath = path.join(rootDir, article.file);
        if (!fs.existsSync(articlePath)) {
          console.error(`    ❌ Article file not found: ${article.file}`);
          hasErrors = true;
          continue;
        }

        // Validate article file content
        try {
          const fileContent = fs.readFileSync(articlePath, 'utf8');
          const parsed = matter(fileContent);

          // Check frontmatter consistency
          if (parsed.data.id && parsed.data.id !== article.id) {
            console.warn(`    ⚠️  Frontmatter ID (${parsed.data.id}) differs from TOC ID (${article.id})`);
            hasWarnings = true;
          }

          if (parsed.data.moduleId && parsed.data.moduleId !== module.id) {
            console.warn(`    ⚠️  Frontmatter moduleId (${parsed.data.moduleId}) differs from parent module (${module.id})`);
            hasWarnings = true;
          }

          if (!parsed.content || parsed.content.trim().length === 0) {
            console.error(`    ❌ Article ${article.id} has no content`);
            hasErrors = true;
          }

          console.log(`    ✓ ${article.title}`);
        } catch (error) {
          console.error(`    ❌ Error parsing article ${article.file}: ${error.message}`);
          hasErrors = true;
        }
      }
    }

    // Summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 Validation Summary');
    console.log('='.repeat(50));
    console.log(`Modules: ${moduleIds.size}`);
    console.log(`Articles: ${articleIds.size}`);
    
    if (hasErrors) {
      console.log('\n❌ Validation failed with errors');
      process.exit(1);
    } else if (hasWarnings) {
      console.log('\n⚠️  Validation passed with warnings');
      process.exit(0);
    } else {
      console.log('\n✅ Validation passed successfully');
      process.exit(0);
    }

  } catch (error) {
    console.error('\n❌ Error during validation:', error.message);
    process.exit(1);
  }
}

// Run validator
validateHelpCenter();
