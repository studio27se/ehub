# GitHub Actions Workflow Templates for Auto-Documentation

This directory contains templates and documentation for GitHub Actions workflows that automatically create documentation PRs in the `studio27se/ehub` repository when PRs are opened in other repositories.

## Overview

When a PR is opened in `studio27se/ehub-webapp`, `studio27se/ehub-backend-api`, or `studio27se/ehub-app-ionic`, a GitHub Actions workflow should automatically:

1. Analyze the PR title, description, and changed files
2. Create a branch in `studio27se/ehub` repository
3. Generate or update help center Markdown documentation
4. Open a PR in `studio27se/ehub` with the proposed documentation changes

## Setup Instructions

### Prerequisites

1. **GitHub App Token or PAT**: You need a token with permissions to create branches and PRs in `studio27se/ehub`
   - Recommended: Use a GitHub App installation token for better security
   - Alternative: Use a Personal Access Token (PAT) with `repo` scope
   
2. **Store Token as Secret**: In each repository (webapp, backend-api, app-ionic):
   - Go to Settings > Secrets and variables > Actions
   - Create a new secret named `EHUB_DOCS_TOKEN`
   - Paste the token value

### Required Permissions

The token must have these permissions:
- `contents`: write (to create branches and commit files)
- `pull_requests`: write (to create PRs)

## Workflow Template

Copy this template to `.github/workflows/auto-docs-pr.yml` in each of the following repositories:
- `studio27se/ehub-webapp`
- `studio27se/ehub-backend-api`
- `studio27se/ehub-app-ionic`

```yaml
name: Auto-create Documentation PR

on:
  pull_request:
    types: [opened, synchronize, edited]
    branches:
      - main
      - master
      - develop

jobs:
  create-docs-pr:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: read
      contents: read
    
    steps:
      - name: Checkout current repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get PR details
        id: pr-info
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          # Get PR information
          PR_TITLE="${{ github.event.pull_request.title }}"
          PR_BODY="${{ github.event.pull_request.body }}"
          PR_NUMBER="${{ github.event.pull_request.number }}"
          PR_URL="${{ github.event.pull_request.html_url }}"
          REPO_NAME="${{ github.repository }}"
          
          # Get list of changed files
          CHANGED_FILES=$(git diff --name-only origin/${{ github.event.pull_request.base.ref }}...HEAD | head -20)
          
          # Save to outputs
          echo "pr_title=$PR_TITLE" >> $GITHUB_OUTPUT
          echo "pr_number=$PR_NUMBER" >> $GITHUB_OUTPUT
          echo "pr_url=$PR_URL" >> $GITHUB_OUTPUT
          echo "repo_name=$REPO_NAME" >> $GITHUB_OUTPUT
          
          # Save changed files to a temp file
          echo "$CHANGED_FILES" > changed_files.txt
      
      - name: Checkout ehub repository
        uses: actions/checkout@v4
        with:
          repository: studio27se/ehub
          token: ${{ secrets.EHUB_DOCS_TOKEN }}
          path: ehub-docs
      
      - name: Create documentation branch
        working-directory: ehub-docs
        run: |
          BRANCH_NAME="docs/auto-pr-${{ steps.pr-info.outputs.pr_number }}-from-$(echo '${{ steps.pr-info.outputs.repo_name }}' | sed 's/studio27se\///' | sed 's/\//-/g')"
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git checkout -b "$BRANCH_NAME"
          echo "BRANCH_NAME=$BRANCH_NAME" >> $GITHUB_ENV
      
      - name: Generate documentation draft
        working-directory: ehub-docs
        run: |
          # Create a draft documentation file based on PR info
          REPO_SHORT=$(echo '${{ steps.pr-info.outputs.repo_name }}' | sed 's/studio27se\///')
          DOC_FILE="help-center/troubleshooting/draft-from-pr-${{ steps.pr-info.outputs.pr_number }}.md"
          
          cat > "$DOC_FILE" << 'EOF'
          ---
          id: draft-pr-${{ steps.pr-info.outputs.pr_number }}-$(echo $REPO_SHORT | sed 's/-//g')
          title: "[DRAFT] Documentation from ${{ steps.pr-info.outputs.pr_title }}"
          moduleId: troubleshooting
          order: 999
          draft: true
          ---
          
          # [DRAFT] Documentation Update
          
          **Source PR**: [${{ steps.pr-info.outputs.pr_title }}](${{ steps.pr-info.outputs.pr_url }})
          **Repository**: ${{ steps.pr-info.outputs.repo_name }}
          **PR Number**: #${{ steps.pr-info.outputs.pr_number }}
          
          ## PR Description
          
          ${{ github.event.pull_request.body }}
          
          ## Changed Files
          
          ```
          $(cat ../changed_files.txt)
          ```
          
          ## Action Items
          
          - [ ] Review the source PR and changes
          - [ ] Determine appropriate help center module (getting-started, features, settings, integrations, troubleshooting)
          - [ ] Write or update relevant documentation
          - [ ] Update `help-center-toc.yaml` if adding new articles
          - [ ] Remove this draft file after incorporating changes
          - [ ] Run `npm run build:validate` to generate and validate
          
          ## Suggested Documentation
          
          Based on the PR title and description, consider:
          
          - What new features or changes need to be documented?
          - Are there breaking changes that users need to know about?
          - Should existing articles be updated?
          - Do we need new troubleshooting guides?
          
          Please edit this draft or create new documentation files as appropriate.
          EOF
          
          git add "$DOC_FILE"
      
      - name: Commit and push changes
        working-directory: ehub-docs
        run: |
          git commit -m "docs: Auto-generated draft from ${{ steps.pr-info.outputs.repo_name }}#${{ steps.pr-info.outputs.pr_number }}"
          git push origin "$BRANCH_NAME"
      
      - name: Create Pull Request
        working-directory: ehub-docs
        env:
          GH_TOKEN: ${{ secrets.EHUB_DOCS_TOKEN }}
        run: |
          gh pr create \
            --title "📝 Documentation update from ${{ steps.pr-info.outputs.repo_name }}#${{ steps.pr-info.outputs.pr_number }}" \
            --body "This is an automatically generated PR for documentation updates based on:

          **Source PR**: ${{ steps.pr-info.outputs.pr_url }}
          **Repository**: ${{ steps.pr-info.outputs.repo_name }}
          **PR Title**: ${{ steps.pr-info.outputs.pr_title }}

          ## Review Checklist

          - [ ] Review the source PR to understand the changes
          - [ ] Update or create appropriate help center articles
          - [ ] Ensure article metadata (id, title, moduleId, order) is correct
          - [ ] Update \`help-center-toc.yaml\` if needed
          - [ ] Run \`npm run build:validate\` to test
          - [ ] Remove draft files after incorporating content
          - [ ] Verify generated JSON is correct

          ## Changed Files in Source PR

          \`\`\`
          $(cat ../changed_files.txt)
          \`\`\`

          Please review and edit the documentation as appropriate." \
            --base main \
            --head "$BRANCH_NAME"
```

## Workflow Explanation

### Trigger
- Activates when PRs are opened, synchronized, or edited
- Monitors main/master/develop branches

### Steps
1. **Checkout current repo**: Gets the source repository code
2. **Get PR details**: Extracts PR title, body, number, and changed files
3. **Checkout ehub**: Clones the ehub docs repository with write access
4. **Create branch**: Creates a new branch for the documentation changes
5. **Generate draft**: Creates a draft Markdown file with PR context
6. **Commit and push**: Commits the draft to the new branch
7. **Create PR**: Opens a PR in ehub repository with a checklist

### Security Notes

- Uses `EHUB_DOCS_TOKEN` secret for authentication to ehub repository
- Minimal permissions on source repository (read-only)
- Write permissions only to ehub repository via the token
- Bot commits are attributed to `github-actions[bot]`

## Customization

You can customize the workflow by:

1. **Different module placement**: Edit the `DOC_FILE` path to place drafts in different modules
2. **Template content**: Modify the draft template to include more context
3. **Trigger conditions**: Add or remove trigger types
4. **File analysis**: Add logic to suggest specific modules based on changed files

## Testing

To test the workflow:

1. Set up the token as a secret
2. Copy the workflow file to the repository
3. Open a test PR
4. Check the Actions tab for workflow execution
5. Verify a PR is created in ehub repository

## Troubleshooting

- **Workflow doesn't trigger**: Check branch names match your default branch
- **Token errors**: Verify token has correct permissions and is not expired
- **PR creation fails**: Ensure token has `pull_requests: write` permission
- **Branch already exists**: The workflow creates unique branch names per PR

## Next Steps

After setting up the workflows:

1. Monitor initial runs to ensure they work correctly
2. Train team members on reviewing auto-generated doc PRs
3. Iterate on the draft template based on feedback
4. Consider adding AI-powered content suggestions in the future
