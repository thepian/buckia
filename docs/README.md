# Thepia Documentation

This directory contains comprehensive documentation for all Thepia products and development practices.

## 📖 **Documentation Standards**

- **[Documentation Standards](documentation-standards.html)** - Interactive guide to writing world-class documentation for all Thepia products

## 🏗️ **Architecture & Decisions**

- [Architecture Decision Record](../memory-bank/draft-architecture.md) - System architecture decisions
- [Design System Decision Record](../memory-bank/design-system-decision-record.md) - Design system choices
- [ADR 0003: Default Test Execution Mode](adr/0003-default-test-execution-mode.md) - Testing approach decisions

## 🔐 **Authentication**

- [Authentication Documentation](auth/) - Complete passwordless authentication system with WebAuthn/passkeys and Auth0

## 📝 **Content Management**

- [Content Management System](content/) - Comprehensive content organization, writing guidelines, and i18n strategy
- [UX Principles](ux-principles.md) - User experience guidelines

## 🧪 **Testing & QA**

- [Test Page Guide](testing/test-page-guide.md) - Production-safe QA interface at `/test` for validation and troubleshooting

## 📄 **PDF Generation**

- [PDF Best Practices](pdf-best-practices.md) - Professional PDF styling for whitepapers and insights documents

## 🚀 **Development & Deployment**

- [Network Development Setup](network-development-setup.md) - Port 443 and mDNS setup for network-wide development access
- [Development Permission Issues](development-permission-issues.md) - Troubleshooting guide for port 443 permission problems
- [Deployment Guide](deployment.md) - Complete deployment instructions from scratch to production

## 🤖 **For AI Assistants**

When working on Thepia projects, always reference:

1. **[Documentation Standards](documentation-standards.html)** - Follow these guidelines for all documentation
2. **Project Context** - Check the main README.md for project-specific setup
3. **Architecture Decisions** - Review ADRs before making structural changes
4. **Testing Requirements** - Follow established testing patterns

### Quick Reference for AI

```markdown
📖 **Documentation**: Follow [Thepia Documentation Standards](documentation-standards.html)
🏗️ **Architecture**: Check [ADRs](adr/) before structural changes  
🧪 **Testing**: Use established patterns in [testing/](testing/)
🔐 **Auth**: Reference [auth documentation](auth/) for authentication flows
```

## 📁 **Directory Structure**

```
docs/
├── README.md                           # This file
├── documentation-standards.html        # Documentation guidelines (interactive)
├── adr/                               # Architecture Decision Records
├── auth/                              # Authentication documentation
├── content/                           # Content management guidelines
├── testing/                           # Testing guides and patterns
├── ux-principles.md                   # UX guidelines
├── network-development-setup.md       # Development setup
├── development-permission-issues.md   # Troubleshooting
└── deployment.md                      # Deployment guide
```

---

**Note**: The [Documentation Standards](documentation-standards.html) apply to **all Thepia repositories** and should be referenced when creating or updating documentation across the entire Thepia ecosystem.
