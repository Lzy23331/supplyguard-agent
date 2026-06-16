import { useState } from "react";
import { TaskCreatePage } from "./pages/TaskCreatePage";
import { TaskDetailPage } from "./pages/TaskDetailPage";

function App() {
  const [taskId, setTaskId] = useState<string | null>(null);
  return taskId ? <TaskDetailPage taskId={taskId} onBack={() => setTaskId(null)} /> : <TaskCreatePage onTaskCreated={setTaskId} />;
}

export default App;
