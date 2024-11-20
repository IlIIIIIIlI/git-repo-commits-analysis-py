# Repository Structure

<ClientOnly>
  <div class="structure-container">
    <div v-if="loading" class="loading">Loading repository structure...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="Object.keys(structure).length === 0" class="no-data">
        No repository data available
      </div>
      <div v-else class="structure-tree">
        <div v-for="(repo, repoName) in structure" :key="repoName" class="repo-node">
          <h2 class="repo-title">
            <router-link :to="'/reports/' + repoName">{{ repoName }}</router-link>
          </h2>
          <div class="dates-container">
            <div v-for="(dateInfo, date) in repo" :key="date" class="date-node">
              <h3 class="date-title">{{ formatDate(date) }}</h3>
              <div class="report-info">
                <span class="report-count">Reports: {{ dateInfo.report_count }}</span>
                <ul class="report-list">
                  <li v-for="sha in dateInfo.reports" :key="sha" class="report-item">
                    <code class="commit-sha">{{ sha.slice(0, 7) }}</code>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</ClientOnly>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'

const structure = ref({})
const loading = ref(true)
const error = ref(null)

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD')
}

onMounted(async () => {
  try {
    const response = await fetch('/api/debug/reports/structure')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    structure.value = await response.json()
  } catch (err) {
    error.value = 'Failed to load repository structure: ' + err.message
  } finally {
    loading.value = false
  }
})
</script>

<style>
.structure-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading, .error, .no-data {
  padding: 20px;
  text-align: center;
  border-radius: 6px;
  margin: 20px 0;
}

.loading {
  background: var(--c-bg-light);
  color: var(--c-text-lighter);
}

.error {
  background: #fff5f5;
  color: #cf222e;
  border: 1px solid #ffdce0;
}

.no-data {
  background: var(--c-bg-light);
  color: var(--c-text-lighter);
  border: 1px solid var(--c-border);
}

.repo-node {
  margin-bottom: 32px;
}

.repo-title {
  border-bottom: 2px solid var(--c-brand);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.repo-title a {
  color: var(--c-text);
  text-decoration: none;
}

.repo-title a:hover {
  color: var(--c-brand);
}

.dates-container {
  padding-left: 16px;
}

.date-node {
  margin: 16px 0;
  padding: 16px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: var(--c-bg-lighter);
}

.date-title {
  color: var(--c-text-light);
  margin: 0 0 8px 0;
  font-size: 1.1em;
}

.report-info {
  color: var(--c-text-lighter);
}

.report-count {
  font-weight: 500;
}

.report-list {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-item {
  display: inline-block;
}

.commit-sha {
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, monospace;
  background: var(--c-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
</style>
