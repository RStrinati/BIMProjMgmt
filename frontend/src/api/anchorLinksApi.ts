/**
 * API client for IssueAnchorLinks endpoints
 */

import axios from 'axios';

const API_BASE = '/api';

export interface AnchorLinkedIssue {
  link_id: number;
  issue_key: string;
  display_id: string;
  title: string;
  status_normalized: string;
  priority_normalized: string;
  discipline_normalized: string;
  assignee_user_key: string | null;
  issue_updated_at: string | null;
  link_role: string;
  note: string | null;
  link_created_at: string | null;
  link_created_by: string | null;
  source_system: string;
}

export interface AnchorLinkedIssuesResponse {
  page: number;
  page_size: number;
  total_count: number;
  issues: AnchorLinkedIssue[];
  error?: string;
}

export interface AnchorBlockerCounts {
  total_linked: number;
  open_count: number;
  closed_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
}

export interface LinkedAnchor {
  link_id: number;
  anchor_type: string;
  service_id: number | null;
  review_id: number | null;
  item_id: number | null;
  link_role: string;
  note: string | null;
  created_at: string | null;
  created_by: string | null;
}

export interface LinkedAnchorsResponse {
  anchors: LinkedAnchor[];
  error?: string;
}

export interface CreateIssueLinkPayload {
  project_id: number;
  issue_key_hash: string; // hex-encoded
  anchor_type: 'review' | 'service' | 'item';
  anchor_id: number;
  link_role?: 'blocks' | 'evidence' | 'relates';
  note?: string;
  created_by?: string;
}

export interface CreateIssueLinkResponse {
  link_id?: number;
  anchor_type?: string;
  anchor_id?: number;
  link_role?: string;
  error?: string;
}

/**
 * Get issues linked to an anchor
 */
export async function getAnchorLinkedIssues(
  projectId: number,
  anchorType: 'review' | 'service' | 'item',
  anchorId: number,
  page?: number,
  pageSize?: number,
  sortBy?: string,
  sortDir?: string,
  linkRole?: string,
): Promise<AnchorLinkedIssuesResponse> {
  try {
    const response = await axios.get<AnchorLinkedIssuesResponse>(
      `${API_BASE}/projects/${projectId}/anchors/${anchorType}/${anchorId}/issues`,
      {
        params: {
          page: page || 1,
          page_size: pageSize || 20,
          sort_by: sortBy || 'updated_at',
          sort_dir: sortDir || 'DESC',
          ...(linkRole && { link_role: linkRole }),
        },
      }
    );
    return response.data;
  } catch (error: any) {
    // Handle 400/404 gracefully - return empty issues list instead of throwing
    if (error.response?.status === 400 || error.response?.status === 404) {
      if (process.env.NODE_ENV === 'development') {
        console.debug(
          `Anchor linked issues unavailable (${error.response?.status}) for ${anchorType}:${anchorId}`,
          'Returning empty issues list.'
        );
      }
      return {
        page: 1,
        page_size: pageSize || 20,
        total_count: 0,
        issues: [],
      };
    }
    // For other errors, log and re-throw
    console.error('Error fetching anchor linked issues:', error);
    throw error;
  }
}

/**
 * Get blocker counts for an anchor
 */
export async function getAnchorBlockerCounts(
  projectId: number,
  anchorType: 'review' | 'service' | 'item',
  anchorId: number,
): Promise<AnchorBlockerCounts> {
  try {
    const response = await axios.get<AnchorBlockerCounts>(
      `${API_BASE}/projects/${projectId}/anchors/${anchorType}/${anchorId}/counts`
    );
    return response.data;
  } catch (error: any) {
    // Handle 400/404 gracefully - return empty counts instead of throwing
    if (error.response?.status === 400 || error.response?.status === 404) {
      if (process.env.NODE_ENV === 'development') {
        console.debug(
          `Anchor blocker counts unavailable (${error.response?.status}) for ${anchorType}:${anchorId}`,
          'Returning empty counts.'
        );
      }
      return {
        total_linked: 0,
        open_count: 0,
        closed_count: 0,
        critical_count: 0,
        high_count: 0,
        medium_count: 0,
      };
    }
    // For other errors, log and re-throw
    console.error('Error fetching anchor blocker counts:', error);
    throw error;
  }
}

/**
 * Create a new issue-anchor link
 */
export async function createIssueLink(
  payload: CreateIssueLinkPayload,
): Promise<CreateIssueLinkResponse> {
  try {
    const response = await axios.post<CreateIssueLinkResponse>(
      `${API_BASE}/issue-links`,
      payload
    );
    return response.data;
  } catch (error) {
    console.error('Error creating issue link:', error);
    throw error;
  }
}

/**
 * Delete (soft-delete) an issue-anchor link
 */
export async function deleteIssueLink(linkId: number): Promise<{ success?: boolean; error?: string }> {
  try {
    const response = await axios.delete<{ success?: boolean; error?: string }>(
      `${API_BASE}/issue-links/${linkId}`
    );
    return response.data;
  } catch (error) {
    console.error('Error deleting issue link:', error);
    throw error;
  }
}

/**
 * Get all anchors linked to a specific issue
 */
export async function getIssueLinkedAnchors(
  projectId: number,
  issueKeyHash: string, // hex-encoded
): Promise<LinkedAnchorsResponse> {
  try {
    const response = await axios.get<LinkedAnchorsResponse>(
      `${API_BASE}/issues/${issueKeyHash}/links`,
      {
        params: { project_id: projectId },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching issue linked anchors:', error);
    throw error;
  }
}

// Export as a namespace
export const anchorLinksApi = {
  getAnchorLinkedIssues,
  getAnchorBlockerCounts,
  createIssueLink,
  deleteIssueLink,
  getIssueLinkedAnchors,
};
