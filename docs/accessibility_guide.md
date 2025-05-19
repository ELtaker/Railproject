# Raildrops Accessibility Guide

This guide documents the accessibility features implemented in the Raildrops platform and provides guidelines for maintaining and extending these features in new components.

## Table of Contents

1. [Accessibility Components](#accessibility-components)
2. [Testing Procedures](#testing-procedures)
3. [Implementation Guidelines](#implementation-guidelines)
4. [Screen Reader Support](#screen-reader-support)

## Accessibility Components

### Toast Notifications
Replaces standard JavaScript alerts with accessible, dismissible notifications.

```html
<div class="toast-container position-fixed top-0 end-0 p-3">
  <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
    <div class="toast-header bg-success text-white">
      <strong class="me-auto">Melding</strong>
      <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Lukk"></button>
    </div>
    <div class="toast-body">{{ message }}</div>
  </div>
</div>
```

**Accessibility Features:**
- Uses `role="alert"` for screen reader announcements
- `aria-live="assertive"` ensures immediate announcement
- Close button has `aria-label="Lukk"`
- Color contrast meets WCAG AA standards

### Dark/Light Mode Toggle
Implemented in base template to support user preference for reduced eye strain.

```html
<button class="btn btn-sm" id="theme-toggle" aria-label="Bytt fargemodus">
  <i class="fa fa-moon" aria-hidden="true"></i>
  <span class="d-none d-md-inline ms-1">Fargemodus</span>
</button>
```

**Accessibility Features:**
- Respects `prefers-color-scheme` media query
- Persists user preference in localStorage
- Clear visual indication of current mode
- Keyboard accessible

### Loading Spinner
Consistent loading indicator with text alternative.

```html
<div class="spinner-container text-center my-4">
  <div class="spinner-border" role="status" aria-hidden="true"></div>
  <span class="visually-hidden">Laster innhold...</span>
</div>
```

**Accessibility Features:**
- `role="status"` for proper semantic meaning
- Visually hidden text for screen readers
- Sufficient size and contrast

### Skip-to-Content Link
Allows keyboard users to bypass navigation.

```html
<a href="#main-content" class="visually-hidden-focusable skip-link">
  Hopp til hovedinnhold
</a>
```

**Accessibility Features:**
- Only visible when focused (for keyboard users)
- First focusable element in the DOM
- Targets main content area with `id="main-content"`

### Responsive Tables
Tables that adapt to mobile screens with proper structure.

```html
<div class="table-responsive" role="region" aria-label="[Table Description]">
  <table class="table table-striped align-middle">
    <caption class="visually-hidden">[Table Description]</caption>
    <thead>
      <tr>
        <th scope="col">Column Header</th>
        <!-- Additional headers -->
      </tr>
    </thead>
    <tbody>
      <tr>
        <th scope="row">Row Header</th>
        <td>Cell data</td>
        <!-- Additional cells -->
      </tr>
    </tbody>
  </table>
</div>
```

**Mobile Card Alternative:**
```html
<div class="d-md-none">
  <div class="card mb-3">
    <div class="card-body">
      <h3 class="card-title h5">[Row Header]</h3>
      <p class="card-text">[Cell Data]</p>
      <!-- Additional data -->
    </div>
  </div>
</div>
```

## Testing Procedures

### Screen Reader Testing

Test all pages with the following screen readers:
- **NVDA** (Windows) - Free, open-source
- **VoiceOver** (macOS/iOS) - Built into Apple devices
- **TalkBack** (Android) - Built into Android devices

#### Testing Checklist:
- [ ] Verify all interactive elements are announced correctly
- [ ] Confirm heading hierarchy makes sense (h1 → h2 → h3)
- [ ] Test that ARIA landmarks provide proper navigation
- [ ] Ensure form fields have proper labels and error states
- [ ] Verify that dynamic content updates are announced

### Keyboard Navigation Testing

- [ ] Tab through the entire page to ensure logical flow
- [ ] Verify that all interactive elements can be activated with keyboard
- [ ] Check that focus indicators are visible on all elements
- [ ] Test that modal dialogs trap focus appropriately
- [ ] Ensure dropdown menus can be navigated with arrow keys

### Responsive Design Testing

Test on multiple devices and viewport sizes:
- Desktop (1920×1080, 1366×768)
- Tablet (iPad, 768×1024)
- Mobile (iPhone, 375×667)

## Implementation Guidelines

### Semantic HTML

- Use the most appropriate HTML element for the content
- Prefer semantic elements over generic `<div>` and `<span>`
- Maintain proper heading hierarchy (h1, h2, h3)
- Follow HTML5 doctype as required by Windsurf rules

### ARIA Best Practices

- Only use ARIA when HTML semantics are insufficient
- Always test with actual screen readers
- Follow the "first rule of ARIA": don't use ARIA if native HTML can do the job

### Color and Contrast

- Ensure all text meets WCAG AA contrast requirements
- Don't rely on color alone to convey information
- Provide sufficient contrast in both light and dark modes
- Use Bootstrap 5 color utilities for consistency

### Forms and Validation

- All form fields must have visible labels
- Use HTML5 validation attributes where possible
- Provide clear error messages
- Group related fields with `<fieldset>` and `<legend>`

```html
<div class="mb-3">
  <label for="phone" class="form-label">Telefon</label>
  <input type="tel" 
         class="form-control" 
         id="phone" 
         name="phone" 
         pattern="^(\+\d{1,3}[- ]?)?\d{8,10}$" 
         aria-describedby="phone-help"
         required>
  <div id="phone-help" class="form-text">Format: +47 12345678</div>
</div>
```

## Templates to Update

The following templates should be updated with accessibility enhancements:

1. **Login and Registration Forms**
   - Add proper ARIA attributes
   - Improve error handling
   - Enhance keyboard navigation

2. **Giveaway Detail Pages**
   - Add proper heading hierarchy
   - Enhance form controls for participation
   - Improve status indicators

3. **Business Profile Pages**
   - Enhance image accessibility 
   - Improve data display on mobile
   - Add skip links for long content

## Additional Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [Bootstrap 5 Accessibility](https://getbootstrap.com/docs/5.0/getting-started/accessibility/)
- [MDN Web Docs: Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)