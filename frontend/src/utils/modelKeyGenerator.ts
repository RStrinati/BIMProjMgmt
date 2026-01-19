/**
 * Generate unique model key for ExpectedModels table.
 * Enforces NVARCHAR(50) constraint and prevents collisions.
 */
export const generateModelKey = (abv?: string): string => {
  const prefix = (abv || 'MODEL').slice(0, 10).toUpperCase();
  const timestamp = Date.now().toString(36); // Base36: shorter than decimal
  const random = Math.random().toString(36).slice(2, 6).toUpperCase();
  const key = `${prefix}-${timestamp}-${random}`;
  
  // Enforce NVARCHAR(50) constraint
  if (key.length > 50) {
    return key.slice(0, 50);
  }
  return key;
};

// Example outputs:
// "ARCH-l8k9m3n4-A3F9"  (when abv="ARCH")
// "MODEL-l8k9m3n4-B2K7"  (when abv is empty)
