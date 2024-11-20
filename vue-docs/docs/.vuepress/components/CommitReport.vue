// docs/.vuepress/components/CommitReport.vue
<template>
  <div class="commit-report">
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
      <span class="commit-date">{{ formatDate(commit.date) }}</span>
      <span class="commit-sha">{{ commit.id.slice(0, 7) }}</span>
      <span class="commit-author">By {{ commit.author }}</span>
    </div>
    <div class="commit-content" v-if="report">
      <div class="report-layout">
        <div class="report-main">
          <div v-html="processedContent"></div>
        </div>
        <div class="report-toc">
          <div class="toc-container">
            <div v-if="headers.length" class="toc-title">Contents</div>
            <nav class="table-of-contents">
              <div
                v-for="header in headers"
                :key="header.slug"
                class="toc-item"
                :class="[`level-${header.level}`]"
              >
                <a
                  :href="`#${header.slug}`"
                  :title="header.title"
                  class="toc-link"
                >
                  {{ header.title }}
                </a>
              </div>
            </nav>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="loading">Loading report...</div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import dayjs from "dayjs";
import { marked } from "marked";
import SizeIcon from "./SizeIcon.vue";

const props = defineProps({
  commit: {
    type: Object,
    required: true,
  },
});

const report = ref(null);
const headers = ref([]);

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD HH:mm");
};

// Process Markdown content, extract titles and generate a table of contents
const processContent = (content) => {
  const extractedHeaders = [];
  const renderer = new marked.Renderer();

  renderer.heading = (text, level) => {
    const slug = text
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")//Support Chinese
      .replace(/^-+|-+$/g, ""); //Remove leading and trailing hyphens

    extractedHeaders.push({
      level,
      title: text,
      slug,
    });

    return `<h${level} id="${slug}">${text}</h${level}>`;
  };

  marked.setOptions({
    renderer,
    headerIds: true,
    gfm: true,
  });

  const htmlContent = marked(content);
  headers.value = extractedHeaders;

  return htmlContent;
};

const processedContent = computed(() => {
  if (!report.value) return "";
  return processContent(report.value.content);
});

// Get report content
const fetchReport = async () => {
  try {
    const formattedRepo = props.commit.repository.replace(/\//g, "_");
    const response = await fetch(
      `/api/reports/${formattedRepo}/${props.commit.id}`
    );
    if (response.ok) {
      report.value = await response.json();
    }
  } catch (error) {
    console.error("Error fetching report:", error);
  }
};

onMounted(fetchReport);
</script>

<style scoped>
.commit-report {
  border: 1px solid var(--c-border);
  border-radius: 8px;
  margin-bottom: 1.5rem;
  background: var(--c-bg);
}

.commit-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid var(--c-border);
}

.commit-title {
  margin: 0;
  font-size: 1.1em;
  flex: 1;
}

.commit-meta {
  padding: 0.5rem 1rem;
  color: var(--c-text-lighter);
  font-size: 0.9em;
  display: flex;
  gap: 1rem;
  background: var(--c-bg-light);
}

.commit-sha {
  font-family: monospace;
  background: var(--c-bg);
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
}

.report-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 250px;
  gap: 2rem;
  padding: 1rem;
}

.report-main {
  min-width: 0;
}

.report-toc {
  position: sticky;
  top: 4rem;
}

.toc-container {
  background: var(--c-bg-light);
  border-radius: 6px;
  padding: 1rem;
}

.toc-title {
  font-weight: 500;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--c-border);
}

.table-of-contents {
  font-size: 0.9em;
}

.toc-item {
  margin: 0.2rem 0;
}

.toc-item.level-1 {
  padding-left: 0;
}
.toc-item.level-2 {
  padding-left: 1rem;
}
.toc-item.level-3 {
  padding-left: 2rem;
}

.toc-link {
  display: block;
  padding: 0.2rem 0;
  color: var(--c-text);
  text-decoration: none;
  transition: color 0.3s;
}

.toc-link:hover {
  color: var(--c-brand);
}

.loading {
  padding: 2rem;
  text-align: center;
  color: var(--c-text-lighter);
}

@media (max-width: 719px) {
  .report-layout {
    grid-template-columns: 1fr;
  }

  .report-toc {
    order: -1;
    position: static;
  }
}

/* Report content style */
:deep(.report-main) {
  line-height: 1.7;
}

:deep(.report-main h1) {
  font-size: 1.8em;
  margin: 1.5em 0 1em;
}

:deep(.report-main h2) {
  font-size: 1.4em;
  margin: 1.5em 0 1em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--c-border);
}

:deep(.report-main h3) {
  font-size: 1.2em;
  margin: 1.2em 0 0.8em;
}

:deep(.report-main p) {
  margin: 1em 0;
}

:deep(.report-main code) {
  background: var(--c-bg-light);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

:deep(.report-main strong) {
  color: var(--c-text-accent);
}
</style>
