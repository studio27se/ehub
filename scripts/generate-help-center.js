#!/usr/bin/env node
/**
 * Help Center Generator
 * 
 * Generates a pure-data JSON file from Markdown documentation and TOC.
 * This JSON is consumed by the webapp help center runtime.
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
const OUTPUT_FILE = path.join(rootDir, 'help-center.json');

/**
 * Main generator function
 */
async function generateHelpCenter() {
  console.log('🚀 Starting Help Center generation...\n');

  try {
    // Load TOC
    console.log('📖 Loading TOC...');
    const tocContent = fs.readFileSync(TOC_FILE, 'utf8');
    const toc = yaml.load(tocContent);
    
    if (!toc || !toc.modules) {
      throw new Error('Invalid TOC structure: missing modules');
    }

    console.log(`✅ Loaded ${toc.modules.length} modules\n`);

    // Process modules and articles
    const modules = [];
    let totalArticles = 0;

    for (const module of toc.modules) {
      console.log(`📂 Processing module: ${module.title} (${module.id})`);
      
      const processedModule = {
        id: module.id,
        title: module.title,
        description: module.description || '',
        icon: module.icon || 'file',
        order: module.order || 0,
        articles: []
      };

      if (module.articles && Array.isArray(module.articles)) {
        for (const article of module.articles) {
          const articlePath = path.join(rootDir, article.file);
          
          if (!fs.existsSync(articlePath)) {
            console.warn(`⚠️  Article file not found: ${article.file}`);
            continue;
          }

          // Read and parse Markdown file
          const fileContent = fs.readFileSync(articlePath, 'utf8');
          const parsed = matter(fileContent);
          
          // Extract metadata from frontmatter or use TOC defaults
          const articleData = {
            id: parsed.data.id || article.id,
            title: parsed.data.title || article.title,
            moduleId: parsed.data.moduleId || module.id,
            order: parsed.data.order !== undefined ? parsed.data.order : article.order || 0,
            content: parsed.content.trim()
          };

          processedModule.articles.push(articleData);
          totalArticles++;
          console.log(`  ✓ ${articleData.title}`);
        }
      }

      modules.push(processedModule);
    }

    // Create output object
    const output = {
      version: toc.version || '1.0.0',
      generated: new Date().toISOString(),
      modules: modules
    };

    // Write JSON output
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2), 'utf8');

    console.log('\n✨ Generation complete!');
    console.log(`📄 Output: ${OUTPUT_FILE}`);
    console.log(`📊 Stats: ${modules.length} modules, ${totalArticles} articles`);
    console.log('');

    return output;
  } catch (error) {
    console.error('\n❌ Error generating help center:', error.message);
    process.exit(1);
  }
}

// Run generator
generateHelpCenter();
