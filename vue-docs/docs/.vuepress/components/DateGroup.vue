<template>
  <div class="date-group">
    <h2 class="date-header">{{ formatDate(date) }}</h2>
    <div class="commits-container">
      <CommitReport
        v-for="commit in commits"
        :key="commit.id"
        :commit="commit"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import dayjs from "dayjs";
import CommitReport from "./CommitReport.vue";

const props = defineProps({
  date: {
    type: String,
    required: true,
  },
  commits: {
    type: Array,
    required: true,
    default: () => [],
  },
});

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD");
};

const sortedCommits = computed(() => {
  return [...props.commits].sort((a, b) => {
    // First sort by date in descending order
    const dateCompare = new Date(b.date) - new Date(a.date);
    if (dateCompare !== 0) return dateCompare;

    // If the dates are the same, sort by commit length in descending order (usually longer commits contain more information)
    return b.title.length - a.title.length;
  });
});
</script>

<style scoped>
.date-group {
  margin-bottom: 32px;
  animation: fade-in 0.3s ease-in-out;
}

.date-header {
  padding: 12px 16px;
  background: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 1.4em;
  color: #24292e;
  border-left: 4px solid #0366d6;
}

.commits-container {
  padding: 0 16px;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .date-header {
    background: #161b22;
    color: #c9d1d9;
    border-left-color: #1f6feb;
  }
}
</style>
