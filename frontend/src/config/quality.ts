/**
 * Quality Register Configuration Constants
 *
 * Freshness and tolerance settings for the Quality Register tab.
 */

export const QUALITY_REGISTER_CONFIG = {
  /**
   * Number of days before next review to show "DUE_SOON" status
   */
  DUE_SOON_WINDOW_DAYS: 7,

  /**
   * Number of days after last version date before showing "OUT_OF_DATE"
   * (typically 0 to mark as out of date if before next review date)
   */
  TOLERANCE_DAYS: 0,

  /**
   * Maximum page size for quality register queries
   */
  MAX_PAGE_SIZE: 500,

  /**
   * Default page size
   */
  DEFAULT_PAGE_SIZE: 50,
} as const;
