# docs/.vuepress/components/CommitGroup.vue
<template>
  <div class="commit-group">
    <div
      class="date-header"
      @click="isExpanded = !isExpanded"
      :class="{ expanded: isExpanded }"
    >
      <div class="date-info">
        <span class="date">{{ formatDate(date) }}</span>
        <span class="commit-count">({{ commits.length }} commits)</span>
      </div>
      <span class="expand-icon">{{ isExpanded ? "▼" : "▶" }}</span>
    </div>
    <div v-show="isExpanded" class="commits-container">
      <div v-for="commit in commits" :key="commit.id" class="commit-card">
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
            <SizeIcon type="total" :size="commit.stats?.total_size || 'none'" />
          </div>
        </div>
        <div class="commit-meta">
          <span class="commit-time">{{ formatDateTime(commit.date) }}</span>
          <span class="commit-sha">{{ commit.id.slice(0, 7) }}</span>
          <span class="commit-author">By {{ commit.author }}</span>
        </div>
        <div v-if="commitReports[commit.id]" class="commit-report">
          <div
            class="report-content"
            v-html="commitReports[commit.id].content"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import dayjs from "dayjs";
import SizeIcon from "./SizeIcon.vue";

const props = defineProps({
  date: {
    type: String,
    required: true,
  },
  commits: {
    type: Array,
    required: true,
  },
});

const isExpanded = ref(false);
const commitReports = ref({});

const formatDate = (date) => dayjs(date).format("YYYY-MM-DD");
const formatDateTime = (date) => dayjs(date).format("YYYY-MM-DD HH:mm");

const fetchReports = async () => {
  for (const commit of props.commits) {
    try {
      const response = await fetch(
        `/api/reports/${commit.repository}/${commit.id}`
      );
      if (response.ok) {
        const report = await response.json();
        commitReports.value[commit.id] = report;
      }
    } catch (err) {
      console.error(`Error fetching report for commit ${commit.id}:`, err);
    }
  }
};

onMounted(fetchReports);
</script>

<style scoped>
.commit-group {
  margin-bottom: 1rem;
}

.date-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--c-bg-light);
  border-radius: 6px;
  cursor: pointer;
  user-select: none;
  border-left: 4px solid var(--c-brand);
  transition: all 0.3s ease;
}

.date-header:hover {
  background: var(--c-bg-lighter);
}

.date-info {
  display: flex;
  gap: 8px;
  align-items: center;
}

.date {
  font-weight: 500;
  color: var(--c-text);
}

.commit-count {
  color: var(--c-text-lighter);
  font-size: 0.9em;
}

.expand-icon {
  color: var(--c-text-lighter);
  transition: transform 0.3s ease;
}

.expanded .expand-icon {
  transform: rotate(90deg);
}

.commits-container {
  padding: 16px;
  animation: slideDown 0.3s ease;
}

.commit-card {
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: var(--c-bg);
}

.commit-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.commit-title {
  margin: 0;
  font-size: 1.1em;
  flex: 1;
  padding-right: 16px;
}

.commit-stats {
  display: flex;
  gap: 8px;
}

.commit-meta {
  display: flex;
  gap: 16px;
  color: var(--c-text-lighter);
  font-size: 0.9em;
  margin-bottom: 16px;
}

.commit-sha {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  background: var(--c-bg-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.commit-report {
  padding-top: 16px;
  border-top: 1px solid var(--c-border);
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
