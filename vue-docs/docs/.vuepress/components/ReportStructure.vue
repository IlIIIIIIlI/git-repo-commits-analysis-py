<template>
  <div class="report-structure">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="structure-tree">
      <div
        v-for="(repo, repoName) in structure"
        :key="repoName"
        class="repo-node"
      >
        <h2>
          <router-link :to="'/reports/' + repoName">{{ repoName }}</router-link>
        </h2>
        <div class="dates-container">
          <div v-for="(dateInfo, date) in repo" :key="date" class="date-node">
            <h3>{{ date }}</h3>
            <div class="report-info">
              Reports: {{ dateInfo.report_count }}
              <ul class="report-list">
                <li v-for="sha in dateInfo.reports" :key="sha">
                  <code>{{ sha }}</code>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const structure = ref({});
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const response = await axios.get("/api/debug/reports/structure");
    structure.value = response.data;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.report-structure {
  padding: 20px;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error {
  color: #cf222e;
  padding: 20px;
  border: 1px solid #ffdce0;
  border-radius: 6px;
  background: #fff5f5;
}

.repo-node {
  margin-bottom: 32px;
}

.repo-node h2 {
  border-bottom: 2px solid #0366d6;
  padding-bottom: 8px;
}

.dates-container {
  margin-left: 16px;
}

.date-node {
  margin: 16px 0;
  padding: 16px;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
}

.report-info {
  margin-top: 8px;
  color: #666;
}

.report-list {
  margin-top: 8px;
  list-style: none;
  padding-left: 16px;
}

.report-list code {
  font-family: monospace;
  background: #f6f8fa;
  padding: 2px 4px;
  border-radius: 3px;
}
</style>
