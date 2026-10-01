import type {
  ReactNode,
} from "react";

import AuthGuard
  from "@/components/auth/AuthGuard";

import ClientWorkspace
  from "@/components/client/ClientWorkspace";


export default function ClientLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <AuthGuard mode="client">
      <ClientWorkspace>
        {children}
      </ClientWorkspace>
    </AuthGuard>
  );
}