# MidPrint End-to-End Testing Plan

## Overview

This document outlines the comprehensive testing strategy for the MidPrint application, focusing on validating the complete workflow from user prompts to browser automation with real-time visual feedback.

## Test Categories

### 1. Core Navigation Scenarios

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| NAV-01 | Simple URL navigation via chat prompt | Browser navigates to URL, displays screenshot, updates URL bar | High |
| NAV-02 | Navigation with incomplete URL (without protocol) | System adds appropriate protocol and navigates successfully | Medium |
| NAV-03 | Navigation to non-existent domain | System shows appropriate error message and recovery options | Medium |
| NAV-04 | Back/forward navigation commands | Browser correctly navigates through history | Low |

### 2. Form Interaction Scenarios

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| FORM-01 | Login form completion (username/password) | Fields are filled correctly with typing indicators | High |
| FORM-02 | Search form submission | Text is entered, form submitted, results displayed | High |
| FORM-03 | Complex form with multiple field types | All field types correctly filled and submitted | Medium |
| FORM-04 | Form with validation errors | System handles errors appropriately | Medium |

### 3. Multi-Step Complex Workflows

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| FLOW-01 | Search-click-extract workflow | Complete 3-step process with visual feedback | High |
| FLOW-02 | Navigation with conditional logic | System handles decision points based on page content | Medium |
| FLOW-03 | Long-running workflow (10+ steps) | Completes all steps with state persistence | Medium |
| FLOW-04 | Workflow requiring wait periods | System properly waits then continues execution | Low |

### 4. State Synchronization Tests

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| SYNC-01 | URL state synchronization | Frontend URL bar matches actual browser URL | High |
| SYNC-02 | Page title synchronization | Frontend shows correct page title from backend | Medium |
| SYNC-03 | Task status synchronization | Task status in UI matches backend task state | High |
| SYNC-04 | Image synchronization latency test | Measure time between action and screenshot update | Medium |

### 5. Error Handling and Recovery

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| ERR-01 | Element not found error | Displays helpful error message, allows retry | High |
| ERR-02 | Navigation timeout | System handles timeouts gracefully | Medium |
| ERR-03 | JavaScript error on page | System continues functioning despite page errors | Medium |
| ERR-04 | WebSocket disconnection recovery | System reconnects and resumes functionality | High |

### 6. Performance Tests

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| PERF-01 | Screenshot streaming performance | Consistently maintains target FPS under load | High |
| PERF-02 | Rapid action sequence performance | System remains responsive during quick actions | Medium |
| PERF-03 | Long-running task memory usage | Memory consumption remains stable over time | Medium |
| PERF-04 | Concurrent task handling | Multiple tasks execute without interference | Low |

### 7. Visual Feedback Verification

| Test ID | Description | Expected Result | Priority |
|---------|-------------|-----------------|----------|
| VIS-01 | Click visualization accuracy | Click indicators appear at correct coordinates | High |
| VIS-02 | Typing visualization | Typing indicators show correct text input | Medium |
| VIS-03 | Highlight element accuracy | Element highlights surround correct elements | Medium |
| VIS-04 | Action indicator timing | Indicators appear and disappear with correct timing | Low |

## Test Environment Requirements

- **Backend**: Running instance with WebSocket capability
- **Frontend**: Development server with connection to backend
- **Test Sites**: Mix of custom test pages and public websites
- **Network**: Tests under both optimal and throttled conditions
- **Browsers**: Chrome (primary), Firefox and Safari (secondary)

## Manual Testing Procedure

1. Launch backend server with: `cd backend && python -m app.main`
2. Launch frontend server with: `cd frontend && npm run dev`
3. Open browser to frontend URL
4. Execute test cases according to priority
5. Document any failures with screenshots and detailed steps
6. Note any performance issues or visual glitches

## Automated Test Scripts

Automated test scripts will be created for high-priority tests and stored in the `tests/end-to-end/scripts` directory. Each script will:

1. Set up test environment
2. Submit user prompts via API
3. Verify task execution status
4. Capture screenshots for visual validation
5. Verify synchronization between frontend and backend
6. Report results with timing metrics

## Known Limitations and Issues

This section will be updated as testing progresses with any discovered limitations or known issues that cannot be fixed immediately.

## Success Criteria

The testing phase will be considered successful when:

1. All high-priority tests pass without errors
2. At least 80% of medium-priority tests pass without errors
3. Performance metrics meet target thresholds
4. Any critical issues are identified and fixed
5. Known limitations are documented 