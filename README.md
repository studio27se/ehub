# Introduction
This repository serves two primary purposes for the eHUB online entrepreneur operations and documentation software:

1. **Issue Tracking**: Report bugs, suggest improvements, and track feature requests through the [issues](https://github.com/studio27se/ehub/issues/) tab. Issues cover not only problems but also enhancements and refactors.

2. **Help Center Documentation**: Source of truth for eHUB's help center, containing Markdown-based documentation that is consumed by the webapp, mobile app, and other clients. See the [Help Center README](help-center/README.md) for details.

You can always ask questions through the contact form on our [webpage](https://studio27.se/contact/).

# Release Schedule

This section outlines the upcoming release dates for eHUB as holistic system.

## Release Cadence
- **Frequency:** Releases are planned on a fortnight basis.
- **Release Days:** Thursday, typically at 09.00pm CET.

## Release Types
- **Major Releases:** Introduce significant new features or changes. Indicated by increase in the first number of the version. (e.g., v**3**.0.0)
- **Minor Releases:** Add enhancements or smaller features. Indicated by increase of the second number of the version. (e.g., v2.**12**.0)
- **Patch Releases:** Focus on bug fixes or urgent updates. Indicated by increase of the third number of the version. (e.g., v2.11.**1**)

## Upcoming and Deployed Releases

| Release Version | Date         | Notes                           |
| --------------- | ------------ | ------------------------------- |
|[v2.27.0](https://github.com/studio27se/ehub/releases/tag/v2.27.3)|Jun 11, 2026||
|[v2.28.0](https://github.com/studio27se/ehub/releases/tag/v2.28.0)|Jun 23, 2026||
|v2.29.0|Jul 9, 2026||




## Communication
- **Release Notes:** All updates will be documented in the repository [releases](https://github.com/studio27se/ehub/releases).
- **Notifications:** User's with impacted change requests will be noted for testing in the acceptance environment, as well as when the package is released.

## Contribution to Releases
Contributors can view planned features in the [issues list](https://github.com/studio27se/ehub/issues/) and propose changes by creating new issues.

# Help Center Documentation

This repository contains the source of truth for eHUB's help center documentation.

## Quick Start

```bash
# Install dependencies
npm install

# Validate documentation
npm run validate

# Generate help-center.json
npm run build

# Validate and build together
npm run build:validate
```

## Documentation Structure

- **`help-center/`** - Markdown documentation files organized by module
- **`help-center-toc.yaml`** - Table of contents defining structure and metadata
- **`scripts/`** - Generator and validation scripts
- **`.github/workflows/`** - GitHub Actions templates for automation

## Learn More

- [Help Center Documentation Guide](help-center/README.md) - Complete guide for writing and managing documentation
- [CDN Deployment Strategy](docs/CDN-STRATEGY.md) - How to serve documentation via CDN
- [GitHub Actions Setup](.github/workflows/README.md) - Automated documentation PR workflows

---

