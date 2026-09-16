import type { FC } from "react";
import { HomeIcon, ScanLeafIcon, HistoryIcon, ChatIcon, CloudIcon } from "./icons";

export interface NavItem {
  to: string;
  labelKey: string;
  icon: FC<{ className?: string }>;
}

// The four primary destinations (brief section 21) — used for the mobile
// bottom nav and as the top group of the desktop sidebar.
export const PRIMARY_NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", labelKey: "nav_dashboard", icon: HomeIcon },
  { to: "/detect", labelKey: "nav_detect", icon: ScanLeafIcon },
  { to: "/history", labelKey: "nav_history", icon: HistoryIcon },
  { to: "/chat", labelKey: "nav_chat", icon: ChatIcon },
];

// Desktop has room for one more destination in the primary rail.
export const DESKTOP_ONLY_NAV_ITEMS: NavItem[] = [
  { to: "/weather", labelKey: "nav_weather", icon: CloudIcon },
];
