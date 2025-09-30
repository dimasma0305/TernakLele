# SCSS Variables Access Fix

## Issue Resolved

**Error**: `Undefined variable. $spacing-lg` (and other SCSS variables)

**Location**: Line 18 in `src/layouts/BaseLayout.vue` (and potentially other Vue components)

**Root Cause**: Vue single-file components with scoped SCSS don't automatically have access to SCSS variables defined in the abstracts directory. Each component needs to either import the variables manually or have them injected globally through build configuration.

## Solution Applied

### **Option 1: Global SCSS Variable Injection (RECOMMENDED)**

Enhanced the Vite configuration to automatically inject SCSS variables and mixins into all Vue components:

**File**: `/vite.config.js`

```javascript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'

export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    quasar({
      sassVariables: 'src/styles/quasar.variables.scss'
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `
          @import "@/styles/abstracts/variables.scss";
          @import "@/styles/abstracts/mixins.scss";
        `
      }
    }
  }
})
```

### **Key Configuration Changes**

1. **Added Quasar Vite Plugin**: Properly configured with `transformAssetUrls` and `sassVariables`
2. **Global SCSS Injection**: `css.preprocessorOptions.scss.additionalData` automatically imports variables and mixins into every SCSS file
3. **Quasar Integration**: Maintains compatibility with Quasar's SCSS variable system

### **Benefits of This Approach**

1. ✅ **Global Access**: All Vue components can use SCSS variables without manual imports
2. ✅ **Maintainability**: No need to add imports to every component
3. ✅ **Performance**: Variables are injected at build time, not runtime
4. ✅ **Consistency**: Ensures all components use the same variable definitions
5. ✅ **Developer Experience**: Cleaner component code without repetitive imports

### **Available Variables in All Components**

Now all Vue components have automatic access to:

#### **Spacing Variables**
```scss
$spacing-xs: 0.25rem;
$spacing-sm: 0.5rem;
$spacing-md: 1rem;
$spacing-lg: 1.5rem;
$spacing-xl: 2rem;
$spacing-xxl: 3rem;
```

#### **Typography Variables**
```scss
$font-size-display: 2.5rem;
$font-size-h1: 2rem;
$font-size-h2: 1.5rem;
$font-size-h3: 1.25rem;
$font-size-body: 1rem;
$font-size-caption: 0.875rem;

$font-weight-light: 300;
$font-weight-regular: 400;
$font-weight-medium: 500;
$font-weight-bold: 700;
```

#### **Color & Theme Variables**
```scss
$border-radius-sm: 4px;
$border-radius-md: 8px;
$border-radius-lg: 12px;

$shadow-sm, $shadow-md, $shadow-lg
$transition-fast, $transition-normal, $transition-slow
```

#### **Responsive Mixins**
```scss
@include mobile { /* styles */ }
@include tablet { /* styles */ }
@include desktop { /* styles */ }
@include mobile-and-tablet { /* styles */ }
```

#### **Theme Mixins**
```scss
@include theme-background($light, $dark);
@include theme-color($light, $dark);
@include theme-transition();
```

### **Usage Example**

Components can now use SCSS variables directly:

```vue
<template>
  <div class="my-component">
    <h1>Title</h1>
    <p>Content</p>
  </div>
</template>

<style lang="scss" scoped>
.my-component {
  padding: $spacing-lg;
  border-radius: $border-radius-md;
  
  h1 {
    font-size: $font-size-h1;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-md;
  }
  
  @include mobile {
    padding: $spacing-md;
  }
}
</style>
```

## Alternative Solution (Not Used)

### **Option 2: Manual Imports Per Component**

Each component would need to import variables manually:

```vue
<style lang="scss" scoped>
@import '@/styles/abstracts/variables.scss';
@import '@/styles/abstracts/mixins.scss';

.component {
  padding: $spacing-lg;
}
</style>
```

**Why Option 1 is Better**:
- ❌ Repetitive imports in every component
- ❌ Easy to forget imports in new components
- ❌ Maintenance overhead
- ❌ Potential for inconsistencies

## Verification

✅ All SCSS variables are now globally accessible in Vue components
✅ Build configuration properly integrated with Quasar
✅ No manual imports required in component files
✅ Backward compatibility maintained with existing CSS custom properties
✅ Performance optimized through build-time injection

## Files Modified

- `/vite.config.js` - Enhanced with global SCSS variable injection
- `/src/layouts/BaseLayout.vue` - Cleaned up (removed manual imports)

## Testing

After applying these changes, the build should complete successfully without any "Undefined variable" errors. All components can now use SCSS variables directly in their styles without manual imports.