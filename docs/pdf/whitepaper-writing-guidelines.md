# Whitepaper Writing Guidelines

**For thepia.com Documentation**

This guide provides comprehensive instructions for creating, formatting, and maintaining professional whitepapers that generate high-quality PDFs using the Buckia PDF generation system.

## 📋 **Quick Reference**

### **For Writers**
- Follow [Thepia Writing Guidelines](https://github.com/thepian/thepia.com/blob/main/docs/content/writing-guidelines.md)
- Use this whitepaper structure template
- Optimize content for both web and PDF formats
- Include proper citations and sources

### **For Developers**
- Use Buckia CSS override system for PDF styling
- Test PDF generation with `--local-only` flag
- Maintain PDF template CSS files
- Follow [PDF Best Practices](https://github.com/thepian/buckia/blob/main/docs/pdf-best-practices.md)

## 📖 **Whitepaper Structure Template**

### **Required Frontmatter**
```markdown
---
title: "The Hidden Costs of Manual Employee Offboarding"
description: "A comprehensive analysis of inefficiencies in manual HR processes"
author: "Thepia Team"
publishDate: 2024-06-14
uid: "a7f3c8e9-2d4b-4c1a-9e8f-1b2c3d4e5f6a"  # Required: Unique identifier
tags: ["HR", "Automation", "Digital Transformation"]
category: "Business Process"
featured: true
pdfTemplate: "thepia-whitepaper"  # PDF template to use
---
```

### **Content Structure**
```markdown
# [Whitepaper Title]

## Executive Summary
*2-3 paragraphs summarizing key findings and recommendations*

## Introduction
*Problem statement and context*

## [Main Section 1]
*Core content with evidence and analysis*

## [Main Section 2]
*Supporting analysis and case studies*

## Key Findings
*Bullet points of main discoveries*

## Recommendations
*Actionable next steps*

## Conclusion
*Summary and call to action*

## References
*Numbered citations with sources*
```

## ✍️ **Writing Standards**

### **Content Requirements**
- **Length**: 2,000-4,000 words for comprehensive coverage
- **Tone**: Professional, authoritative, evidence-based
- **Audience**: Business decision-makers and technical professionals
- **Citations**: All claims must be supported by credible sources

### **Formatting Guidelines**

#### **Headings**
```markdown
# Main Title (H1) - Only one per document
## Section Headings (H2) - Primary sections
### Subsections (H3) - Supporting topics
```

#### **Lists and Bullets**
```markdown
**Key Benefits:**
- Clear, actionable benefit statements
- Use parallel structure
- Start with action verbs when possible
```

#### **Citations**
```markdown
Manual processes cost organizations an average of $12,000 per employee annually [1].

## References
[1] Society for Human Resource Management. (2024). "HR Technology Survey Report." 
https://www.shrm.org/research/survey-findings/hr-technology-survey
Quote: "Organizations using manual HR processes report 40% higher administrative costs..."
```

## 🖼️ **Image Guidelines**

### **Image Requirements**
- **Format**: PNG, JPG, or WebP
- **Location**: `src/assets/whitepapers/[whitepaper-name]/`
- **Naming**: Descriptive filenames (e.g., `employee-offboarding-process-chart.png`)
- **Size**: Optimize for web (under 500KB) - Astro will optimize further

### **Image Markdown**
```markdown
![Employee Offboarding Process Chart](../../assets/whitepapers/hidden-cost-brief/employee-offboarding-mindmap.webp)

*Figure 1: Traditional vs. Automated Offboarding Process Comparison*
```

### **PDF-Optimized Images**
- **Max width**: Images will be constrained to 13cm in PDF
- **Categories**: Use CSS classes for different image types:
  - `.logo` - Company logos (max 4cm)
  - `.diagram` - Process diagrams (max 10cm)
  - `.screenshot` - Software screenshots (max 12cm)
  - `.full-width` - Full-width illustrations (max 13cm)

## 📄 **PDF Template System**

### **Available Templates**
1. **`thepia-whitepaper`** - Standard Thepia-branded template
2. **`thepia-case-study`** - Case study format
3. **`thepia-technical`** - Technical documentation style

### **Template Selection**
Add to frontmatter:
```markdown
---
pdfTemplate: "thepia-whitepaper"
---
```

### **Custom Styling**
For special formatting needs, add CSS classes:
```markdown
<div class="executive-summary">
Key insights and recommendations...
</div>

<div class="callout">
Important note or highlight
</div>

<div class="page-break"></div>
```

## 🔧 **Development Workflow**

### **1. Content Creation**
```bash
# Create new whitepaper file
touch src/content/whitepapers/your-whitepaper.md

# Add images to assets
mkdir src/assets/whitepapers/your-whitepaper/
# Add images to this directory
```

### **2. Local Development**
```bash
# Start development server
npm run dev

# Preview at: http://localhost:4321/whitepapers/your-whitepaper/
```

### **3. PDF Generation**
```bash
# Build the site
npm run build

# Generate PDF locally (for testing)
buckia pdf render dist/whitepapers/your-whitepaper/index.html thepia-cdn unique-id your-whitepaper --local-only --css-override pdf-styles/thepia-whitepaper-template.css

# Generate and upload to CDN
buckia pdf render dist/whitepapers/your-whitepaper/index.html thepia-cdn $(date +%s) your-whitepaper --css-override pdf-styles/thepia-whitepaper-template.css
```

## 🎨 **Template Maintenance**

### **CSS Template Files**
```
thepia.com/
├── pdf-styles/
│   ├── thepia-whitepaper-template.css    # Standard template
│   ├── thepia-case-study-template.css    # Case study variant
│   └── thepia-technical-template.css     # Technical docs variant
```

### **Template Updates**
When updating PDF templates:

1. **Test locally** with existing whitepapers
2. **Check image sizing** and layout
3. **Verify page breaks** work correctly
4. **Update this documentation** if structure changes

### **Common Template Customizations**
```css
/* Brand colors */
.text-primary { color: #3182ce !important; }
.bg-primary { background-color: #ebf8ff !important; }

/* Special sections */
.executive-summary {
  background: #f7fafc !important;
  border-left: 4pt solid #3182ce !important;
  padding: 0.8cm !important;
}

/* Image sizing */
.logo { max-width: 4cm !important; }
.diagram { max-width: 10cm !important; }
.screenshot { max-width: 12cm !important; }
```

## ✅ **Quality Checklist**

### **Before Publishing**
- [ ] Content follows [Thepia Writing Guidelines](https://github.com/thepian/thepia.com/blob/main/docs/content/writing-guidelines.md)
- [ ] All claims are properly cited with credible sources
- [ ] Images are optimized and properly referenced
- [ ] PDF generates correctly with proper formatting
- [ ] Links work in both web and PDF versions
- [ ] Spelling and grammar checked (Swiss English)
- [ ] Brand voice consistency maintained

### **PDF-Specific Checks**
- [ ] Page breaks occur in logical places
- [ ] Images are properly sized (not too large/small)
- [ ] Headers and footers display correctly
- [ ] Table of contents works (if included)
- [ ] All text is readable and well-formatted
- [ ] File size is reasonable (under 2MB)

## 🔗 **Related Documentation**

- [Thepia Writing Guidelines](https://github.com/thepian/thepia.com/blob/main/docs/content/writing-guidelines.md)
- [Content Templates](https://github.com/thepian/thepia.com/blob/main/docs/content/content-templates.md)
- [PDF Best Practices](https://github.com/thepian/buckia/blob/main/docs/pdf-best-practices.md)
- [Buckia PDF Configuration](https://github.com/thepian/buckia/blob/main/docs/configuration/pdf.md)

## 📞 **Support**

For questions about:
- **Content and writing**: Reference [Writing Guidelines](https://github.com/thepian/thepia.com/blob/main/docs/content/writing-guidelines.md)
- **PDF generation issues**: See [PDF Best Practices](https://github.com/thepian/buckia/blob/main/docs/pdf-best-practices.md)
- **Template customization**: Check [Buckia Documentation](https://github.com/thepian/buckia/blob/main/docs/)

---

**Last Updated**: June 14, 2024  
**Version**: 1.0.0  
**Maintained by**: Thepia Development Team
