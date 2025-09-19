// API service for communicating with the Flask backend
const API_BASE_URL = '/api';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Project Management
  async getProjects() {
    return this.request('/projects');
  }

  async getProjectsFullData() {
    return this.request('/projects_full');
  }

  async createProject(projectData) {
    return this.request('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  }

  async updateProject(projectId, projectData) {
    return this.request(`/projects/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify(projectData),
    });
  }

  async getProjectDetails(projectId) {
    return this.request(`/project_details/${projectId}`);
  }

  async updateProjectDetails(projectId, details) {
    return this.request(`/project_details/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify(details),
    });
  }

  // User Management
  async getUsers() {
    return this.request('/users');
  }

  // Review Management
  async getReviewTasks(projectId, cycleId) {
    return this.request(`/review_tasks?project_id=${projectId}&cycle_id=${cycleId}`);
  }

  async updateReviewTask(scheduleId, data) {
    return this.request(`/review_task/${scheduleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getReviewSummary(projectId, cycleId) {
    return this.request(`/review_summary/${projectId}/${cycleId}`);
  }

  async getReviewCycles(projectId) {
    return this.request(`/review_cycles/${projectId}`);
  }

  async createReviewCycle(projectId, cycleData) {
    return this.request(`/review_cycles/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(cycleData),
    });
  }

  async updateReviewCycle(projectId, cycleId, cycleData) {
    return this.request(`/review_cycles/${projectId}/${cycleId}`, {
      method: 'PATCH',
      body: JSON.stringify(cycleData),
    });
  }

  async deleteReviewCycle(projectId, cycleId) {
    return this.request(`/review_cycles/${projectId}/${cycleId}`, {
      method: 'DELETE',
    });
  }

  // Service Management
  async getProjectServices(projectId) {
    return this.request(`/project_services/${projectId}`);
  }

  async generateReviewsFromServices(projectId, reviewData) {
    return this.request(`/generate_reviews_from_services/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  // Document Management
  async getBEPMatrix(projectId) {
    return this.request(`/bep_matrix/${projectId}`);
  }

  async updateBEPSection(projectId, sectionData) {
    return this.request(`/bep_matrix/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(sectionData),
    });
  }

  async updateBEPStatus(projectId, status) {
    return this.request(`/bep_status/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // Reference Data
  async getReferenceData(table) {
    return this.request(`/reference/${table}`);
  }

  // File Management
  async uploadFile(formData) {
    return fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData, // FormData object, don't set Content-Type header
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    });
  }

  // Project Bookmarks
  async getProjectBookmarks(projectId) {
    return this.request(`/project_bookmarks/${projectId}`);
  }

  async createBookmark(projectId, bookmarkData) {
    return this.request(`/project_bookmarks/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(bookmarkData),
    });
  }

  async updateBookmark(bookmarkId, bookmarkData) {
    return this.request(`/bookmark/${bookmarkId}`, {
      method: 'PATCH',
      body: JSON.stringify(bookmarkData),
    });
  }

  async deleteBookmark(bookmarkId) {
    return this.request(`/bookmark/${bookmarkId}`, {
      method: 'DELETE',
    });
  }

  // Task Management
  async getTasks(projectId) {
    return this.request(`/tasks?project_id=${projectId}`);
  }

  async createTask(taskData) {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  async updateTask(taskId, taskData) {
    return this.request(`/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(taskData),
    });
  }

  async deleteTask(taskId) {
    return this.request(`/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async getTaskDependencies(taskId) {
    return this.request(`/task_dependencies/${taskId}`);
  }

  async getResources() {
    return this.request('/resources');
  }
}

export const apiService = new ApiService();