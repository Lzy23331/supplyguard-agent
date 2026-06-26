import { useEffect, useState } from "react";
import { DemoGalleryPage } from "./pages/DemoGalleryPage";
import { LandingPage } from "./pages/LandingPage";
import { ProviderStatusPage } from "./pages/ProviderStatusPage";
import { TaskCreatePage } from "./pages/TaskCreatePage";
import { TaskDetailPage } from "./pages/TaskDetailPage";
import { TaskListPage } from "./pages/TaskListPage";

type Route = { page: "landing" } | { page: "create" } | { page: "demo" } | { page: "status" } | { page: "tasks" } | { page: "detail"; taskId: string };

function parseRoute(): Route {
  const path = window.location.pathname;
  const pathMatch = path.match(/^\/tasks\/([^/]+)$/);
  if (pathMatch) return { page: "detail", taskId: decodeURIComponent(pathMatch[1]) };
  if (path === "/tasks") return { page: "tasks" };
  if (path === "/demo") return { page: "demo" };
  if (path === "/settings/status") return { page: "status" };
  if (path === "/app") return { page: "create" };

  const hash = window.location.hash.replace(/^#/, "");
  const hashMatch = hash.match(/^\/tasks\/([^/]+)$/);
  if (hashMatch) return { page: "detail", taskId: decodeURIComponent(hashMatch[1]) };
  if (hash === "/tasks") return { page: "tasks" };
  if (hash === "/demo") return { page: "demo" };
  if (hash === "/settings/status") return { page: "status" };
  return { page: "landing" };
}

function navigate(path: string) {
  window.history.pushState(null, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute());

  useEffect(() => {
    const onRouteChange = () => setRoute(parseRoute());
    window.addEventListener("popstate", onRouteChange);
    window.addEventListener("hashchange", onRouteChange);
    return () => {
      window.removeEventListener("popstate", onRouteChange);
      window.removeEventListener("hashchange", onRouteChange);
    };
  }, []);

  if (route.page === "landing") {
    return <LandingPage onCreateTask={() => navigate("/app")} onStartDemo={() => navigate("/demo")} onOpenTasks={() => navigate("/tasks")} onOpenStatus={() => navigate("/settings/status")} />;
  }
  if (route.page === "demo") {
    return <DemoGalleryPage onBack={() => navigate("/")} onCreateTask={() => navigate("/app")} onOpenTask={(taskId) => navigate(`/tasks/${encodeURIComponent(taskId)}`)} />;
  }
  if (route.page === "status") {
    return <ProviderStatusPage onBack={() => navigate("/")} />;
  }
  if (route.page === "tasks") {
    return <TaskListPage onBackHome={() => navigate("/")} onOpenTask={(taskId) => navigate(`/tasks/${encodeURIComponent(taskId)}`)} onCreateNew={() => navigate("/app")} />;
  }
  if (route.page === "detail") {
    return <TaskDetailPage taskId={route.taskId} onBack={() => navigate("/tasks")} />;
  }
  return <TaskCreatePage onBackHome={() => navigate("/")} onTaskCreated={(taskId) => navigate(`/tasks/${encodeURIComponent(taskId)}`)} onOpenTasks={() => navigate("/tasks")} />;
}

export default App;
