import { useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Breadcrumbs,
  Link as MuiLink,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Folder as FolderIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Settings as SettingsIcon,
  CloudUpload as CloudUploadIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

interface MenuItem {
  text: string;
  icon: JSX.Element;
  path: string;
}

const menuItems: MenuItem[] = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Projects & Services', icon: <FolderIcon />, path: '/projects' },
  { text: 'Data Imports', icon: <CloudUploadIcon />, path: '/data-imports' },
  { text: 'Reviews (redirect)', icon: <CheckCircleIcon />, path: '/reviews' },
  { text: 'Tasks', icon: <AssignmentIcon />, path: '/tasks' },
];

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const breadcrumbs = (() => {
    const segments = location.pathname.split('/').filter(Boolean);
    if (!segments.length) return [];

    const labelMap: Record<string, string> = {
      projects: 'Projects',
      'data-imports': 'Data Imports',
      tasks: 'Tasks',
      reviews: 'Reviews',
    };

    const items: { label: string; path: string }[] = [];
    let cumulative = '';
    segments.forEach((segment, idx) => {
      cumulative += `/${segment}`;
      const label =
        labelMap[segment] ||
        (idx === 1 && segments[0] === 'projects' ? `Project ${segment}` : segment);
      items.push({ label, path: cumulative });
    });

    return items;
  })();

  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = search.trim();
    navigate(trimmed ? `/projects?search=${encodeURIComponent(trimmed)}` : '/projects');
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 600 }}>
          BIM Manager
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/settings')}>
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1, flexWrap: 'wrap' }}>
            <Box>
              <Typography variant="h6" noWrap component="div">
                BIM Project Management System
              </Typography>
              {breadcrumbs.length > 0 && (
                <Breadcrumbs aria-label="breadcrumb" sx={{ color: 'common.white', mt: 0.25 }}>
                  <MuiLink
                    underline="hover"
                    color="inherit"
                    onClick={() => navigate('/')}
                    sx={{ cursor: 'pointer' }}
                  >
                    Dashboard
                  </MuiLink>
                  {breadcrumbs.map((crumb, idx) =>
                    idx === breadcrumbs.length - 1 ? (
                      <Typography key={crumb.path} color="inherit">
                        {crumb.label}
                      </Typography>
                    ) : (
                      <MuiLink
                        key={crumb.path}
                        underline="hover"
                        color="inherit"
                        onClick={() => navigate(crumb.path)}
                        sx={{ cursor: 'pointer' }}
                      >
                        {crumb.label}
                      </MuiLink>
                    ),
                  )}
                </Breadcrumbs>
              )}
            </Box>
            <Box sx={{ flexGrow: 1 }} />
            <Box component="form" onSubmit={submitSearch} sx={{ minWidth: { xs: '100%', sm: 280 }, maxWidth: 400 }}>
              <TextField
                size="small"
                variant="outlined"
                fullWidth
                placeholder="Global search (projects, services)"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar /> {/* Spacer for fixed AppBar */}
        {children}
      </Box>
    </Box>
  );
}
