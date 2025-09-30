<template>
  <q-card class="login-card" :class="$q.dark.isActive ? 'bg-dark' : ''">
    <q-card-section class="text-center">
      <div class="text-h5 q-mb-md">Welcome to Ternak Lele</div>
      <div class="text-subtitle2">Please enter your password to continue</div>
    </q-card-section>
    <q-card-section>
      <q-form @submit.prevent="onSubmit">
        <div class="row">
          <div class="col col-12">
            <q-input
              outlined
              v-model="password"
              type="password"
              label="Password"
              :color="$q.dark.isActive ? 'secondary' : 'primary'"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="lock" />
              </template>
            </q-input>
          </div>
        </div>
        <div class="q-pt-md text-center">
          <q-btn 
            label="Login" 
            type="submit" 
            :color="$q.dark.isActive ? 'secondary' : 'primary'" 
            unelevated
            rounded
            class="full-width"
          />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

<script>
import { mapMutations } from "vuex";

export default {
  data: function () {
    return {
      password: null,
    };
  },
  methods: {
    onSubmit: async function () {
      this.setServerPassword(this.password);
      await this.$router.push({ name: "flags" });
    },
    ...mapMutations(["setServerPassword"]),
  },
};
</script>

<style lang="scss">
.login-card {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  
  .q-card__section {
    padding: 32px;
  }
  
  .body--dark & {
    background: rgba(30, 30, 30, 0.95);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }
}
</style>
