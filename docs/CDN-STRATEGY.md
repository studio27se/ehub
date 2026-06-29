# CDN Consumption Strategy

This document outlines strategies for serving the generated help center JSON file from a CDN-like endpoint rather than embedding it directly in the webapp repository.

## Overview

The generated `help-center.json` file should be served from a stable, cached endpoint that can be consumed by:
- Web application (`studio27se/ehub-webapp`)
- Backend API (`studio27se/ehub-backend-api`)
- Mobile app (`studio27se/ehub-app-ionic`)

## Recommended Approaches

### Option 1: GitHub Pages (Recommended)

**Pros:**
- Free hosting
- Automatic HTTPS
- Good CDN coverage
- Simple deployment via GitHub Actions
- Version control built-in

**Cons:**
- Public only (not suitable for private/confidential docs)
- Rate limits for high-traffic sites

**Implementation:**

1. **Enable GitHub Pages** on the `studio27se/ehub` repository:
   - Go to Settings > Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` or `main`
   - Folder: `/docs` or `/ (root)`

2. **Add GitHub Action to publish JSON**:

```yaml
name: Deploy Help Center to GitHub Pages

on:
  push:
    branches:
      - main
    paths:
      - 'help-center/**'
      - 'help-center-toc.yaml'
      - 'scripts/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Validate and build
        run: npm run build:validate
      
      - name: Create public directory
        run: |
          mkdir -p public
          cp help-center.json public/
          echo '{ "version": "1.0.0", "endpoints": { "help-center": "help-center.json" } }' > public/index.json
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'public'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

3. **Access the JSON**:
   - URL: `https://studio27se.github.io/ehub/help-center.json`
   - With custom domain: `https://docs.ehub.se/help-center.json`

4. **Consume in webapp**:

```javascript
// www/v2/assets/js/manual.js or similar
const HELP_CENTER_URL = 'https://studio27se.github.io/ehub/help-center.json';

async function loadHelpCenter() {
  try {
    const response = await fetch(HELP_CENTER_URL);
    const helpCenter = await response.json();
    return helpCenter;
  } catch (error) {
    console.error('Failed to load help center:', error);
    // Fallback to bundled version if needed
    return loadBundledHelpCenter();
  }
}
```

### Option 2: GitHub Releases

**Pros:**
- Simple to implement
- Versioned artifacts
- Good for tagged releases
- Works with private repos

**Cons:**
- Requires manual or automated release process
- Not real-time updates
- Need to manage versions in consumers

**Implementation:**

1. **Add release workflow**:

```yaml
name: Release Help Center

on:
  push:
    tags:
      - 'help-center-v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install and build
        run: |
          npm ci
          npm run build:validate
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: help-center.json
          body: |
            Help Center JSON for ${{ github.ref_name }}
            
            Download URL: 
            `https://github.com/studio27se/ehub/releases/download/${{ github.ref_name }}/help-center.json`
```

2. **Consume in webapp**:

```javascript
const HELP_CENTER_VERSION = 'help-center-v1.0.0';
const HELP_CENTER_URL = `https://github.com/studio27se/ehub/releases/download/${HELP_CENTER_VERSION}/help-center.json`;
```

### Option 3: Cloud Storage (S3, Azure Blob, Google Cloud Storage)

**Pros:**
- Full control over caching and CDN
- Can use CloudFront/Azure CDN/Cloud CDN
- Suitable for high-traffic applications
- Can serve private content with authentication

**Cons:**
- Additional infrastructure costs
- More complex setup
- Requires cloud provider credentials

**Implementation Example (AWS S3 + CloudFront):**

1. **Create S3 bucket**: `ehub-help-center`
2. **Enable static website hosting**
3. **Set up CloudFront distribution**
4. **Add GitHub Action**:

```yaml
name: Deploy to S3

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
      
      - name: Build
        run: |
          npm ci
          npm run build:validate
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-north-1
      
      - name: Upload to S3
        run: |
          aws s3 cp help-center.json s3://ehub-help-center/help-center.json \
            --cache-control "public, max-age=300" \
            --content-type "application/json"
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/help-center.json"
```

### Option 4: jsDelivr CDN (GitHub)

**Pros:**
- Free CDN for public GitHub repos
- Fast global delivery
- Automatic caching
- No setup required

**Cons:**
- Public only
- Limited to GitHub public repos
- Cache can be aggressive

**Implementation:**

1. Commit `help-center.json` to the repository
2. Access via jsDelivr:
   - Latest: `https://cdn.jsdelivr.net/gh/studio27se/ehub/help-center.json`
   - Specific commit: `https://cdn.jsdelivr.net/gh/studio27se/ehub@{commit-hash}/help-center.json`
   - Specific tag: `https://cdn.jsdelivr.net/gh/studio27se/ehub@v1.0.0/help-center.json`

## Caching Strategy

Regardless of the approach chosen, implement proper caching:

### HTTP Cache Headers

```
Cache-Control: public, max-age=300, s-maxage=600
ETag: "<content-hash>"
```

- `max-age=300`: Browser cache for 5 minutes
- `s-maxage=600`: CDN cache for 10 minutes
- Use ETag for efficient revalidation

### Application-Level Caching

```javascript
// In webapp
class HelpCenterCache {
  constructor() {
    this.cache = null;
    this.cacheTime = null;
    this.cacheDuration = 5 * 60 * 1000; // 5 minutes
  }
  
  async get() {
    if (this.cache && Date.now() - this.cacheTime < this.cacheDuration) {
      return this.cache;
    }
    
    this.cache = await fetch(HELP_CENTER_URL).then(r => r.json());
    this.cacheTime = Date.now();
    return this.cache;
  }
  
  invalidate() {
    this.cache = null;
    this.cacheTime = null;
  }
}
```

## Versioning

For production stability, consider versioned endpoints:

```
https://cdn.example.com/help-center/v1/help-center.json
https://cdn.example.com/help-center/v2/help-center.json
```

This allows:
- Gradual rollout of documentation changes
- A/B testing of help content
- Rollback capability
- Breaking change management

## Migration Plan

1. **Phase 1**: Deploy JSON to CDN while keeping bundled version
2. **Phase 2**: Update webapp to fetch from CDN with bundled fallback
3. **Phase 3**: Monitor usage and error rates
4. **Phase 4**: Remove bundled version after stability confirmed

## Monitoring

Track these metrics:
- CDN cache hit rate
- Response times
- Error rates
- Bandwidth usage
- User-facing load times

## Recommendation Summary

**For eHUB**: Use **GitHub Pages** (Option 1) because:
- Zero cost
- Simple setup
- Reliable
- Integrates well with existing GitHub workflow
- Easy to add custom domain later

If you need private documentation, use **GitHub Releases** (Option 2) with a private repo and authentication tokens.
