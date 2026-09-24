import React from "react";
import { useAuth } from "../../context/AuthContext";
import TopBar from "./TopBar";
import DesktopSidebar from "./DesktopSidebar";
import MobileBottomNav from "./MobileBottomNav";

const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-earth-50">
      <TopBar />
      <div className="flex-1 flex">
        {user && <DesktopSidebar />}
        <main className={`flex-1 min-w-0 ${user ? "pb-20 md:pb-0" : ""}`}>{children}</main>
      </div>
      {user && <MobileBottomNav />}
    </div>
  );
};

export default AppShell;
