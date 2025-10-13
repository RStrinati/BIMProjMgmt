# BIM Project Management - React Frontend

Modern React frontend for the BIM Project Management System, built with Vite, TypeScript, and Material-UI.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+ (for backend)
- SQL Server database configured

### Installation

1. **Install frontend dependencies:**
```bash
cd frontend
npm install
```

2. **Start the development servers:**

**Terminal 1 - Backend (Flask):**
```bash
# From project root
python backend/app.py
```

**Terminal 2 - Frontend (React):**
```bash
# From frontend directory
cd frontend
npm run dev
```

3. **Open your browser:**
```
http://localhost:5173
```

The frontend will automatically proxy API requests to the Flask backend at `http://localhost:5000`.

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   │   ├── client.ts     # Axios instance
│   │   ├── projects.ts   # Projects API
│   │   ├── reviews.ts    # Reviews API
│   │   └── tasks.ts      # Tasks API
│   ├── components/       # Reusable React components
│   │   └── layout/       # Layout components
│   │       └── MainLayout.tsx
│   ├── pages/            # Page components
│   │   ├── DashboardPage.tsx
│   │   └── ProjectsPage.tsx
│   ├── theme/            # Material-UI theme
│   │   └── theme.ts
│   ├── types/            # TypeScript type definitions
│   │   └── api.ts
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🛠️ Technology Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Material-UI (MUI)** - Component library
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Axios** - HTTP client

## 📝 Available Scripts

- `npm run dev` - Start development server (http://localhost:5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🔗 API Integration

The frontend connects to the Flask backend via a proxy configured in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:5000'
  }
}
```

All API calls are made through the centralized API client in `src/api/`.

## 🎨 Theme Customization

The Material-UI theme is configured in `src/theme/theme.ts`. You can customize:
- Colors (primary, secondary, etc.)
- Typography
- Component styles
- Spacing and borders

## 📦 Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## 🐛 Troubleshooting

**Frontend won't start:**
- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

**API errors:**
- Ensure Flask backend is running on port 5000
- Check CORS is enabled in `backend/app.py`
- Verify database connection

**Build errors:**
- Clear cache: `npm run build -- --force`
- Check TypeScript errors: `npm run lint`

## 🔜 Next Steps

### Pages to Build:
- ✅ Dashboard (basic stats)
- ✅ Projects (grid view with search)
- ⏳ Reviews Management
- ⏳ Tasks Management  
- ⏳ Analytics Dashboard
- ⏳ Settings

### Features to Add:
- Project detail view
- Create/Edit project forms
- Review scheduling UI
- Task management
- File uploads
- Real-time updates

## 📚 Documentation

- [React Documentation](https://react.dev/)
- [Material-UI](https://mui.com/)
- [React Query](https://tanstack.com/query/latest)
- [Vite](https://vitejs.dev/)

## 🆚 Comparison with Tkinter UI

This modern React frontend replaces the Tkinter desktop interface with:
- ✅ Modern, responsive design
- ✅ Better UX and visual hierarchy
- ✅ Faster navigation
- ✅ Real-time data updates
- ✅ Mobile-responsive (bonus!)
- ✅ Easier to maintain and extend

**Note:** The Tkinter UI (`run_enhanced_ui.py`) is still available as a backup.
