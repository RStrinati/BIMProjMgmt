# 🚀 START HERE - BIM Project Management System

Welcome! This document is your entry point to the BIM Project Management System codebase.

---

## 📍 Quick Navigation

### For New Developers
👉 **[README.md](./README.md)** — Project overview, architecture, and core concepts (start here!)

### For AI/Code Agents  
👉 **[AGENTS.md](./AGENTS.md)** — Critical architectural rules, core model, and development guidelines (REQUIRED READING)

### For Detailed Documentation
👉 **[docs/DOCUMENTATION_INDEX.md](./docs/DOCUMENTATION_INDEX.md)** — Complete documentation guide organized by category

---

## 🎯 What is This System?

**BIM Project Management System** is an enterprise-grade construction project lifecycle management application built with:
- **Frontend**: React 18 + TypeScript + Material-UI + Vite
- **Backend**: Flask API (Python) + SQL Server database
- **Core Features**: Project management, review cycles, billing, analytics, data integrations

---

## 📚 Documentation by Role

### 👨‍💻 Backend Developer
1. Read: [README.md](./README.md) → Architecture section
2. Read: [docs/core/DATABASE_CONNECTION_GUIDE.md](./docs/core/DATABASE_CONNECTION_GUIDE.md)
3. Read: [docs/core/DEVELOPER_ONBOARDING.md](./docs/core/DEVELOPER_ONBOARDING.md)
4. Browse: [docs/features/](./docs/features/) for your feature area

### 🎨 Frontend Developer
1. Read: [README.md](./README.md) → Architecture section
2. Read: [docs/features/REACT_INTEGRATION_ROADMAP.md](./docs/features/REACT_INTEGRATION_ROADMAP.md)
3. Read: [docs/features/README.md](./docs/features/README.md) for feature guides
4. Browse: [docs/reference/](./docs/reference/) for component patterns

### 🗄️ Database Administrator
1. Read: [docs/core/database_schema.md](./docs/core/database_schema.md)
2. Read: [docs/migration/README.md](./docs/migration/README.md)
3. Browse: [sql/](./sql/) directory for schema files

### 🐛 Troubleshooter
👉 **[docs/troubleshooting/README.md](./docs/troubleshooting/README.md)** — Error solutions and debugging guides

### 📊 Analytics / Data Warehouse
👉 **[docs/features/WAREHOUSE_IMPLEMENTATION_GUIDE.md](./docs/features/WAREHOUSE_IMPLEMENTATION_GUIDE.md)**

---

## 🏗️ Core Conceptual Model (CRITICAL ⚠️)

This system uses **Option A core model**. Understanding this is non-negotiable:

```
Project
├─ Services (project offerings/scopes)
│  ├─ Reviews (recurring cycles/meetings)
│  └─ Items (service deliverables)
└─ Tasks (project execution units - independent)
```

**Key Rule**: Items ≠ Tasks
- **Items**: Service-owned deliverables (e.g., "Weekly progress report")
- **Tasks**: Project-owned execution (e.g., "Coordinate HVAC ductwork")

👉 **For full details**: See [AGENTS.md](./AGENTS.md) → "Core Model (Option A)"

---

## 🚀 Getting Started

### Step 1: Security Setup (REQUIRED)

⚠️ **CRITICAL:** This must be done FIRST before any development work.

1. **Copy environment templates:**
   ```bash
   cp .env.example .env
   cp tools/.env.example tools/.env
   ```

2. **Edit `.env` and `tools/.env` with your actual database credentials**
   - Use a text editor to open both files
   - Replace `your_username_here` with your actual database username
   - Replace `your_secure_password_here` with your actual password
   - Update `your_server_here` with your database server address

3. **Verify files are ignored by Git:**
   ```bash
   git check-ignore .env tools/.env
   ```
   Both should be returned by the command (meaning they're properly ignored)

⚠️ **IMPORTANT:** Never commit `.env` files! They contain sensitive credentials.

See the [Security Setup section in README.md](./README.md#-security-setup) for more details.

### Step 2: Set Up Environment
```bash
# Create virtual environment (Python 3.12+)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Start Backend (Flask API)
```bash
cd backend
python app.py
# Runs on http://localhost:5000
```

### Step 4: Start Frontend (React)
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### Step 5: Read the Core Docs
- [README.md](./README.md) — Full project documentation
- [AGENTS.md](./AGENTS.md) — Development guidelines
- [docs/core/DEVELOPER_ONBOARDING.md](./docs/core/DEVELOPER_ONBOARDING.md) — Setup guide

---

## 📖 Documentation Structure

```
docs/
├─ core/                  Essential development docs
│  ├─ README.md
│  ├─ DEVELOPER_ONBOARDING.md
│  ├─ DATABASE_CONNECTION_GUIDE.md
│  └─ database_schema.md
│
├─ features/             Feature implementation guides
│  ├─ README.md
│  ├─ REACT_INTEGRATION_ROADMAP.md
│  ├─ WAREHOUSE_IMPLEMENTATION_GUIDE.md
│  └─ [30+ feature docs]
│
├─ integrations/         External system integration
│  ├─ README.md
│  └─ [ACC, Revizto, APS integration guides]
│
├─ migration/            Database migration guides
│  ├─ README.md
│  └─ [Schema evolution docs]
│
├─ troubleshooting/      Error solutions & debugging
│  ├─ README.md
│  └─ [Common issues & fixes]
│
├─ reference/            Quick references & APIs
│  ├─ README.md
│  └─ [API docs, checklists, etc.]
│
└─ archive/              Historical work (read-only)
   ├─ phases/           Phase completion reports
   ├─ services-linear-refactor/  Deployment session records
   └─ [Other historical projects]
```

**👉 Full index**: [docs/DOCUMENTATION_INDEX.md](./docs/DOCUMENTATION_INDEX.md)

---

## 🔗 Key Links

### System Architecture
- [README.md § Architecture](./README.md#-architecture) — Tech stack & design
- [README.md § Core Conceptual Model](./README.md#-core-conceptual-model-authoritative---option-a) — Data model
- [docs/core/database_schema.md](./docs/core/database_schema.md) — Database tables & relationships

### Development Guides
- [docs/core/DEVELOPER_ONBOARDING.md](./docs/core/DEVELOPER_ONBOARDING.md) — Setup & first steps
- [docs/core/DATABASE_CONNECTION_GUIDE.md](./docs/core/DATABASE_CONNECTION_GUIDE.md) — DB access patterns
- [AGENTS.md](./AGENTS.md) — Code rules & patterns (AI agents)

### Feature Implementations
- [docs/features/README.md](./docs/features/README.md) — Feature overview
- [docs/features/REACT_INTEGRATION_ROADMAP.md](./docs/features/REACT_INTEGRATION_ROADMAP.md) — Frontend roadmap
- [docs/features/WAREHOUSE_IMPLEMENTATION_GUIDE.md](./docs/features/WAREHOUSE_IMPLEMENTATION_GUIDE.md) — Analytics setup

### External Integrations
- [docs/integrations/README.md](./docs/integrations/README.md) — Integration overview
- Integration guides for ACC, Revizto, APS, Revit, IFC

### Troubleshooting
- [docs/troubleshooting/README.md](./docs/troubleshooting/README.md) — Common issues & solutions

---

## ❓ Common Questions

**Q: Where is the project roadmap?**  
A: See [docs/core/ROADMAP.md](./docs/core/ROADMAP.md)

**Q: How do I set up the database?**  
A: See [docs/core/DATABASE_CONNECTION_GUIDE.md](./docs/core/DATABASE_CONNECTION_GUIDE.md) and [docs/migration/README.md](./docs/migration/README.md)

**Q: What are the data model rules I must follow?**  
A: See [AGENTS.md](./AGENTS.md) → "Core Model (Option A) - CRITICAL ARCHITECTURAL RULES"

**Q: How do I add a new feature?**  
A: See [docs/features/README.md](./docs/features/README.md) → implementation checklist

**Q: Where are the API docs?**  
A: See [docs/reference/](./docs/reference/) (look for API references)

**Q: I broke something. How do I fix it?**  
A: See [docs/troubleshooting/README.md](./docs/troubleshooting/README.md)

---

## 🎓 Learning Path

**New to the system?** Follow this order:

1. ⏱️ **5 minutes**: Read this file (START_HERE.md)
2. ⏱️ **15 minutes**: Read [README.md](./README.md)
3. ⏱️ **10 minutes**: Read [AGENTS.md](./AGENTS.md) → Core Model
4. ⏱️ **30 minutes**: Read [docs/core/DEVELOPER_ONBOARDING.md](./docs/core/DEVELOPER_ONBOARDING.md)
5. ⏱️ **As needed**: Browse category READMEs for your area

**Total: ~1 hour** to be productive

---

## 🆘 Need Help?

### Documentation Issues
- See [docs/troubleshooting/README.md](./docs/troubleshooting/README.md) for common problems
- Check [docs/DOCUMENTATION_INDEX.md](./docs/DOCUMENTATION_INDEX.md) for complete topic list

### Development Issues
- Check [docs/core/DATABASE_CONNECTION_GUIDE.md](./docs/core/DATABASE_CONNECTION_GUIDE.md) for DB errors
- Check [docs/features/REACT_INTEGRATION_ROADMAP.md](./docs/features/REACT_INTEGRATION_ROADMAP.md) for frontend issues
- Review [AGENTS.md](./AGENTS.md) for code pattern rules

### Missing Information
- Try [docs/DOCUMENTATION_INDEX.md](./docs/DOCUMENTATION_INDEX.md) search by keyword
- Check archive/ for historical context on completed features

---

## 🚀 Next Steps

**Ready to start?**

- **New to project**: → [docs/core/DEVELOPER_ONBOARDING.md](./docs/core/DEVELOPER_ONBOARDING.md)
- **Have code to write**: → [AGENTS.md](./AGENTS.md) (rules) + relevant feature doc
- **Setting up environment**: → [docs/core/DATABASE_CONNECTION_GUIDE.md](./docs/core/DATABASE_CONNECTION_GUIDE.md)
- **Want full overview**: → [README.md](./README.md)
- **Exploring features**: → [docs/features/README.md](./docs/features/README.md)

---

**Last Updated**: January 16, 2026  
**Status**: Active  
**Maintained By**: Development Team
