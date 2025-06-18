#!/usr/bin/env node

/**
 * Generate Reference Files Script
 * 
 * This script generates thepia-whitepaper-reference.html and thepia-whitepaper-reference.css
 * from Astro source files to ensure our layouts can reproduce the exact reference structure.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');

// Configuration
const SRC_STYLES_DIR = path.join(projectRoot, 'src/styles');
const OUTPUT_DIR = path.join(projectRoot, 'tests/output/reference-generation');
const REFERENCE_DIR = path.join(projectRoot, 'tests/reference/weasyprint');

console.log('🚀 Generating Reference Files from Astro Sources');
console.log('=' * 50);

// Ensure directories exist
if (!existsSync(OUTPUT_DIR)) {
  mkdirSync(OUTPUT_DIR, { recursive: true });
}
if (!existsSync(REFERENCE_DIR)) {
  mkdirSync(REFERENCE_DIR, { recursive: true });
}

/**
 * Generate thepia-whitepaper-reference.css from src/styles
 */
function generateReferenceCSS() {
  console.log('\n📄 Generating thepia-whitepaper-reference.css...');
  
  const cssFiles = [
    'whitepaper-base.css',
    'whitepaper-print.css',
    'whitepaper-cover.css',
    'whitepaper-cover-typography.css',
    'whitepaper-components.css'
  ];
  
  let combinedCss = '/* Thepia Whitepaper Reference Template - Generated from src/styles */\n\n';
  
  for (const cssFile of cssFiles) {
    const cssPath = path.join(SRC_STYLES_DIR, cssFile);
    if (existsSync(cssPath)) {
      const cssContent = readFileSync(cssPath, 'utf-8');
      combinedCss += `/* === ${cssFile.toUpperCase()} === */\n`;
      combinedCss += cssContent;
      combinedCss += '\n\n';
      console.log(`  ✅ Included: ${cssFile}`);
    } else {
      console.log(`  ❌ Missing: ${cssFile}`);
    }
  }
  
  // Add Thepia brand variables
  combinedCss += `/* === THEPIA BRAND VARIABLES === */\n`;
  combinedCss += `:root {\n`;
  combinedCss += `  --accentColor: #988aca; /* Thepia lavender */\n`;
  combinedCss += `  --coverBackgroundColor: #988aca;\n`;
  combinedCss += `}\n`;
  
  // Write to output directory
  const outputPath = path.join(OUTPUT_DIR, 'thepia-whitepaper-reference.css');
  writeFileSync(outputPath, combinedCss, 'utf-8');
  
  // Copy to reference directory
  const referencePath = path.join(REFERENCE_DIR, 'thepia-whitepaper-reference.css');
  writeFileSync(referencePath, combinedCss, 'utf-8');
  
  console.log(`  📄 Generated: ${outputPath}`);
  console.log(`  📄 Updated reference: ${referencePath}`);
  console.log(`  📊 Total size: ${combinedCss.length} characters`);
  
  return combinedCss;
}

/**
 * Generate thepia-whitepaper-reference.html from layout structure
 */
function generateReferenceHTML() {
  console.log('\n📄 Generating thepia-whitepaper-reference.html...');
  
  const content = {
    title: "Digital Transformation ROI Analysis",
    description: "A comprehensive analysis of return on investment for digital transformation initiatives in modern enterprises",
    author: "Thepia Research Team",
    publishDate: new Date('2024-06-01'),
    accentColor: "#988aca",
    coverDesign: "classic",
    showTableOfContents: true,
    showCoverPage: true
  };
  
  const formattedDate = content.publishDate.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const html = `<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${content.title} - Thepia Research</title>
  <link rel="stylesheet" href="thepia-whitepaper-reference.css">
</head>

<body>

  <!-- COVER PAGE -->
  <div id="cover" class="cover-page">
    <div class="cover-content">
      <h1 class="cover-title">${content.title}</h1>
      <p class="cover-subtitle">${content.description}</p>

      <div class="cover-meta">
        <p><strong>${content.author}</strong></p>
        <p>${formattedDate}</p>
      </div>
    </div>

    <div class="cover-logo">THEPIA</div>
  </div>

  <!-- TABLE OF CONTENTS -->
  <div id="contents">
    <h2>Table of Contents</h2>

    <div class="toc-section">
      <h3>Executive Summary</h3>
      <ul>
        <li><a href="#executive-summary">Key Findings and Recommendations</a></li>
        <li><a href="#methodology">Research Methodology</a></li>
      </ul>
    </div>

    <div class="toc-section">
      <h3>Analysis</h3>
      <ul>
        <li><a href="#market-overview">Market Overview and Trends</a></li>
        <li><a href="#roi-metrics">ROI Metrics and Benchmarks</a></li>
        <li><a href="#case-studies">Enterprise Case Studies</a></li>
      </ul>
    </div>

    <div class="toc-section">
      <h3>Recommendations</h3>
      <ul>
        <li><a href="#implementation">Implementation Framework</a></li>
        <li><a href="#conclusions">Conclusions and Next Steps</a></li>
      </ul>
    </div>
  </div>

  <!-- EXECUTIVE SUMMARY -->
  <div id="executive-summary">
    <h2>Executive Summary</h2>

    <div class="executive-summary">
      <p><strong>Key Finding:</strong> Organizations implementing comprehensive digital transformation initiatives
        achieve an average ROI of 312% within 24 months, with leading enterprises reaching 450% returns through
        strategic technology adoption and organizational change management.</p>
    </div>

    <h3 id="methodology">Research Methodology</h3>

    <p>This analysis examines digital transformation ROI across 247 enterprise organizations spanning multiple
      industries. Our research methodology combines quantitative financial analysis with qualitative organizational
      assessment to provide comprehensive insights into transformation success factors.</p>

    <div class="callout">
      <p><strong>Research Scope:</strong> 247 enterprises across 12 industries, $50M+ annual revenue, 18-month
        transformation timeline analysis</p>
    </div>
  </div>

  <!-- MARKET OVERVIEW -->
  <div id="market-overview">
    <h2>Market Overview and Trends</h2>

    <h3>Digital Transformation Investment Patterns</h3>

    <p>Enterprise digital transformation spending has accelerated significantly, with organizations allocating an
      average of 8.2% of annual revenue to technology modernization initiatives. This represents a 340% increase from
      pre-2020 baseline levels.</p>

    <div class="two-column">
      <p>The acceleration in digital transformation investment reflects fundamental shifts in business operations,
        customer expectations, and competitive dynamics. Organizations are no longer viewing digital transformation as
        optional but as essential for survival and growth in an increasingly digital economy.</p>

      <p>Leading organizations demonstrate sophisticated approaches to transformation planning, emphasizing strategic
        alignment, change management, and measurable outcomes. These enterprises consistently outperform peers in both
        transformation success rates and financial returns.</p>
    </div>
  </div>

  <!-- ROI METRICS -->
  <div id="roi-metrics">
    <h2>ROI Metrics and Benchmarks</h2>

    <h3>Financial Performance Analysis</h3>

    <p>Our analysis reveals significant variation in transformation ROI based on organizational maturity, implementation
      approach, and strategic alignment. The following table summarizes key performance metrics across different
      enterprise categories:</p>

    <table>
      <thead>
        <tr>
          <th>Organization Type</th>
          <th>Average ROI (%)</th>
          <th>Payback Period (Months)</th>
          <th>Success Rate (%)</th>
          <th>Key Success Factors</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Digital Leaders</td>
          <td>450%</td>
          <td>14</td>
          <td>89%</td>
          <td>Strategic alignment, change management</td>
        </tr>
        <tr>
          <td>Fast Followers</td>
          <td>312%</td>
          <td>18</td>
          <td>72%</td>
          <td>Proven technologies, phased approach</td>
        </tr>
        <tr>
          <td>Traditional Adopters</td>
          <td>185%</td>
          <td>24</td>
          <td>58%</td>
          <td>Risk mitigation, vendor partnerships</td>
        </tr>
        <tr>
          <td>Laggards</td>
          <td>95%</td>
          <td>36</td>
          <td>34%</td>
          <td>Compliance-driven, limited scope</td>
        </tr>
      </tbody>
    </table>

    <blockquote>
      <p>"The most successful digital transformations are not technology projects—they are business transformation
        initiatives enabled by technology. Organizations that understand this distinction consistently achieve superior
        outcomes."</p>
      <cite>— Chief Digital Officer, Fortune 500 Financial Services Company</cite>
    </blockquote>
  </div>

  <!-- CONCLUSIONS -->
  <div id="conclusions">
    <h2>Conclusions and Next Steps</h2>

    <h3>Key Recommendations</h3>

    <div class="recommendations">
      <div class="recommendation">
        <h4>1. Establish Clear Success Metrics</h4>
        <p>Define measurable outcomes aligned with business objectives. Organizations with well-defined success metrics
          achieve 67% higher ROI than those without clear measurement frameworks.</p>
      </div>

      <div class="recommendation">
        <h4>2. Invest in Change Management</h4>
        <p>Allocate 20-25% of transformation budget to change management and training. Human factors are the primary
          determinant of transformation success or failure.</p>
      </div>

      <div class="recommendation">
        <h4>3. Adopt Phased Implementation</h4>
        <p>Implement transformation in manageable phases with clear milestones. Phased approaches reduce risk and enable
          course correction based on early learnings.</p>
      </div>
    </div>

    <div class="final-callout">
      <p><strong>The Digital Imperative:</strong> Organizations that delay digital transformation face increasing
        competitive disadvantage. The window for transformation leadership is narrowing, making immediate action
        essential for long-term viability.</p>
    </div>

    <div class="references">
      <h3>References and Methodology</h3>
      <p>This analysis is based on primary research conducted between January 2023 and May 2024, including surveys of
        247 enterprise organizations, 89 in-depth interviews with transformation leaders, and financial analysis of
        publicly available data.</p>
    </div>
  </div>

</body>

</html>`;

  // Write to output directory
  const outputPath = path.join(OUTPUT_DIR, 'thepia-whitepaper-reference.html');
  writeFileSync(outputPath, html, 'utf-8');
  
  // Copy to reference directory
  const referencePath = path.join(REFERENCE_DIR, 'thepia-whitepaper-reference.html');
  writeFileSync(referencePath, html, 'utf-8');
  
  console.log(`  📄 Generated: ${outputPath}`);
  console.log(`  📄 Updated reference: ${referencePath}`);
  console.log(`  📊 Total size: ${html.length} characters`);
  
  return html;
}

/**
 * Main execution
 */
function main() {
  try {
    const css = generateReferenceCSS();
    const html = generateReferenceHTML();
    
    console.log('\n✅ Reference files generated successfully!');
    console.log('\n📋 Summary:');
    console.log(`  📄 HTML: ${html.length} characters`);
    console.log(`  🎨 CSS: ${css.length} characters`);
    console.log(`  📁 Output: ${OUTPUT_DIR}`);
    console.log(`  📁 Reference: ${REFERENCE_DIR}`);
    
    console.log('\n🎯 Next Steps:');
    console.log('  1. Review generated files in tests/output/reference-generation/');
    console.log('  2. Test PDF generation with: buckia pdf render tests/reference/weasyprint/thepia-whitepaper-reference.html');
    console.log('  3. Compare output with existing reference PDF');
    
  } catch (error) {
    console.error('❌ Error generating reference files:', error.message);
    process.exit(1);
  }
}

main();
