import { defineClientConfig } from "@vuepress/client";
import DynamicSidebar from "./components/DynamicSidebar.vue";
import CommitGroup from "./components/CommitGroup.vue";
import ReportsLayout from "./components/ReportsLayout.vue";

export default defineClientConfig({
  enhance({ app }) {
    app.component("DynamicSidebar", DynamicSidebar);
    app.component("CommitGroup", CommitGroup);
    app.component("ReportsLayout", ReportsLayout);
  },
});
