import { createFileRoute, Outlet } from "@tanstack/react-router";

// Auth removed — this layout route is now a plain passthrough. The folder name
// is kept so child route paths (and the generated route tree) stay unchanged.
export const Route = createFileRoute("/_authenticated")({
  ssr: false,
  component: () => <Outlet />,
});
