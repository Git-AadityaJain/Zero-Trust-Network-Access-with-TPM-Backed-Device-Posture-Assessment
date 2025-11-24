# Policy Engine - Future Scope

## Current Status
✅ Frontend policy management is fully functional:
- Create, edit, delete policies
- Activate/deactivate policies
- Filter and view policy details
- JSON rules input (free-form textarea)

## Future Enhancement: Policy Engine Integration

### Goal
Replace the free-form JSON rules textarea with a structured dropdown/rule builder that only allows rules supported by the policy engine.

### Requirements

1. **Policy Engine Development**
   - Create a policy evaluation engine that can process specific rule types
   - Define the supported rule schema/structure
   - Implement rule validation logic

2. **Frontend Changes**
   - Replace JSON textarea with rule builder UI
   - Implement dropdown/selector for rule types
   - Limit available rules to those supported by the policy engine
   - Provide structured input fields based on selected rule type
   - Validate rules against policy engine schema before submission

3. **Rule Types to Support** (to be defined based on policy engine capabilities)
   - Device compliance rules
   - Access control rules
   - Security posture rules
   - Time-based rules
   - Location-based rules
   - User role-based rules
   - Custom conditions

### Implementation Notes

- The current JSON textarea allows flexibility during development
- Once policy engine is implemented, rules must conform to engine's schema
- Frontend should prevent invalid rule configurations
- Consider a rule builder UI with:
  - Rule type selector
  - Condition builder
  - Value input fields
  - Rule preview/validation

### Files to Modify

- `frontend/src/pages/PoliciesPage.jsx` - Replace rules textarea with rule builder
- `backend/app/services/policy_service.py` - Add policy engine integration
- `backend/app/schemas/policy.py` - Update rule schema to match engine requirements
- Create new rule builder component(s) in frontend

### Testing Checklist (Future)

- [ ] Rule builder allows only valid rule types
- [ ] Rules are validated against policy engine schema
- [ ] Invalid rules are rejected with clear error messages
- [ ] Rule preview shows formatted rule structure
- [ ] Policy engine can evaluate all created rules
- [ ] Migration path for existing JSON rules (if needed)

