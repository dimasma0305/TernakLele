<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Header Section -->
      <div class="login-header">
        <div class="login-icon">
          <q-icon name="security" size="3rem" color="primary" />
        </div>
        <h1 class="login-title">Access Control</h1>
        <p class="login-subtitle">Enter server password to continue</p>
      </div>

      <!-- Form Section -->
      <div class="login-form">
        <q-form @submit.prevent="onSubmit" class="form">
          <div class="form-group">
            <div class="floating-label">
              <q-input
                v-model="password"
                type="password"
                placeholder="Enter server password"
                class="form-input password-input"
                :class="{ 'input-error': hasError }"
                outlined
                dense
                :loading="isLoading"
                @keyup.enter="onSubmit"
                @input="clearError"
                ref="passwordInput"
              >
                <template v-slot:prepend>
                  <q-icon name="lock" color="grey-6" />
                </template>
                
                <template v-slot:append>
                  <q-btn
                    flat
                    round
                    dense
                    :icon="showPassword ? 'visibility_off' : 'visibility'"
                    @click="togglePasswordVisibility"
                    class="password-toggle"
                  />
                </template>
              </q-input>
              <label class="form-label">Server Password</label>
            </div>
            
            <div v-if="errorMessage" class="form-message message-error">
              <q-icon name="error" size="sm" />
              {{ errorMessage }}
            </div>
          </div>

          <div class="form-actions">
            <q-btn
              type="submit"
              color="primary"
              class="login-btn"
              :loading="isLoading"
              :disable="!password || password.length < 1"
              unelevated
              size="lg"
            >
              <q-icon name="login" left />
              Access Platform
            </q-btn>
          </div>
        </q-form>
      </div>

      <!-- Security Notice -->
      <div class="security-notice">
        <q-icon name="info" size="sm" color="grey-6" />
        <span>This is a secure CTF platform. Unauthorized access is prohibited.</span>
      </div>
    </div>

    <!-- Background Pattern -->
    <div class="login-background"></div>
  </div>
</template>

<script>
import { mapMutations } from "vuex";

export default {
  name: 'LoginForm',
  
  data() {
    return {
      password: '',
      showPassword: false,
      isLoading: false,
      hasError: false,
      errorMessage: '',
    };
  },
  
  mounted() {
    // Focus on password input when component mounts
    this.$nextTick(() => {
      if (this.$refs.passwordInput) {
        this.$refs.passwordInput.focus();
      }
    });
  },
  
  methods: {
    async onSubmit() {
      if (!this.password || this.password.length < 1) {
        this.showError('Password is required');
        return;
      }
      
      this.isLoading = true;
      this.clearError();
      
      try {
        // Simulate authentication delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        this.setServerPassword(this.password);
        
        // Show success feedback
        this.$q.notify({
          type: 'positive',
          message: 'Authentication successful',
          icon: 'check_circle',
          timeout: 2000,
        });
        
        // Navigate to flags page
        await this.$router.push({ name: "flags" });
        
      } catch (error) {
        this.showError('Authentication failed. Please check your password.');
      } finally {
        this.isLoading = false;
      }
    },
    
    togglePasswordVisibility() {
      this.showPassword = !this.showPassword;
      // Update input type
      const inputEl = this.$refs.passwordInput.$el.querySelector('input');
      if (inputEl) {
        inputEl.type = this.showPassword ? 'text' : 'password';
      }
    },
    
    showError(message) {
      this.hasError = true;
      this.errorMessage = message;
      
      // Clear error after 5 seconds
      setTimeout(() => {
        this.clearError();
      }, 5000);
    },
    
    clearError() {
      this.hasError = false;
      this.errorMessage = '';
    },
    
    ...mapMutations(["setServerPassword"]),
  },
};
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  background: var(--background-primary);
  
  @media (max-width: 599px) {
    padding: 1rem;
  }
}

.login-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 3rem;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  transition: all 200ms ease-out;
  
  :root[data-theme='dark'] & {
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  }
  
  @media (max-width: 599px) {
    padding: 2rem;
    border-radius: 0.75rem;
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
    
    :root[data-theme='dark'] & {
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
    }
  }
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
  
  .login-icon {
    margin-bottom: 1rem;
    
    .q-icon {
      opacity: 0.8;
    }
  }
  
  .login-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
  }
  
  .login-subtitle {
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin: 0;
    line-height: 1.5;
  }
}

.login-form {
  margin-bottom: 1.5rem;
  
  .form-group {
    margin-bottom: 1.5rem;
  }
  
  .floating-label {
    position: relative;
    
    .form-label {
      position: absolute;
      top: -0.5rem;
      left: 0.75rem;
      background: var(--surface);
      padding: 0 0.25rem;
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-secondary);
      z-index: 1;
      transition: all 200ms ease-out;
    }
  }
  
  .password-input {
    :deep(.q-field__control) {
      height: 56px;
      border-radius: 0.5rem;
      transition: all 200ms ease-out;
      
      &:hover {
        border-color: var(--border-hover);
      }
    }
    
    :deep(.q-field__native) {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1rem;
      padding: 0 0.75rem;
    }
    
    &.input-error {
      :deep(.q-field__control) {
        border-color: var(--error) !important;
      }
    }
    
    &:focus-within {
      :deep(.q-field__control) {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px var(--focus-ring);
      }
      
      ~ .form-label {
        color: var(--primary);
      }
    }
  }
  
  .password-toggle {
    color: var(--text-secondary);
    transition: color 150ms ease-out;
    
    &:hover {
      color: var(--text-primary);
    }
  }
  
  .form-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
    font-size: 0.875rem;
    
    &.message-error {
      color: var(--error);
    }
  }
  
  .form-actions {
    margin-top: 2rem;
    
    .login-btn {
      width: 100%;
      height: 48px;
      font-weight: 600;
      font-size: 1rem;
      letter-spacing: 0.02em;
      border-radius: 0.5rem;
      transition: all 200ms ease-out;
      
      &:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
      }
      
      &:active:not(:disabled) {
        transform: translateY(0);
      }
      
      &:disabled {
        opacity: 0.6;
      }
    }
  }
}

.security-notice {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
  padding: 1rem;
  background: var(--background-secondary);
  border-radius: 0.5rem;
  border: 1px solid var(--border);
}

.login-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  background: 
    radial-gradient(circle at 20% 80%, var(--primary) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, var(--secondary) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, var(--accent) 0%, transparent 50%);
  animation: backgroundFloat 20s ease-in-out infinite;
  z-index: 0;
}

@keyframes backgroundFloat {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  33% {
    transform: translate(30px, -30px) rotate(120deg);
  }
  66% {
    transform: translate(-20px, 20px) rotate(240deg);
  }
}

// Loading state animation
.login-btn {
  :deep(.q-spinner) {
    color: currentColor;
  }
}

// Enhanced focus states for accessibility
.login-form {
  :deep(*:focus) {
    outline: 2px solid var(--focus-ring);
    outline-offset: 2px;
  }
}

// Smooth theme transitions
.login-container,
.login-card,
.login-header,
.login-form,
.security-notice {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}
</style>
