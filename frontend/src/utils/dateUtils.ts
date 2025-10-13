/**
 * Date utility functions
 * Safe date formatting with null/undefined checks
 */

import { format as dateFnsFormat } from 'date-fns';

/**
 * Safely format a date with fallback for invalid dates
 * @param date - Date string, Date object, or null/undefined
 * @param formatString - date-fns format string (default: 'MMM d, yyyy')
 * @param fallback - Fallback text for invalid dates (default: 'N/A')
 * @returns Formatted date string or fallback
 */
export const formatDate = (
  date: string | Date | null | undefined,
  formatString: string = 'MMM d, yyyy',
  fallback: string = 'N/A'
): string => {
  if (!date) {
    return fallback;
  }

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    // Check if date is valid
    if (isNaN(dateObj.getTime())) {
      return fallback;
    }
    
    return dateFnsFormat(dateObj, formatString);
  } catch (error) {
    console.error('Error formatting date:', error, 'Date value:', date);
    return fallback;
  }
};

/**
 * Safely format a datetime with fallback
 * @param date - Date string, Date object, or null/undefined
 * @param fallback - Fallback text for invalid dates (default: 'N/A')
 * @returns Formatted datetime string or fallback
 */
export const formatDateTime = (
  date: string | Date | null | undefined,
  fallback: string = 'N/A'
): string => {
  return formatDate(date, 'MMM d, yyyy HH:mm', fallback);
};

/**
 * Check if a date value is valid
 * @param date - Date string, Date object, or null/undefined
 * @returns true if date is valid, false otherwise
 */
export const isValidDate = (date: string | Date | null | undefined): boolean => {
  if (!date) {
    return false;
  }

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return !isNaN(dateObj.getTime());
  } catch {
    return false;
  }
};
