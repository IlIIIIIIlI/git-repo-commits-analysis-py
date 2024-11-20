<ClientOnly>
<div class="reports-container">
  <div class="repository-selector" v-if="repositories.length > 0">
    <label for="repo-select">Select Repository:</label>
    <select 
      id="repo-select" 
      v-model="currentRepo" 
      @change="fetchCommits(currentRepo)"
      class="repo-select"
    >
      <option v-for="repo in repositories" :key="repo" :value="repo">
        {{ repo }}
      </option>
    </select>
  </div>

  <div v-if="loading" class="loading">Loading commits...</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else>
    <div v-if="!commits.length" class="no-commits">
      No commits found for this repository
    </div>
    <div v-else>
      <div v-for="(commitsInDate, date) in groupedCommits" :key="date" class="date-section">
        <h2 class="date-header">{{ formatDate(date) }}</h2>
        <div class="commit-list">
          <div v-for="commit in commitsInDate" :key="commit.id" class="commit-item">
            <div class="commit-header">
              <h3 class="commit-title">{{ commit.title }}</h3>
              <div class="commit-stats">
                <SizeIcon
                  type="additions"
                  :size="commit.stats?.additions_size || 'none'"
                />
                <SizeIcon
                  type="deletions"
                  :size="commit.stats?.deletions_size || 'none'"
                />
                <SizeIcon 
                  type="total" 
                  :size="commit.stats?.total_size || 'none'"
                />
              </div>
            </div>
            <div class="commit-meta">
              <span class="commit-date">{{ formatDateTime(commit.date) }}</span>
              <span class="commit-sha">{{ commit.id.slice(0, 7) }}</span>
              <span class="commit-author">By {{ commit.author }}</span>
            </div>
            <div v-if="commitReports[commit.id]" class="commit-content">
              <div v-html="commitReports[commit.id].content"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
</div>
</ClientOnly>

<script setup>
import { ref, onMounted, computed } from 'vue'
import dayjs from 'dayjs'
import SizeIcon from '@/components/SizeIcon.vue'  // 修改这里

const repositories = ref([])
const currentRepo = ref('')
const commits = ref([])
const loading = ref(true)
const error = ref(null)
const commitReports = ref({})

const fetchRepositories = async () => {
  try {
    const response = await fetch('/api/repositories')
    if (response.ok) {
      repositories.value = await response.json()
      if (repositories.value.length > 0) {
        currentRepo.value = repositories.value[0]
        await fetchCommits(currentRepo.value)
      }
    }
  } catch (err) {
    error.value = 'Error loading repositories: ' + err.message
  }
}

const fetchCommits = async (repo) => {
  loading.value = true
  error.value = null
  commits.value = []
  commitReports.value = {}
  
  try {
    const response = await fetch(`/api/commits`)
    if (response.ok) {
      const allCommits = await response.json()
      commits.value = allCommits.filter(c => c.repository === repo)
      // Fetch reports for each commit
      await Promise.all(commits.value.map(commit => fetchCommitReport(commit)))
    } else {
      error.value = `Error: ${response.statusText}`
    }
  } catch (err) {
    error.value = 'Error loading commits: ' + err.message
  } finally {
    loading.value = false
  }
}

const formatRepository = (repo) => {
  return repo.replace(/\//g, '_')
}

import { marked } from 'marked'

const fetchCommitReport = async (commit) => {
  try {
    const formattedRepo = formatRepository(commit.repository)
    const response = await fetch(`/api/reports/${formattedRepo}/${commit.id}`)
    if (response.ok) {
      const report = await response.json()
      console.log(report);
      report.content = marked(report.content)
      commitReports.value[commit.id] = report
    }
  } catch (err) {
    console.error(`Error fetching report for commit ${commit.id}:`, err)
  }
}

const groupedCommits = computed(() => {
  const groups = {}
  commits.value.forEach(commit => {
    const date = dayjs(commit.date).format('YYYY-MM-DD')
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(commit)
  })
  // Sort dates in descending order
  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .reduce((acc, date) => {
      acc[date] = groups[date].sort((a, b) => 
        new Date(b.date) - new Date(a.date)
      )
      return acc
    }, {})
})

const formatDate = (date) => dayjs(date).format('YYYY-MM-DD')
const formatDateTime = (date) => dayjs(date).format('YYYY-MM-DD HH:mm')

onMounted(fetchRepositories)
</script>

<style>
.reports-container {
  margin: 20px;
}

.repository-selector {
  margin: 20px 0;
  padding: 16px;
  background: var(--c-bg-light);
  border-radius: 6px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.repo-select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid var(--c-border);
  background: var(--c-bg);
  color: var(--c-text);
  font-size: 0.9em;
  min-width: 200px;
}

.date-section {
  margin-bottom: 2rem;
}

.date-header {
  padding: 12px 16px;
  background: var(--c-bg-light);
  border-radius: 6px;
  margin-bottom: 1rem;
  border-left: 4px solid var(--c-brand);
}

.commit-item {
  border: 1px solid var(--c-border);
  border-radius: 6px;
  margin-bottom: 1rem;
  padding: 1rem;
  background: var(--c-bg);
}

.commit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.commit-title {
  margin: 0;
  font-size: 1.1em;
  color: var(--c-text);
}

.commit-meta {
  color: var(--c-text-lighter);
  font-size: 0.9em;
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
}

.commit-sha {
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, monospace;
  background: var(--c-bg-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.commit-stats {
  display: flex;
  gap: 8px;
}

.commit-content {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--c-border);
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
