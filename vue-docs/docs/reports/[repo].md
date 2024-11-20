# docs/reports/[repo].md

<template>
  <div class="repository-page">
    <h1>{{ repository }}</h1>
    
    <div v-if="loading" class="loading">Loading commits...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="Object.keys(groupedCommits).length === 0" class="no-commits">
        No commits found for this repository
      </div>
      <div v-else>
        <CommitGroup
          v-for="(commits, date) in groupedCommits"
          :key="date"
          :date="date"
          :commits="commits"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'

const route = useRoute()
const repository = computed(() => route.params.repo.replace('_', '/'))
const commits = ref([])
const loading = ref(true)
const error = ref(null)

const groupedCommits = computed(() => {
  const groups = {}
  commits.value.forEach(commit => {
    const date = dayjs(commit.date).format('YYYY-MM-DD')
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(commit)
  })
  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .reduce((acc, date) => {
      acc[date] = groups[date].sort((a, b) => new Date(b.date) - new Date(a.date))
      return acc
    }, {})
})

const fetchCommits = async () => {
  try {
    const response = await fetch(`/api/commits`)
    if (response.ok) {
      const allCommits = await response.json()
      commits.value = allCommits.filter(c => c.repository === repository.value)
    } else {
      error.value = `Error: ${response.statusText}`
    }
  } catch (err) {
    error.value = 'Error loading commits: ' + err.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchCommits)
</script>

<style>
.repository-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading, .error, .no-commits {
  padding: 20px;
  text-align: center;
  border-radius: 6px;
  margin: 20px 0;
}

.loading {
  background: var(--c-bg-light);
}

.error {
  background: #fff5f5;
  color: #cf222e;
  border: 1px solid #ffdce0;
}

.no-commits {
  background: var(--c-bg-light);
  color: var(--c-text-lighter);
  border: 1px solid var(--c-border);
}
</style>
