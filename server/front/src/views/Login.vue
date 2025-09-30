<template>
  <q-page class="login-page flex flex-center">
    <div class="login-container">
      <login-form />
    </div>
  </q-page>
</template>

<script>
import LoginForm from "@/components/LoginForm.vue";
export default {
  components: { LoginForm },
};
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  .body--dark & {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 0 1rem;
}
</style>
