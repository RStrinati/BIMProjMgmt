import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import {
  Dashboard,
  Assignment,
  People,
  FolderOpen,
  Description,
  BookmarkBorder,
  Settings,
} from '@mui/icons-material';

import { ProjectProvider } from './context/ProjectContext';
import ProjectSetup from './components/ProjectSetup/ProjectSetup';
import TaskManagement from './components/TaskManagement/TaskManagement';
import ResourceManagement from './components/ResourceManagement/ResourceManagement';
import ReviewManagement from './components/ReviewManagement/ReviewManagement';
import DocumentManagement from './components/DocumentManagement/DocumentManagement';
import ACCIntegration from './components/ACCIntegration/ACCIntegration';
import ProjectBookmarks from './components/ProjectBookmarks/ProjectBookmarks';
import DashboardComponent from './components/Dashboard/Dashboard';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    h6: {
      fontWeight: 600,
    },
  },
});

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/' },
  { text: 'Project Setup', icon: <Settings />, path: '/projects' },
  { text: 'Task Management', icon: <Assignment />, path: '/tasks' },
  { text: 'Resource Management', icon: <People />, path: '/resources' },
  { text: 'Review Management', icon: <Assignment />, path: '/reviews' },
  { text: 'Document Management', icon: <Description />, path: '/documents' },
  { text: 'ACC Integration', icon: <FolderOpen />, path: '/acc' },
  { text: 'Project Bookmarks', icon: <BookmarkBorder />, path: '/bookmarks' },
];

function App() {
  return (
    <ThemeProvider theme={theme}>
      <ProjectProvider>
        <Router>
          <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <AppBar
              position="fixed"
              sx={{
                width: `calc(100% - ${drawerWidth}px)`,
                ml: `${drawerWidth}px`,
              }}
            >
              <Toolbar>
                <Typography variant="h6" noWrap component="div">
                  BIM Project Management System
                </Typography>
              </Toolbar>
            </AppBar>
            <Drawer
              sx={{
                width: drawerWidth,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                  width: drawerWidth,
                  boxSizing: 'border-box',
                },
              }}
              variant="permanent"
              anchor="left"
            >
              <Toolbar />
              <Box sx={{ overflow: 'auto' }}>
                <List>
                  {menuItems.map((item) => (
                    <ListItem
                      button
                      key={item.text}
                      component={Link}
                      to={item.path}
                    >
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.text} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </Drawer>
            <Box
              component="main"
              sx={{
                flexGrow: 1,
                bgcolor: 'background.default',
                p: 3,
              }}
            >
              <Toolbar />
              <Routes>
                <Route path="/" element={<DashboardComponent />} />
                <Route path="/projects" element={<ProjectSetup />} />
                <Route path="/tasks" element={<TaskManagement />} />
                <Route path="/resources" element={<ResourceManagement />} />
                <Route path="/reviews" element={<ReviewManagement />} />
                <Route path="/documents" element={<DocumentManagement />} />
                <Route path="/acc" element={<ACCIntegration />} />
                <Route path="/bookmarks" element={<ProjectBookmarks />} />
              </Routes>
            </Box>
          </Box>
        </Router>
      </ProjectProvider>
    </ThemeProvider>
  );
}

export default App;