import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/apiService';

const ProjectContext = createContext();

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load initial data
  useEffect(() => {
    loadProjects();
    loadUsers();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const projectsData = await apiService.getProjects();
      setProjects(projectsData);
    } catch (err) {
      setError('Failed to load projects');
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const usersData = await apiService.getUsers();
      setUsers(usersData);
    } catch (err) {
      console.error('Error loading users:', err);
    }
  };

  const selectProject = (project) => {
    setCurrentProject(project);
    // Notify other components about project change
    window.dispatchEvent(new CustomEvent('projectChanged', { detail: project }));
  };

  const createProject = async (projectData) => {
    try {
      setLoading(true);
      await apiService.createProject(projectData);
      await loadProjects(); // Refresh project list
      setError(null);
      return true;
    } catch (err) {
      setError('Failed to create project');
      console.error('Error creating project:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const updateProject = async (projectId, projectData) => {
    try {
      setLoading(true);
      await apiService.updateProject(projectId, projectData);
      await loadProjects(); // Refresh project list
      setError(null);
      return true;
    } catch (err) {
      setError('Failed to update project');
      console.error('Error updating project:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    projects,
    currentProject,
    users,
    loading,
    error,
    selectProject,
    createProject,
    updateProject,
    loadProjects,
    loadUsers,
    setError,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};