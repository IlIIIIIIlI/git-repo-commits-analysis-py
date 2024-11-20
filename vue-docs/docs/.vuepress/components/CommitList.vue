// docs/.vuepress/components/CommitList.vue
<template>
  <div class="commit-list">
    <div v-if="loading" class="loading">Loading commits...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-for="(commitsInDate, date) in groupedCommits" :key="date">
        <div class="date-expander">
          <div
            class="date-header"
            @click="toggleDate(date)"
            :class="{ expanded: expandedDates[date] }"
          >
            <h3>{{ formatDate(date) }} ({{ commitsInDate.length }} commits)</h3>
            <span class="expand-icon">{{
              expandedDates[date] ? "▼" : "▶"
            }}</span>
          </div>

          <div v-show="expandedDates[date]" class="commits-container">
            <div
              v-for="commit in commitsInDate"
              :key="commit.id"
              class="commit-card"
            >
              <div class="commit-header">
                <h4>{{ commit.title }}</h4>
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
                <span class="commit-time">{{
                  formatDateTime(commit.date)
                }}</span>
                <span class="commit-sha">{{ commit.id.slice(0, 7) }}</span>
                <span class="commit-author">By {{ commit.author }}</span>
              </div>

              <div v-if="commitReports[commit.id]" class="commit-report">
                <div v-html="commitReports[commit.id].content"></div>
              </div>
              <div v-else class="report-loading">Loading report...</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import dayjs from "dayjs";
import SizeIcon from "./SizeIcon.vue";

const props = defineProps({
  repository: {
    type: String,
    required: true,
  },
});

const commits = ref([]);
const commitReports = ref({});
const loading = ref(true);
const error = ref(null);
const expandedDates = ref({});

// Group commits by date
const groupedCommits = computed(() => {
  const groups = {};
  commits.value.forEach((commit) => {
    const date = dayjs(commit.date).format("YYYY-MM-DD");
    if (!groups[date]) groups[date] = [];
    groups[date].push(commit);
  });
  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .reduce((acc, date) => {
      acc[date] = groups[date].sort(
        (a, b) => new Date(b.date) - new Date(a.date)
      );
      return acc;
    }, {});
});

const formatDate = (date) => dayjs(date).format("YYYY-MM-DD");
const formatDateTime = (date) => dayjs(date).format("YYYY-MM-DD HH:mm");

const toggleDate = (date) => {
  expandedDates.value[date] = !expandedDates.value[date];
  if (expandedDates.value[date]) {
    loadReportsForDate(date);
  }
};

const loadReportsForDate = async (date) => {
  const dayCommits = groupedCommits.value[date] || [];
  await Promise.all(
    dayCommits.map(async (commit) => {
      if (!commitReports.value[commit.id]) {
        try {
          const response = await fetch(
            `/api/reports/${props.repository}/${commit.id}`
          );
          if (response.ok) {
            const report = await response.json();
            commitReports.value[commit.id] = report;
          }
        } catch (err) {
          console.error(`Error loading report for commit ${commit.id}:`, err);
        }
      }
    })
  );
};

onMounted(async () => {
  try {
    // 获取提交列表
    const response = await fetch(`/api/commits`);
    if (!response.ok) throw new Error("Failed to fetch commits");
    const allCommits = await response.json();
    commits.value = allCommits.filter((c) => c.repository === props.repository);

    // 默认展开最新的日期
    const latestDate = Object.keys(groupedCommits.value)[0];
    if (latestDate) {
      expandedDates.value[latestDate] = true;
      await loadReportsForDate(latestDate);
    }
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.commit-list {
  max-width: 1200px;
  margin: 0 auto;
}

.date-expander {
  margin-bottom: 1rem;
}

.date-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--c-bg-light);
  border-radius: 6px;
  cursor: pointer;
  border-left: 4px solid var(--c-brand);
  user-select: none;
}

.date-header h3 {
  margin: 0;
  font-size: 1.1em;
}

.expand-icon {
  transition: transform 0.2s;
}

.date-header.expanded .expand-icon {
  transform: rotate(180deg);
}

.commits-container {
  padding: 1rem 0;
  animation: slideDown 0.3s ease;
}

.commit-card {
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.commit-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.commit-header h4 {
  margin: 0;
  font-size: 1.1em;
}

.commit-stats {
  display: flex;
  gap: 0.5rem;
}

.commit-meta {
  color: var(--c-text-lighter);
  font-size: 0.9em;
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
}

.commit-sha {
  font-family: monospace;
  background: var(--c-bg-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.commit-report {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--c-border);
}

.report-loading {
  text-align: center;
  padding: 1rem;
  color: var(--c-text-lighter);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
