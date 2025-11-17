<!-- 21ac17e3-61af-4218-9a68-76f888d03031 994dc394-a225-4675-b08d-a14c81185c34 -->
# Comprehensive OpAMP Capabilities UI Implementation

## Overview

Enhance the OpAMP capabilities display with expandable category sections, detailed descriptions, status indicators, and bit position information for all 12 capabilities. Display in both AgentDetails and AgentManagement pages.

## Components to Create/Modify

### 1. New Component: `CapabilitiesDetailView.tsx`

**Location**: `frontend/src/components/CapabilitiesDetailView.tsx`

Create a new comprehensive capabilities display component with:

- Expandable sections grouped by category:
  - **Reporting**: ReportsStatus, ReportsEffectiveConfig, ReportsOwnTraces, ReportsOwnMetrics, ReportsOwnLogs, ReportsHealth, ReportsRemoteConfig, ReportsHeartbeat, ReportsAvailableComponents
  - **Configuration**: AcceptsRemoteConfig, ReportsEffectiveConfig, ReportsRemoteConfig
  - **Connection**: AcceptsOpAMPConnectionSettings
  - **Lifecycle**: AcceptsRestartCommand, ReportsHealth, ReportsHeartbeat
- Each capability card shows:
  - Capability name (e.g., "ReportsStatus")
  - Status badge (Enabled/Disabled) with color coding
  - Bit position (e.g., "Bit 0: 0x01")
  - Expandable description section with:
    - "What it is" (brief summary)
    - "Architectural impact" (how it affects the system)
    - "What it buys you" (benefits/use cases)
- Visual indicators:
  - Green checkmark for enabled capabilities
  - Gray X for disabled capabilities
  - Category headers with icons
  - Collapsible/expandable sections

### 2. Update: `CapabilitiesDisplay.tsx`

**Location**: `frontend/src/components/CapabilitiesDisplay.tsx`

Keep existing component for backward compatibility, but add option to use new detailed view:

- Add prop `detailed?: boolean` to toggle between simple and detailed views
- If `detailed=true`, render `CapabilitiesDetailView` instead

### 3. Update: `AgentDetails.tsx`

**Location**: `frontend/src/pages/AgentDetails.tsx`

Replace or enhance the existing capabilities section (around line 337-359):

- Replace `CapabilitiesDisplay` with `CapabilitiesDetailView`
- Pass agent and server capabilities with decoded names
- Show both "Agent Capabilities" and "Server Capabilities" in separate sections

### 4. Update: `AgentManagement.tsx`

**Location**: `frontend/src/pages/AgentManagement.tsx`

Enhance the capabilities display (around line 424-446):

- Replace `CapabilitiesDisplay` with `CapabilitiesDetailView` for selected agent
- Ensure it works within the existing agent selection UI

### 5. Capability Metadata Configuration

**Location**: `frontend/src/config/capabilities.ts` (new file)

Create a configuration file mapping capability names to:

- Bit positions and hex values
- Category assignments
- Detailed descriptions (from user's requirements)
- Icons/visual indicators

Structure:

```typescript
interface CapabilityInfo {
  name: string;
  bitPosition: number;
  hexValue: string;
  category: 'Reporting' | 'Configuration' | 'Connection' | 'Lifecycle';
  description: {
    whatItIs: string;
    architecturalImpact: string;
    whatItBuysYou: string;
  };
  icon?: string;
}
```

## Implementation Details

### Capability Categories and Groupings

**Reporting** (9 capabilities):

- ReportsStatus (Bit 0: 0x01)
- ReportsEffectiveConfig (Bit 2: 0x04)
- ReportsOwnTraces (Bit 5: 0x20)
- ReportsOwnMetrics (Bit 6: 0x40)
- ReportsOwnLogs (Bit 7: 0x80)
- ReportsHealth (Bit 11: 0x800)
- ReportsRemoteConfig (Bit 12: 0x1000)
- ReportsHeartbeat (Bit 13: 0x2000)
- ReportsAvailableComponents (Bit 14: 0x4000)

**Configuration** (3 capabilities):

- AcceptsRemoteConfig (Bit 1: 0x02)
- ReportsEffectiveConfig (Bit 2: 0x04) - also in Reporting
- ReportsRemoteConfig (Bit 12: 0x1000) - also in Reporting

**Connection** (1 capability):

- AcceptsOpAMPConnectionSettings (Bit 8: 0x100)

**Lifecycle** (3 capabilities):

- AcceptsRestartCommand (Bit 10: 0x400)
- ReportsHealth (Bit 11: 0x800) - also in Reporting
- ReportsHeartbeat (Bit 13: 0x2000) - also in Reporting

Note: Some capabilities appear in multiple categories. Display them in all relevant categories or choose primary category.

### UI/UX Design

1. **Category Sections**:

   - Collapsible accordion-style sections
   - Show count of enabled/disabled capabilities per category
   - Category icons (e.g., 📊 Reporting, ⚙️ Configuration, 🔌 Connection, 🔄 Lifecycle)

2. **Capability Cards**:

   - Header with name, status badge, and bit position
   - Expandable body with detailed descriptions
   - Color coding: Green for enabled, Gray for disabled
   - Icons for quick visual identification

3. **Status Indicators**:

   - Enabled: Green checkmark + "Enabled" badge
   - Disabled: Gray X + "Disabled" badge
   - Show bit-field value in hex and decimal

4. **Responsive Design**:

   - Mobile-friendly collapsible sections
   - Grid layout for capability cards
   - Proper spacing and typography

## Data Flow

1. Backend already provides:

   - `opamp_agent_capabilities`: bit-field number
   - `opamp_agent_capabilities_decoded`: array of capability names
   - Same for server capabilities

2. Frontend will:

   - Use decoded names to determine which capabilities are enabled
   - Match names against capability metadata config
   - Display appropriate information based on enabled/disabled status

## Files to Create

1. `frontend/src/components/CapabilitiesDetailView.tsx` - Main detailed view component
2. `frontend/src/config/capabilities.ts` - Capability metadata and descriptions

## Files to Modify

1. `frontend/src/components/CapabilitiesDisplay.tsx` - Add detailed view option
2. `frontend/src/pages/AgentDetails.tsx` - Replace capabilities section
3. `frontend/src/pages/AgentManagement.tsx` - Enhance capabilities display

## Testing Considerations

- Verify all 12 capabilities display correctly
- Test expandable sections functionality
- Verify enabled/disabled status matches bit-field
- Test responsive design on mobile/tablet
- Verify descriptions are accurate and complete
- Test with agents that have different capability sets

### To-dos

- [ ] Update Template model: add default_version_id, is_system_template, make org_id nullable, add constraints
- [ ] Create Alembic migration 008_add_template_default_version_and_system_support.py
- [ ] Update TemplateService: add set_default_version, load_config_from_gateway, support system templates
- [ ] Update template schemas: add default_version_id, is_system_template, new request/response types
- [ ] Add API endpoints: PUT /templates/{id}/default-version, POST /templates/from-gateway, POST /templates/upload
- [ ] Create TemplateCreateModal component with three tabs: Create New, Upload File, Load from Gateway
- [ ] Create TemplateVersionSelector component with default version indicator and set-as-default action
- [ ] Refactor Templates.tsx: integrate TemplateCreateModal, add version management UI, show default version badges
- [ ] Update frontend API service: add setDefaultVersion, createFromGateway, uploadTemplate methods
- [ ] Update CreateConfigDeployment.tsx: remove Load from Gateway, add template selector with version override
- [ ] Ensure system templates integration: show both org and system templates, handle migration if needed