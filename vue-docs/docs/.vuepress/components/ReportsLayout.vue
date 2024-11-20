// docs/.vuepress/theme/RepoLayout.vue
<template>
  <div class="repo-layout">
    <!-- Custom Sidebar -->
    <div class="repo-sidebar">
      <h2 class="sidebar-title">Repositories</h2>
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <ul v-else class="repo-list">
        <li v-for="repo in repositories" :key="repo">
          <router-link
            :to="`/reports/${repo.replace('/', '_')}`"
            class="repo-link"
            :class="{ active: isCurrentRepo(repo) }"
          >
            {{ repo }}
          </router-link>
        </li>
      </ul>
    </div>

    <!-- Main Content -->
    <div class="repo-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const repositories = ref([]);
const loading = ref(true);
const error = ref(null);

const isCurrentRepo = (repo) => {
  const currentPath = route.path;
  const encodedRepo = repo.replace("/", "_");
  return currentPath.includes(encodedRepo);
};

onMounted(async () => {
  try {
    const response = await fetch("/api/repositories");
    if (!response.ok) throw new Error("Failed to fetch repositories");
    repositories.value = await response.json();
  } catch (err) {
    console.error("Error loading repositories:", err);
    error.value = err.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.repo-layout {
  display: flex;
  min-height: calc(100vh - var(--navbar-height));
  margin-top: var(--navbar-height);
}

.repo-sidebar {
  position: fixed;
  top: var(--navbar-height);
  left: 0;
  bottom: 0;
  width: 260px;
  padding: 2rem 1rem;
  background: var(--c-bg);
  border-right: 1px solid var(--c-border);
  overflow-y: auto;
}

.sidebar-title {
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0 0 1rem;
  padding: 0.5rem;
  color: var(--c-text);
}

.repo-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.repo-link {
  display: block;
  padding: 0.5rem 1rem;
  margin: 0.2rem 0;
  color: var(--c-text);
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.repo-link:hover {
  background: var(--c-bg-lighter);
}

.repo-link.active {
  background: var(--c-bg-light);
  color: var(--c-brand);
  font-weight: 500;
}

.repo-content {
  flex: 1;
  margin-left: 260px;
  padding: 2rem;
  min-height: 100%;
}

.loading,
.error {
  padding: 1rem;
  text-align: center;
  color: var(--c-text-lighter);
}

.error {
  color: #cf222e;
}

@media (max-width: 719px) {
  .repo-layout {
    flex-direction: column;
  }

  .repo-sidebar {
    position: static;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--c-border);
    padding: 1rem;
  }

  .repo-content {
    margin-left: 0;
    padding: 1rem;
  }
}
</style>
