---
title: "Automatisk GET-anrop Upptäckt"
---

# Automatisk GET-anrop Upptäckt

Detta dokument innehåller scripts och verktyg för att automatiskt upptäcka GET-anrop i ehub-app-ionic mobilapplikationen.

## Bash Script för GET-anrop Upptäckt

Kör följande script i roten av ehub-app-ionic repository för att generera en initial lista över GET-anrop:

```bash
#!/bin/bash
# get-requests-scanner.sh
# Script för att hitta alla GET-anrop i Ionic/Angular applikation

echo "🔍 Scanning for GET requests in eHUB mobile app..."
echo "=============================================="

# Skapa output-mapp
mkdir -p scan-results
OUTPUT_FILE="scan-results/get-requests-$(date +%Y%m%d-%H%M%S).txt"

echo "📊 Scanning Results - $(date)" > $OUTPUT_FILE
echo "=============================================" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Hitta TypeScript filer med GET-anrop
echo "🔎 Searching for TypeScript GET requests..."
echo "## TypeScript GET Requests" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

find src/ -name "*.ts" -type f | while read file; do
    # Sök efter olika mönster för GET-anrop
    grep -n -E "(\.get\(|GET|httpGet|this\.http\.get)" "$file" 2>/dev/null | while read match; do
        echo "**File:** $file" >> $OUTPUT_FILE
        echo "**Line:** $match" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    done
done

# Hitta JavaScript filer med GET-anrop  
echo "🔎 Searching for JavaScript GET requests..."
echo "## JavaScript GET Requests" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

find src/ -name "*.js" -type f | while read file; do
    grep -n -E "(\.get\(|GET|httpGet)" "$file" 2>/dev/null | while read match; do
        echo "**File:** $file" >> $OUTPUT_FILE
        echo "**Line:** $match" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    done
done

# Hitta HTML filer med GET-relaterade attribut
echo "🔎 Searching for HTML GET references..."
echo "## HTML GET References" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

find src/ -name "*.html" -type f | while read file; do
    grep -n -E "(http\.get|GET)" "$file" 2>/dev/null | while read match; do
        echo "**File:** $file" >> $OUTPUT_FILE
        echo "**Line:** $match" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    done
done

# Sammanfattning
echo "📈 Generating summary..."
echo "## Summary" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

ts_count=$(find src/ -name "*.ts" -exec grep -l -E "(\.get\(|GET|httpGet)" {} \; 2>/dev/null | wc -l)
js_count=$(find src/ -name "*.js" -exec grep -l -E "(\.get\(|GET|httpGet)" {} \; 2>/dev/null | wc -l)

echo "- TypeScript files with GET requests: $ts_count" >> $OUTPUT_FILE
echo "- JavaScript files with GET requests: $js_count" >> $OUTPUT_FILE
echo "- Total files scanned: $(find src/ -name "*.ts" -o -name "*.js" | wc -l)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "✅ Scan complete! Results saved to: $OUTPUT_FILE"
echo "📋 Next steps:"
echo "   1. Review the results file"
echo "   2. Categorize endpoints by module"
echo "   3. Update the documentation with findings"
```

## PowerShell Script (Windows)

För Windows-användare:

```powershell
# get-requests-scanner.ps1
# PowerShell script för att hitta GET-anrop

Write-Host "🔍 Scanning for GET requests in eHUB mobile app..." -ForegroundColor Green

# Skapa output-mapp
New-Item -ItemType Directory -Force -Path "scan-results" | Out-Null
$outputFile = "scan-results/get-requests-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"

"📊 Scanning Results - $(Get-Date)" | Out-File -FilePath $outputFile
"=============================================" | Out-File -FilePath $outputFile -Append
"" | Out-File -FilePath $outputFile -Append

Write-Host "🔎 Searching for TypeScript GET requests..." -ForegroundColor Yellow

# Sök i TypeScript filer
Get-ChildItem -Path "src" -Filter "*.ts" -Recurse | ForEach-Object {
    $file = $_.FullName
    $matches = Select-String -Path $file -Pattern "(\.get\(|GET|httpGet|this\.http\.get)" -AllMatches
    
    if ($matches) {
        "## File: $($_.Name)" | Out-File -FilePath $outputFile -Append
        "**Path:** $file" | Out-File -FilePath $outputFile -Append
        
        foreach ($match in $matches) {
            "**Line $($match.LineNumber):** $($match.Line.Trim())" | Out-File -FilePath $outputFile -Append
        }
        
        "" | Out-File -FilePath $outputFile -Append
    }
}

Write-Host "✅ Scan complete! Results saved to: $outputFile" -ForegroundColor Green
```

## Node.js Script för Djupare Analys

För mer avancerad analys kan du använda detta Node.js script:

```javascript
// get-requests-analyzer.js
const fs = require('fs');
const path = require('path');

class GetRequestAnalyzer {
    constructor(srcPath = './src') {
        this.srcPath = srcPath;
        this.results = [];
    }

    async scanFiles() {
        console.log('🔍 Starting deep scan for GET requests...');
        
        await this.walkDirectory(this.srcPath);
        
        console.log(`📊 Found ${this.results.length} potential GET requests`);
        
        // Generera rapport
        this.generateReport();
    }

    async walkDirectory(dir) {
        const files = fs.readdirSync(dir);
        
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            
            if (stat.isDirectory()) {
                await this.walkDirectory(filePath);
            } else if (file.endsWith('.ts') || file.endsWith('.js')) {
                await this.analyzeFile(filePath);
            }
        }
    }

    async analyzeFile(filePath) {
        const content = fs.readFileSync(filePath, 'utf8');
        const lines = content.split('\n');
        
        lines.forEach((line, index) => {
            // Olika mönster för GET-anrop
            const patterns = [
                /\.get\s*\(/,
                /this\.http\.get/,
                /this\.httpClient\.get/,
                /axios\.get/,
                /fetch\s*\(/,
                /@Get\s*\(/,
            ];
            
            patterns.forEach(pattern => {
                if (pattern.test(line)) {
                    this.results.push({
                        file: filePath.replace('./src/', ''),
                        line: index + 1,
                        code: line.trim(),
                        type: this.classifyRequest(line),
                        endpoint: this.extractEndpoint(line)
                    });
                }
            });
        });
    }

    classifyRequest(line) {
        if (line.includes('user') || line.includes('auth')) return 'Authentication';
        if (line.includes('project')) return 'Project Management';
        if (line.includes('company') || line.includes('organization')) return 'Organization';
        if (line.includes('invoice') || line.includes('payment')) return 'Finance';
        if (line.includes('customer') || line.includes('client')) return 'CRM';
        if (line.includes('document') || line.includes('file')) return 'Document Management';
        if (line.includes('notification')) return 'Notifications';
        if (line.includes('dashboard') || line.includes('report')) return 'Reporting';
        if (line.includes('settings') || line.includes('config')) return 'Settings';
        return 'Other';
    }

    extractEndpoint(line) {
        // Försök extrahera endpoint från koden
        const urlMatches = line.match(/['"`]([^'"`]*\/api[^'"`]*?)['"`]/);
        if (urlMatches) {
            return urlMatches[1];
        }
        
        const templateMatches = line.match(/\`([^`]*\/api[^`]*?)\`/);
        if (templateMatches) {
            return templateMatches[1];
        }
        
        return 'URL not found';
    }

    generateReport() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportFile = `scan-results/detailed-analysis-${timestamp}.md`;
        
        // Skapa mapp om den inte finns
        if (!fs.existsSync('scan-results')) {
            fs.mkdirSync('scan-results');
        }
        
        let report = `# GET Requests Analysis Report\n\nGenerated: ${new Date().toISOString()}\n\n`;
        
        // Gruppera per typ
        const byType = this.results.reduce((acc, item) => {
            acc[item.type] = acc[item.type] || [];
            acc[item.type].push(item);
            return acc;
        }, {});
        
        Object.entries(byType).forEach(([type, requests]) => {
            report += `## ${type} (${requests.length} requests)\n\n`;
            report += `| File | Line | Endpoint | Code |\n`;
            report += `|------|------|----------|------|\n`;
            
            requests.forEach(req => {
                report += `| ${req.file} | ${req.line} | ${req.endpoint} | \`${req.code}\` |\n`;
            });
            
            report += '\n';
        });
        
        fs.writeFileSync(reportFile, report);
        console.log(`📄 Detailed report saved to: ${reportFile}`);
    }
}

// Kör analyzer
const analyzer = new GetRequestAnalyzer();
analyzer.scanFiles().catch(console.error);
```

## Användning

1. **Bash Script**: Spara som `get-requests-scanner.sh`, gör executable med `chmod +x`, kör med `./get-requests-scanner.sh`

2. **PowerShell Script**: Spara som `get-requests-scanner.ps1`, kör med `.\get-requests-scanner.ps1`

3. **Node.js Script**: Spara som `get-requests-analyzer.js`, kör med `node get-requests-analyzer.js`

## Output Format

Alla scripts genererar rapporter i `scan-results/` mappen med timestamps. Rapporterna innehåller:

- Filens sökväg
- Radnummer
- Kod som innehåller GET-anropet
- Klassificering av anropet (när möjligt)
- Extraherad endpoint URL (när möjligt)

## Nästa Steg

Efter att ha kört dessa scripts:

1. Granska genererade rapporter
2. Manuellt verifiera och klassificera endpoints
3. Uppdatera [mobilapplikationens GET-anrop dokumentation](mobile-app-get-requests)
4. Prioritera optimeringsarbete baserat på frekvens och komplexitet