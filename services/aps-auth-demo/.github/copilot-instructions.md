# Copilot Instructions for APS OAuth Demo

## Project Overview
This is a Node.js Express app demonstrating Autodesk Platform Services (APS) OAuth authentication and basic API usage. The app provides endpoints for authenticating users, retrieving their Autodesk profile, and listing ACC projects.

## Architecture & Data Flow
- **Single-file app:** All logic is in `index.js`.
- **OAuth Flow:**
  1. `/login` – Redirects user to Autodesk OAuth login.
  2. `/callback` – Handles OAuth callback, exchanges code for access token.
  3. `/me` – Uses access token to fetch user profile.
  4. `/projects` – Lists ACC projects for a hardcoded account ID.
- **State:** Access token is stored in a global variable (not persistent, resets on restart).

## Key Files
- `index.js`: Main application logic and all routes.
- `package.json`: Declares dependencies (`express`, `axios`, `open`).

## Developer Workflows
- **Run the app:**
  ```powershell
  node index.js
  ```
- **No tests or build steps** are defined. All code runs directly from `index.js`.
- **Debugging:** Use console logs already present in the code for tracing OAuth flow and API calls.

## Project-Specific Patterns
- **Hardcoded secrets:** Client ID, secret, and ACC account ID are hardcoded for demo purposes. Do NOT use in production.
- **No session management:** Access token is stored in-memory; multi-user support is not implemented.
- **Error handling:** API errors are logged and returned as plain text or JSON.
- **Endpoints:**
  - `/login` – Generates and displays the Autodesk OAuth URL.
  - `/callback` – Exchanges code for token.
  - `/me` – Fetches user profile.
  - `/projects` – Fetches ACC projects (requires valid token and account ID).

## Integration Points
- **Autodesk Platform Services:**
  - OAuth endpoints: `authentication/v1/authorize`, `authentication/v1/gettoken`
  - User profile: `userprofile/v1/users/@me`
  - ACC projects: `project/v1/accounts/{accountId}/projects`
- **External dependencies:**
  - `express` for HTTP server
  - `axios` for HTTP requests

## Example Usage
- Start the app, visit `/login`, authenticate, then use `/me` or `/projects`.
- Replace the hardcoded ACC account ID in `/projects` for real data.

## Conventions
- All routes are defined in a single file.
- Use async/await for API calls.
- Minimal error handling for demo clarity.

---
**For AI agents:**
- Focus on extending endpoints, improving security, or adding session/user management if requested.
- Reference `index.js` for all logic; no other source files exist.
- Do not introduce test/build steps unless explicitly requested.
- Document any new endpoints or patterns in this file.
