# Claude Development Notes

## Project Philosophy

### **MANDATORY TESTING PROTOCOL**

**🚨 BEFORE claiming any fix is complete:**

1. **Test on MOBILE first** - Verify the fix works and nothing broke
2. **Test on DESKTOP second** - Verify the fix works and nothing broke
3. **ONLY THEN** report success to the user

**NEVER:**
- ❌ Assume mobile works if desktop is fixed
- ❌ Assume desktop works if mobile is fixed
- ❌ Tell the user something is "fixed" without actually testing both views
- ❌ Skip testing because "it should work"

**If you cannot test both views yourself, explicitly tell the user:**
*"Please test this on both mobile and desktop to confirm it works correctly."*

### Autonomous Problem Resolution

**When the user asks you to fix problems:**

1. ✅ **DO**: Identify and fix ALL problems autonomously
2. ✅ **DO**: Test your fixes thoroughly (mobile + desktop)
3. ✅ **DO**: Verify no new issues were introduced
4. ✅ **DO**: Report back ONLY when everything is working

**Never:**
- ❌ Report a problem and wait for user instructions
- ❌ Ask "What should I do about this issue?"
- ❌ Say "I found a problem" without fixing it first
- ❌ Report partial success with caveats

**Your response should be:** "Fixed [describe what you fixed]. Tested on mobile and desktop - everything works correctly."

**NOT:** "I fixed X but there's also Y that needs attention..."

### Mobile-First, Desktop-Enhanced Design

**⚠️ CRITICAL: Mobile is the PRIMARY use case**

- User primarily accesses this application on mobile devices
- Mobile experience MUST be fast, clean, and touch-friendly
- No clutter or unnecessary complexity on small screens
- Optimized for quick interactions and one-handed use
- **The mobile wireframe is the source of truth**

**Desktop Enhancements (Progressive Only)**

- Desktop users get richer, more detailed features automatically
- Utilize wider screen real estate with multi-column layouts
- Add desktop-specific interactions (hover states, keyboard shortcuts, context menus)
- Show more data density and detail when space allows
- **All enhancements applied ONLY via media queries**

**Non-Negotiables:**

1. ❌ Do NOT add desktop-only features that require mobile workarounds
2. ❌ Do NOT change mobile layouts to accommodate desktop patterns
3. ❌ Do NOT add complexity to mobile codebase for desktop convenience
4. ✅ All functionality MUST work fully on mobile; desktop just displays it differently
5. ✅ Test mobile FIRST - if something breaks, fix mobile before desktop

**Implementation Principles:**

1. Start with mobile styles as the base (no media queries)
2. Use `@media (min-width: ...)` to add desktop enhancements ONLY
3. Never compromise mobile performance for desktop features
4. Test mobile first, then verify desktop enhancements work
5. Keep mobile UI simple and fast - add complexity only on desktop via media queries

**Reference Files:**

- **Mobile Wireframe**: `power-app-wireframe.html` (canonical design - source of truth)
- **Desktop Wireframe**: `power-app-wireframe-desktop.html` (enhancement reference only)

**Desktop Enhancements from Wireframe:**

- Sidebar navigation (instead of bottom nav)
- Master-detail layout (list + detail panel side-by-side)
- Calendar + selected date list split view
- Entity grid (3 columns)
- Table format with hover actions for deadline lists
- Entity detail: sidebar with quick-copy IDs + 2-column content

**Current Examples:**

- **Calendar**: Mobile shows simple day numbers with count badges; Desktop shows deadline titles stacked in day cells (contained, no overflow)
- **Lists**: Mobile shows cards; Desktop can show data tables with sorting/filtering
- **Navigation**: Mobile has essential tabs; Desktop can add sidebar navigation
- **Data**: Mobile shows summary; Desktop shows full details inline

**Breakpoints:**

- `< 768px`: **Mobile (PRIMARY FOCUS)** - Base styles, no media queries
- `768px - 1023px`: **Tablet** - Transitional, lean toward mobile patterns
- `≥ 1024px`: **Desktop** - Apply enhancements from desktop wireframe

**Testing Priority:**

1. Mobile first, always
2. Desktop is a nice-to-have
3. If something breaks, fix mobile before addressing desktop layout issues

## Design System

### Color Palette

- Primary: `#6366f1` (Indigo)
- Success: `#22c55e` (Green)
- Warning: `#f59e0b` (Amber)
- Error: `#ef4444` (Red)
- Background: `#f5f5f5`
- Card: `#ffffff`

### Typography

- Font Family: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Mobile Base: 12-14px
- Desktop Base: 14-16px

### Status Colors

- Overdue: Red (`#ef4444`)
- Upcoming (This Week): Yellow (`#f59e0b`)
- Normal: Green (`#22c55e`)

### Entity State Colors

- Colorado (CO): Purple (`#8b5cf6`)
- Oregon (OR): Green (`#22c55e`)
- Other: Yellow (`#f59e0b`)

## Technical Stack

- **Framework**: Django 5.0.1
- **Database**: SQLite (development/production)
- **Static Files**: WhiteNoise with compression
- **Auth**: django-allauth (Microsoft SSO ready)
- **Extensions**: django-extensions for management commands

## Key Features

### Core Models

1. **Entity** - Business entities (LLCs, partnerships, etc.)
2. **Deadline** - Recurring and one-time deadlines
3. **BankAccount** - Operating, personal, investment accounts
4. **CreditCard** - Business and personal credit cards
5. **InsurancePolicy** - All insurance policies by entity
6. **License** - Licenses and permits by entity
7. **Loan** - Loans and financing by entity
8. **Contact** - Business and personal contacts

### Views

- **To-Do**: Urgent deadlines (overdue + this week)
- **List**: All deadlines chronologically
- **Calendar**: Month view with deadlines
- **Entity List**: All business entities
- **Entity Detail**: Comprehensive entity view with 6 tabs (Overview, Financial, Insurance, Licenses, Deadlines, Contacts)
- **Deadline Detail**: Individual deadline with complete/advance functionality

### Auto-Advance Logic

- Deadlines can be marked complete
- System automatically calculates next occurrence based on frequency
- Supports: Daily, Weekly, Monthly, Quarterly, Annually, One-time

## Development Environment

### Virtual Environment

- Location: `/Users/lesgutches/Developer/venvs/deadlines-tracker`
- Python: 3.14.2
- Activate: `source /Users/lesgutches/Developer/venvs/deadlines-tracker/bin/activate`

### Running Development Server

```bash
source /Users/lesgutches/Developer/venvs/deadlines-tracker/bin/activate
python manage.py runserver
```

### Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Static Files

```bash
python manage.py collectstatic --noinput
```

## Data Source

### SSOT (Single Source of Truth)

- Location: `/Users/lesgutches/Library/CloudStorage/OneDrive-NGBSolutions/00_ssot`
- Contains comprehensive reference data:
  - Business entities
  - Bank accounts
  - Credit cards
  - Insurance policies
  - Licenses and permits
  - Contacts
  - Deadlines

### Current Data Population Status

- ✅ Entities: Populated (14 entities)
- ✅ Deadlines: Populated (63 deadlines)
- ⚠️ Bank Accounts: Need to import from SSOT
- ⚠️ Credit Cards: Need to import from SSOT
- ⚠️ Insurance Policies: Need to import from SSOT
- ⚠️ Licenses: Need to import from SSOT
- ⚠️ Loans: Need to import from SSOT
- ⚠️ Contacts: Need to import from SSOT

## Known Issues & TODOs

### Critical (Fix First)

- None currently

### High Priority

- [ ] Implement global search functionality
- [ ] Add keyboard shortcuts for desktop users
- [ ] Convert List page to sortable data table on desktop
- [ ] Populate remaining models from SSOT data
- [ ] Add bulk actions (complete multiple deadlines, export, etc.)

### Medium Priority

- [ ] Advanced filtering (by entity, category, date range, amount)
- [ ] Inline editing for deadlines
- [ ] Document attachment/linking to OneDrive SSOT folders
- [ ] Export functionality (CSV/Excel)
- [ ] Entity relationships (parent/child LLCs, partnership percentages)

### Low Priority

- [ ] Drag-and-drop priority reordering
- [ ] Calendar drag-to-reschedule
- [ ] Templates/presets for common deadline types
- [ ] Print-optimized views

## Testing Notes

### Browser Testing

- Primary: Safari Mobile (iOS)
- Secondary: Chrome Desktop
- Using Chrome MCP for automated testing

### Key Test Scenarios

1. Mark deadline complete → verify auto-advance
2. Filter by entity → verify correct deadlines shown
3. Navigate calendar → verify month navigation
4. Add new deadline → verify all fields save correctly
5. Entity detail tabs → verify all 6 tabs load
6. Mobile responsiveness → verify touch-friendly on iPhone

## Deployment

### Platform

- Railway.app ready (nixpacks.toml configured)
- Environment variables in railway.json

### Static Files

- WhiteNoise serves static files in production
- No external CDN needed

### Database

- SQLite for simplicity (suitable for single-user app)
- Backed up via OneDrive sync to project directory

## Future Enhancements

### Phase 2 (Post-MVP)

- Variable-day frequencies (e.g., "Pacific Power ~24th, 19 days after billing")
- Week-end/bi-weekly payment options
- Auto-generation of deadlines from insurance renewals and license expirations
- Property tax payment schedule tracking (Nov/Feb/May installments with discount logic)
- Utility payment dashboard with autopay status indicators
- Multi-state compliance tracking

### Phase 3 (Advanced Features)

- Email/SMS reminders
- Document storage integration
- Financial reporting and analytics
- Cash flow forecasting based on deadlines
- Integration with accounting systems (QBO API)

---

**Last Updated**: January 20, 2026
**Primary Developer**: Claude (with user guidance)
**User**: Les Gutches
