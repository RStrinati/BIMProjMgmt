# Decision Matrix: Tkinter vs React Front End

| Dimension | Tkinter (Current) | React + TypeScript (Proposed) |
|---|---|---|
| UI density / components | Limited; manual layout; no data grid | Rich components (DataGrid, Kanban, Timeline) via MUI/Ant |
| Real-time collab | Hard; custom threads/sockets | Native patterns via WebSockets/SignalR/Firebase |
| Access (external users) | Local app; distribution friction | Browser-based; SSO; easy client access |
| ACC/BIM viewer | Embed tricky | Easy embeds (Forge, Trimble) |
| Dev velocity / UX experiments | Slower; static | Fast; A/B tests; design systems |
| Testing | Manual UI tests | Jest/RTL/Cypress pipelines |
| Offline | Strong | Possible with PWA; optional |

Recommendation: Keep Python backend/services. Start a 2–3 week spike focused on the Reviews module. Ship a thin vertical slice:
- Planning grid with cycle generation
- Tracking grid with folder attach
- Services scope list
- Kanban board

If successful, migrate additional tabs incrementally.
