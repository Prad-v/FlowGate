<!-- 21ac17e3-61af-4218-9a68-76f888d03031 92e6ad26-9499-4c24-a8c2-3431ff900c27 -->
# Template Page Refactoring with Version Control

## Overview
Transform the template page into a centralized config template management system with Google GSM-style version control, supporting both org-scoped and global (system) templates, with three creation methods.

## Database Schema Changes

### 1. Update Template Model (`backend/services/flowgate-backend/app/models/template.py`)
- Add `default_version_id` column (UUID, ForeignKey to `template_versions.id`, nullable)
- Add `is_system_template` boolean column (default False) to distinguish global vs org-scoped templates
- Make `org_id` nullable (system templates won't have org_id)
- Add unique constraint on `(name, org_id)` where org_id is not null, and `(name)` where is_system_template is true
- Update relationships to handle nullable org_id

### 2. Update TemplateVersion Model
- Ensure `version` field is immutable after creation
- Add index on `(template_id, version)` for efficient lookups

### 3. Create Migration
- Create Alembic migration `008_add_template_default_version_and_system_support.py`
- Add `default_version_id`, `is_system_template` columns
- Make `org_id` nullable
- Add constraints and indexes
- Migrate existing templates (set is_system_template=false, ensure org_id is set)

## Backend API Changes

### 4. Update Template Service (`backend/services/flowgate-backend/app/services/template_service.py`)
- Add method `set_default_version(template_id, version, org_id)` to set default version
- Update `create_template()` to handle system templates (org_id=None when is_system_template=True)
- Update `get_templates()` to support filtering by is_system_template
- Add method `load_config_from_gateway(gateway_id, org_id)` that fetches effective config from OpAMP
- Add validation for default_version_id (must belong to the template)

### 5. Add Template Router Endpoints (`backend/services/flowgate-backend/app/routers/templates.py`)
- `PUT /templates/{template_id}/default-version` - Set default version (requires version number)
- `POST /templates/from-gateway` - Create template from gateway config (new endpoint)
- `POST /templates/upload` - Create template from uploaded file (multipart/form-data)
- Update `GET /templates` to support `?is_system_template=true/false` filter
- Update `POST /templates` to accept `is_system_template` field

### 6. Update Template Schemas (`backend/services/flowgate-backend/app/schemas/template.py`)
- Add `default_version_id` to `TemplateResponse`
- Add `is_system_template` to `TemplateCreate` and `TemplateResponse`
- Add `SetDefaultVersionRequest` schema with `version` field
- Add `CreateFromGatewayRequest` schema with `gateway_id`, `name`, `description`
- Make `org_id` optional in relevant schemas

## Frontend Changes

### 7. Update Templates Page (`frontend/src/pages/Templates.tsx`)
- Replace single "Create Template" button with three options:
  - **Create New Template**: Modal with free-form YAML text editor (existing functionality enhanced)
  - **Upload Template**: File upload button with drag-and-drop support
  - **Load from Gateway**: Dropdown to select gateway, then create template from its config
- Add version management UI:
  - Show current default version badge/indicator on each template
  - Version selector dropdown when viewing/editing template
  - "Set as Default" button next to each version in version list
  - Display version history with timestamps and descriptions

### 8. Create Template Creation Modal Component (`frontend/src/components/TemplateCreateModal.tsx`)
- Three tabs or buttons: "Create New", "Upload File", "Load from Gateway"
- **Create New tab**: Name, description, template type, YAML textarea (with syntax highlighting)
- **Upload File tab**: File input with drag-and-drop, preview of uploaded content
- **Load from Gateway tab**: Gateway selector dropdown, preview of config, name/description inputs
- Validation before submission
- Success/error handling

### 9. Create Template Version Selector Component (`frontend/src/components/TemplateVersionSelector.tsx`)
- Dropdown showing all versions with:
  - Version number
  - "Default" badge for current default version
  - Timestamp
  - Description/changelog
- "Set as Default" action for non-default versions
- Visual indicator (star/checkmark) for default version

### 10. Update API Service (`frontend/src/services/api.ts`)
- Add `templateApi.setDefaultVersion(templateId, version, orgId)`
- Add `templateApi.createFromGateway(gatewayId, name, description, orgId)`
- Add `templateApi.uploadTemplate(file, name, description, templateType, orgId)`
- Update `templateApi.list()` to support `isSystemTemplate` parameter
- Add `templateApi.getSystemTemplates()` for global templates

### 11. Update Template Detail Page (if exists) or enhance Templates page
- Show version history table with:
  - Version number
  - Default indicator
  - Created date
  - Description
  - Actions: View, Set as Default, Rollback
- Version comparison view (diff between versions)

## Integration Points

### 12. Update Deployment Creation (`frontend/src/pages/CreateConfigDeployment.tsx`)
- Remove "Load from Gateway" functionality (moved to templates page)
- Add template selector that shows:
  - Template name
  - Default version (auto-selected)
  - Version override dropdown (optional)
- 

### To-dos

- [x] 