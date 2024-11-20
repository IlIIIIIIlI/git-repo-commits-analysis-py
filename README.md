# git-repo-commits-analysis-py
A tool used to analyse all history commits of a certain repo


```{bash}
curl -X POST http://localhost:8000/analyze \
-H "Content-Type: application/json" \
-d '{
    "repositories": "reworkd/AgentGPT",
    "start_date": "2023-04-09",
    "end_date": "2023-04-10"
}'
```

```{bash}
╰─❯ curl http://localhost:8000/tasks/{867934e7-88b9-4359-9e84-0c2f95a0ce19}
{"id":"867934e7-88b9-4359-9e84-0c2f95a0ce19","repositories":"reworkd/AgentGPT","start_date":"2023-04-09","end_date":"2023-04-10","status":"completed","created_at":"2024-11-20T15:53:31.673998","completed_at":"2024-11-20T15:54:08.024375","error":null,"processed_commits":33,"total_commits":0}%     
```

```{bash}
╰─❯ curl -X POST http://localhost:8000/reports/generate-batch \
-H "Content-Type: application/json" \
-d '{
    "repository": "reworkd/AgentGPT",
    "date": "2023-04-10"
}'
{"task_id":"b5e288c4-adb1-455e-8a33-9a8a06468b65","repository":"reworkd/AgentGPT","date":"2023-04-10","total_commits":0,"completed_commits":0,"status":"pending","created_at":"2024-11-20T15:55:28.323242","updated_at":"2024-11-20T15:55:28.323247","completed_at":null,"error":null}% 
```