# Raildrops Accessibility Testing Guide

This guide provides step-by-step instructions for testing the accessibility features of the Raildrops application. It focuses on screen reader compatibility and keyboard navigation following both WCAG 2.1 guidelines and Windsurf rules.

## Table of Contents

1. [Testing Environment Setup](#testing-environment-setup)
2. [Screen Reader Testing](#screen-reader-testing)
   - [NVDA (Windows)](#nvda-windows)
   - [JAWS (Windows)](#jaws-windows)
   - [VoiceOver (macOS/iOS)](#voiceover-macosios)
3. [Keyboard Navigation Testing](#keyboard-navigation-testing)
4. [Component Testing Checklists](#component-testing-checklists)
5. [Automated Testing Tools](#automated-testing-tools)

## Testing Environment Setup

### Required Software

- **Screen Readers:**
  - [NVDA](https://www.nvaccess.org/download/) (Free, Windows)
  - [JAWS](https://www.freedomscientific.com/products/software/jaws/) (Commercial, Windows)
  - VoiceOver (Built into macOS/iOS)

- **Browsers to Test:**
  - Google Chrome
  - Mozilla Firefox
  - Safari (macOS/iOS)
  - Microsoft Edge

- **Testing Devices:**
  - Desktop (Windows/macOS)
  - Tablet (iPad or Android)
  - Mobile Phone (iPhone or Android)

### Application Setup

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Ensure all migrations are applied:
   ```
   python manage.py migrate
   ```

3. Load test data if needed:
   ```
   python manage.py loaddata test_data
   ```

## Screen Reader Testing

### NVDA (Windows)

#### Setup

1. Download and install [NVDA](https://www.nvaccess.org/download/)
2. Start NVDA (Ctrl+Alt+N)
3. Basic commands:
   - Start/Stop reading: NVDA+Down Arrow / Control
   - Navigate by headings: H
   - Navigate by landmarks: D
   - Navigate by links: K
   - Navigate by form controls: F

#### Test Scenarios

##### Login Page Test

1. Navigate to: http://localhost:8000/accounts/member/login/
2. Press H to navigate through headings
   - Verify "Logg inn" heading is announced correctly
3. Press F to navigate through form fields
   - Verify field labels are announced
   - Verify validation errors are announced when submitting invalid data
4. Test password visibility toggle
   - Verify button is announced with its function
   - Verify state changes are announced

##### Member Dashboard Test

1. Login and navigate to: http://localhost:8000/accounts/dashboard/
2. Press H to navigate through headings hierarchy
   - Verify main heading "Min Dashboard" is announced
   - Verify section headings are properly structured
3. Navigate to table with T key
   - Verify table header and row information is announced correctly
   - Check that mobile card view is accessible when viewport is resized

### JAWS (Windows)

#### Setup

1. Install JAWS (commercial software)
2. Basic commands:
   - Start/Stop reading: Insert+Down Arrow / Control
   - List headings: Insert+F6
   - List landmarks: Insert+F7
   - List links: Insert+F7 (then tab to links)

#### Test Scenarios

Same test scenarios as NVDA, but using JAWS commands.

### VoiceOver (macOS/iOS)

#### Setup

1. Enable VoiceOver on macOS: Command+F5
2. Basic commands:
   - Start/Stop reading: VO+A (VO = Control+Option)
   - Navigate next/previous item: VO+Right Arrow / VO+Left Arrow
   - Navigate by headings: VO+Command+H
   - Navigate by landmarks: VO+Command+L

#### Test Scenarios

##### Mobile Testing (iOS)

1. Open Safari on iOS and navigate to your development URL
2. Enable VoiceOver (triple-click home button or side button)
3. Swipe right to navigate through elements
4. Test responsiveness and accessibility on mobile viewport

## Keyboard Navigation Testing

### Basic Navigation

1. Start with the browser focused on the address bar
2. Press Tab repeatedly to move through all interactive elements
   - Verify focus order is logical and follows page structure
   - Verify visible focus indicator on all interactive elements
   - Verify skip-to-content link appears on first Tab press

### Focus Trapping

1. Test modal dialogs
   - Verify focus is trapped inside the modal when open
   - Verify focus returns to trigger element when closed

### Component Testing

1. Test form controls
   - Verify all controls can be activated with keyboard
   - Verify error messages are associated with inputs

2. Test dark/light mode toggle
   - Verify it can be activated with Enter or Space key
   - Verify theme changes are applied correctly

3. Test toast notifications
   - Verify they can be dismissed with keyboard
   - Verify they are announced by screen readers

## Component Testing Checklists

### Forms

- [ ] All inputs have associated labels
- [ ] Required fields are marked and announced
- [ ] Error messages are linked to inputs with aria-describedby
- [ ] Submit buttons work with Enter key
- [ ] Custom controls (like password toggle) are keyboard accessible

### Tables

- [ ] Tables have proper headers with scope attributes
- [ ] Tables have captions or aria-label for context
- [ ] Mobile alternative views maintain same information

### Buttons & Links

- [ ] All buttons have accessible names
- [ ] Icons have aria-hidden="true" and text alternatives
- [ ] Links have descriptive text (not "click here")

### Dialogs & Modals

- [ ] Focus is trapped inside modal dialogs
- [ ] Modals can be closed with Escape key
- [ ] Focus returns to trigger element when closed

## Automated Testing Tools

### Browser Extensions

- [WAVE Evaluation Tool](https://wave.webaim.org/extension/)
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) (built into Chrome DevTools)

### Command Line Tools

Integrate these into your CI/CD pipeline:

```bash
# Install pa11y-ci
npm install -g pa11y-ci

# Run accessibility tests
pa11y-ci http://localhost:8000/accounts/login/ http://localhost:8000/accounts/dashboard/
```

## WCAG Compliance Checklist

- **Perceivable**
  - [ ] Text alternatives for non-text content
  - [ ] Captions and alternatives for multimedia
  - [ ] Content can be presented in different ways
  - [ ] Content is distinguishable (color, contrast)

- **Operable**
  - [ ] All functionality available from keyboard
  - [ ] Users have enough time to read content
  - [ ] Content doesn't cause seizures
  - [ ] Users can navigate and find content

- **Understandable**
  - [ ] Text is readable and understandable
  - [ ] Content appears and operates in predictable ways
  - [ ] Users are helped to avoid and correct mistakes

- **Robust**
  - [ ] Content is compatible with current and future tools

## Testing Report Template

```markdown
# Accessibility Testing Report

## Test Environment
- Browser: 
- Screen Reader: 
- Date: 

## Issues Found

### High Priority
- [ ] Issue 1: Description
  - Location: 
  - WCAG Violation: 
  - Steps to Reproduce: 

### Medium Priority
- [ ] Issue 2: Description

### Low Priority
- [ ] Issue 3: Description

## Passed Checks
- [x] Feature 1: Description
- [x] Feature 2: Description

## Screenshots/Recordings

## Recommendations
```

---

This testing guide aligns with Windsurf rules requiring Bootstrap 5 accessibility, HTML5 doctype, semantic HTML, and ARIA attribute usage throughout the Raildrops application.