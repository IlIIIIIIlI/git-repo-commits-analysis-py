// docs/.vuepress/components/DynamicSidebar.vue
<template>
  <div class="dynamic-sidebar">
    <div v-if="loading" class="loading">Loading repositories...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="sidebar-content">
      <h2 class="sidebar-title">Repositories</h2>
      <ul class="repo-list">
        <li v-for="repo in repositories" :key="repo.text" class="repo-item">
          <router-link
            :to="repo.link"
            class="repo-link"
            :class="{ active: isActive(repo.link) }"
          >
            {{ repo.text }}
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from '@vuepress/client'
import useRepositories from "../hooks/useRepositories";

const route = useRoute();
const { repositories, loading, error } = useRepositories();

const isActive = (link: string) => {
  return route.path.startsWith(link);
};
</script>

<style scoped>
.dynamic-sidebar {
  padding: 1rem;
}

.sidebar-title {
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: 1rem;
  color: var(--c-text);
}

.repo-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.repo-item {
  margin: 0.5rem 0;
}

.repo-link {
  display: block;
  padding: 0.5rem;
  color: var(--c-text);
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.repo-link:hover {
  background: var(--c-bg-lighter);
}

.repo-link.active {
  background: var(--c-bg-light);
  color: var(--c-brand);
  font-weight: 500;
}

.loading {
  padding: 1rem;
  color: var(--c-text-lighter);
}

.error {
  padding: 1rem;
  color: #cf222e;
}
</style>
