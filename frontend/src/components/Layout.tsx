import { ReactNode } from "react";

import { Sidebar } from "./Sidebar";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-view">{children}</main>
    </div>
  );
}
