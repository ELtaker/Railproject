# Raildrops Practical Testing Script

This script provides step-by-step instructions for testing the accessibility features we've implemented in Raildrops. Follow this script to verify compliance with Windsurf accessibility rules.

## Prerequisites

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Have NVDA installed on Windows (or VoiceOver enabled on macOS)

## Test 1: Skip-to-Content Link

### Keyboard Test
1. Open http://localhost:8000/accounts/member/login/
2. Press Tab once (without clicking anything)
3. **Expected**: Skip-to-content link appears
4. Press Enter
5. **Expected**: Focus jumps to the main content area

## Test 2: Login Form Accessibility

### Screen Reader Test (NVDA)
1. Start NVDA (Ctrl+Alt+N)
2. Navigate to http://localhost:8000/accounts/member/login/
3. Press H to navigate to the heading
   - **Expected**: "Logg inn" is announced
4. Press F repeatedly to move through form fields
   - **Expected**: Each field is announced with its label ("E-post", "Passord")
5. Enter invalid email and password
6. Submit the form
   - **Expected**: Error messages are announced by the screen reader

### Keyboard Test
1. Tab through all form elements
   - **Expected**: Focus indicator appears on each element
2. Test password visibility toggle
   - **Expected**: Tab to the eye icon, press Enter, and the password should become visible

## Test 3: Dark/Light Mode Toggle

1. Navigate to any page
2. Tab to the dark/light mode toggle (bottom right)
3. Press Enter
   - **Expected**: Page switches between dark and light mode
4. With NVDA active, toggle again
   - **Expected**: Screen reader announces the mode change

## Test 4: Member Dashboard

### Screen Reader Test
1. Login and navigate to http://localhost:8000/accounts/dashboard/
2. Press H repeatedly to explore headings
   - **Expected**: Headings follow proper hierarchy (h1 → h2 → h3)
3. Press T to find tables
   - **Expected**: Screen reader announces table with correct column headers

### Responsive Test
1. Use browser dev tools to simulate mobile viewport (375px width)
   - **Expected**: Table transforms into card layout
2. With NVDA active, explore the mobile layout
   - **Expected**: All information is still accessible and announced properly

## Test 5: Form Validation

1. Go to member login page (http://localhost:8000/accounts/member/login/) and submit empty form
   - **Expected**: Error messages appear with proper ARIA associations
2. Test with NVDA
   - **Expected**: Error messages are announced after form submission

## Test 6: Keyboard Navigation Flow

1. Start at http://localhost:8000/
2. Using only Tab, Shift+Tab, Enter, and Space keys, try to:
   - Navigate the main menu
   - Access the login form
   - Submit the form
   - Toggle dark/light mode
   - **Expected**: All interactive elements can be accessed and activated

## Test 7: ARIA Landmarks

With NVDA running:
1. Press D to navigate between landmarks
   - **Expected**: You can navigate between header, main content, and footer

## Common Issues to Watch For

- Focus indicators that are difficult to see
- Interactive elements with no visible focus state
- Form fields without proper label associations
- Elements that can be clicked with a mouse but not with keyboard
- Content that disappears or appears without being announced to screen readers
- Color combinations with poor contrast ratios

## Testing Report

Track issues using this format:

```
Issue: [Description]
Location: [URL and element]
Priority: [High/Medium/Low]
WCAG Criteria: [e.g., 2.1.1 Keyboard]
Steps to Reproduce: [Steps]
```

---

Remember that all accessibility features implemented must comply with Windsurf rules for Bootstrap 5, semantic HTML, and responsive design.
