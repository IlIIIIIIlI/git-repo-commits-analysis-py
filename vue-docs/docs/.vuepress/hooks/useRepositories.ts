// docs/.vuepress/hooks/useRepositories.ts
import { ref, onMounted } from "vue";

export interface RepositoryInfo {
  text: string;
  link: string;
}

export function useRepositories() {
  const repositories = ref<RepositoryInfo[]>([]);
  const loading = ref(true);
  const error = ref<string | null>(null);

  const fetchRepositories = async () => {
    try {
      const response = await fetch("http://localhost:8000/repositories");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const repos = await response.json();
      repositories.value = repos.map((repo: string) => ({
        text: repo,
        link: `/reports/${repo.replace("/", "_")}/`,
      }));
    } catch (err) {
      console.error("Error fetching repositories:", err);
      error.value =
        err instanceof Error ? err.message : "Failed to fetch repositories";
    } finally {
      loading.value = false;
    }
  };

  onMounted(fetchRepositories);

  return {
    repositories,
    loading,
    error,
    fetchRepositories,
  };
}

export default useRepositories;
