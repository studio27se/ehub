# eHUB Help Center Documentation System

This directory contains the source of truth for eHUB's help center documentation, which is consumed by the webapp, mobile app, and other clients.

## Overview

The help center system uses:
- **Markdown files** for article content (in `help-center/` directory)
- **YAML TOC** for structure and metadata (`help-center-toc.yaml`)
- **Node.js generator** to create JSON output (`scripts/generate-help-center.js`)
- **Validation** to ensure data integrity (`scripts/validate-help-center.js`)

## Directory Structure

```
ehub/
├── help-center/                    # Markdown content
│   ├── getting-started/           # Module: Getting Started
│   │   ├── introduction.md
│   │   ├── first-steps.md
│   │   └── navigation.md
│   ├── features/                  # Module: Features
│   │   ├── projects.md
│   │   └── documentation.md
│   ├── settings/                  # Module: Settings
│   ├── integrations/              # Module: Integrations
│   └── troubleshooting/           # Module: Troubleshooting
├── help-center-toc.yaml           # Table of contents and metadata
├── scripts/
│   ├── generate-help-center.js    # JSON generator
│   └── validate-help-center.js    # Validation script
├── package.json                   # Node.js dependencies
├── help-center.json               # Generated output (gitignored)
├── .github/workflows/             # GitHub Actions templates
└── docs/CDN-STRATEGY.md           # CDN deployment guide
```

## Quick Start

### Prerequisites

- Node.js 18 or later
- npm

### Installation

```bash
npm install
```

### Commands

```bash
# Validate the TOC and Markdown files
npm run validate

# Generate help-center.json
npm run build

# Validate and build in one step
npm run build:validate
```

## Writing Documentation

### Create a New Article

1. **Create the Markdown file** in the appropriate module directory:

```bash
touch help-center/features/new-feature.md
```

2. **Add frontmatter** to the Markdown file:

```markdown
---
id: features-new-feature
title: New Feature Name
moduleId: features
order: 3
---

# New Feature Name

Article content goes here...
```

3. **Update the TOC** (`help-center-toc.yaml`):

```yaml
- id: features
  title: Features
  # ... other fields ...
  articles:
    # ... existing articles ...
    - id: features-new-feature
      title: New Feature Name
      file: help-center/features/new-feature.md
      order: 3
```

4. **Validate and build**:

```bash
npm run build:validate
```

### Create a New Module

1. **Create the module directory**:

```bash
mkdir help-center/new-module
```

2. **Add module to TOC** (`help-center-toc.yaml`):

```yaml
modules:
  # ... existing modules ...
  - id: new-module
    title: New Module Title
    description: Description of what this module covers
    icon: icon-name  # e.g., rocket, star, settings, plug, wrench
    order: 6
    articles: []
```

3. **Add articles** to the module following the "Create a New Article" steps above.

## Article Frontmatter

Each Markdown file should have YAML frontmatter:

```yaml
---
id: unique-article-id              # Required: Unique across all articles
title: Article Title               # Required: Display title
moduleId: module-id                # Required: Must match parent module
order: 1                           # Required: Display order within module
draft: false                       # Optional: Hide from production
---
```

## TOC Structure

The `help-center-toc.yaml` file defines the complete structure:

```yaml
version: "1.0.0"
modules:
  - id: module-id                  # Required: Unique module ID
    title: Module Title             # Required: Display title
    description: Module description # Required: Short description
    icon: icon-name                 # Required: Icon identifier
    order: 1                        # Required: Module order
    articles:
      - id: article-id              # Required: Unique article ID
        title: Article Title         # Required: Display title
        file: path/to/file.md       # Required: Relative path from repo root
        order: 1                    # Required: Article order within module
```

## Validation Rules

The validator checks for:

✅ **Required Fields**
- Module: id, title, description, icon, order
- Article: id, title, file, order

✅ **Unique IDs**
- No duplicate module IDs
- No duplicate article IDs

✅ **File Existence**
- All referenced Markdown files must exist

✅ **Content**
- Articles must have content (not empty)

✅ **Consistency**
- Frontmatter matches TOC entries
- Module IDs in frontmatter match parent module

## Generated JSON Structure

The `help-center.json` output has this structure:

```json
{
  "version": "1.0.0",
  "generated": "2026-02-09T12:00:00.000Z",
  "modules": [
    {
      "id": "getting-started",
      "title": "Getting Started",
      "description": "Learn the basics",
      "icon": "rocket",
      "order": 1,
      "articles": [
        {
          "id": "getting-started-introduction",
          "title": "Introduction",
          "moduleId": "getting-started",
          "order": 1,
          "content": "Markdown content as plain text..."
        }
      ]
    }
  ]
}
```

**Important**: The JSON contains **pure data only** - no HTML. The webapp is responsible for rendering Markdown to HTML.

## Consuming the JSON

### In Webapp (`studio27se/ehub-webapp`)

The existing `manual.js` should be updated to fetch from CDN:

```javascript
// www/v2/assets/js/manual.js
const HELP_CENTER_URL = 'https://studio27se.github.io/ehub/help-center.json';

async function loadHelpCenter() {
  const response = await fetch(HELP_CENTER_URL);
  const data = await response.json();
  return data;
}

// Render markdown to HTML in the webapp
function renderArticle(article) {
  const html = markdownToHtml(article.content); // Your markdown renderer
  displayHtml(html);
}
```

See `docs/CDN-STRATEGY.md` for deployment options.

## GitHub Actions Integration

### Auto-Documentation PRs

When PRs are opened in other repositories (webapp, backend-api, app-ionic), a GitHub Action automatically creates a documentation PR in this repository.

**Setup**: See `.github/workflows/README.md` for complete instructions.

### Publishing to CDN

GitHub Actions can automatically publish the generated JSON to:
- GitHub Pages
- Cloud storage (S3, Azure Blob, etc.)
- CDN services

See `docs/CDN-STRATEGY.md` for deployment strategies.

## Best Practices

### Writing Style

- ✅ Use clear, concise language
- ✅ Include examples and screenshots where appropriate
- ✅ Structure with headers (##, ###)
- ✅ Use lists for steps and options
- ✅ Link to related articles
- ❌ Don't include HTML (use Markdown)
- ❌ Don't embed videos directly (use links)

### Organization

- ✅ Group related articles in the same module
- ✅ Order articles from basic to advanced
- ✅ Keep articles focused on one topic
- ✅ Use descriptive IDs (e.g., `features-project-management`)
- ❌ Don't create too many modules (5-10 is ideal)
- ❌ Don't make articles too long (split if needed)

### Metadata

- ✅ Use consistent ID naming: `moduleId-article-name`
- ✅ Assign meaningful order numbers with gaps (1, 10, 20) for easy insertion
- ✅ Write clear, searchable titles
- ✅ Keep descriptions concise (1-2 sentences)
- ❌ Don't change IDs after publishing (breaks links)

## Icons

Available icons for modules:
- `rocket` - Getting started, onboarding
- `star` - Features, highlights
- `settings` - Configuration, preferences
- `plug` - Integrations, connections
- `wrench` - Troubleshooting, fixes
- `book` - Documentation, guides
- `shield` - Security, privacy
- `users` - Team, collaboration

These should map to icon sets used in your webapp (Font Awesome, Material Icons, etc.).

## Troubleshooting

### Validation Fails

```bash
# Check for errors
npm run validate

# Common issues:
# - Duplicate IDs: Check TOC for repeated module/article IDs
# - Missing files: Verify file paths are correct and relative to repo root
# - Missing metadata: Ensure all required frontmatter fields are present
```

### Build Produces Empty JSON

```bash
# Ensure TOC is valid YAML
cat help-center-toc.yaml | npx js-yaml

# Check file paths are correct
ls -la help-center/*/
```

### Article Not Appearing

1. Check article is listed in `help-center-toc.yaml`
2. Verify file path is correct
3. Ensure article has required frontmatter
4. Run `npm run build:validate`
5. Check generated `help-center.json`

## Contributing

1. **For content changes**: Edit Markdown files and update TOC
2. **For new articles**: Follow "Writing Documentation" guide
3. **For script changes**: Update `scripts/` files and test thoroughly
4. **Always run**: `npm run build:validate` before committing

## Migration from Existing System

If migrating from `www/v2/assets/js/help-center-content.json`:

1. **Review existing structure**: Note modules and articles
2. **Create matching modules**: Set up directories and TOC
3. **Convert articles**: Transform existing content to Markdown with frontmatter
4. **Validate**: Run `npm run build:validate`
5. **Compare output**: Ensure JSON structure is compatible
6. **Update webapp**: Point to new CDN endpoint
7. **Test**: Verify help center works in webapp
8. **Deploy**: Switch over with bundled fallback

## Support

- **Issues**: [GitHub Issues](https://github.com/studio27se/ehub/issues/)
- **Email**: support@studio27.se
- **Documentation Changes**: Open a PR in this repository

## License

Internal use only - Studio 27 AB
