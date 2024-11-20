<template>
  <span class="size-icon" :class="[type, size]" :title="`${type}: ${size}`">
    <svg v-if="type === 'additions'" viewBox="0 0 24 24" class="w-5 h-5">
      <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
    </svg>
    <svg v-else-if="type === 'deletions'" viewBox="0 0 24 24" class="w-5 h-5">
      <path fill="currentColor" d="M19 13H5v-2h14v2z" />
    </svg>
    <svg v-else viewBox="0 0 24 24" class="w-5 h-5">
      <path
        fill="currentColor"
        d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"
      />
    </svg>
  </span>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ["additions", "deletions", "total"].includes(value),
  },
  size: {
    type: String,
    required: true,
    validator: (value) => ["small", "medium", "large", "none"].includes(value),
  },
});
</script>

<style scoped>
.size-icon {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 4px;
  margin: 0 4px;
}

.size-icon svg {
  width: 16px;
  height: 16px;
}

.additions {
  color: #2da44e;
}

.deletions {
  color: #cf222e;
}

.total {
  color: #6e7781;
}

.small {
  background: #dafbe1;
}

.medium {
  background: #ffd8d6;
}

.large {
  background: #fff1e5;
}

.none {
  background: #f6f8fa;
}
</style>
