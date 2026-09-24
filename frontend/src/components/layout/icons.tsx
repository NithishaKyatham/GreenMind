import React from "react";

type IconProps = { className?: string };

const base = {
  viewBox: "0 0 24 24",
  fill: "none" as const,
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export const HomeIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M4 11.5 12 4l8 7.5" />
    <path d="M6 10v9a1 1 0 0 0 1 1h3v-6h4v6h3a1 1 0 0 0 1-1v-9" />
  </svg>
);

export const ScanLeafIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M6 13c0-4.5 3.2-8 9-8 1 3.5-.5 7-3 9-2 1.6-4.4 1.9-6 1-1.2-.7-1.9-1.3-2-2Z" />
    <path d="M7 20c1-3 2.6-5.3 5-7" />
    <path d="M4 12h16" strokeDasharray="2 3" />
  </svg>
);

export const HistoryIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M3 12a9 9 0 1 0 3-6.7" />
    <path d="M3 4v4h4" />
    <path d="M12 8v4.5l3 2" />
  </svg>
);

export const ChatIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M4 5.5h16v10H9l-4 3.5v-3.5H4Z" />
    <path d="M8 9.5h8M8 12.5h5" />
  </svg>
);

export const CloudIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M7 17.5a4 4 0 0 1-.5-7.97 5 5 0 0 1 9.6-1.7A4.5 4.5 0 0 1 17.5 17.5H7Z" />
  </svg>
);

export const UserIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <circle cx="12" cy="8" r="3.25" />
    <path d="M5 19.5c1.4-3.4 4-5 7-5s5.6 1.6 7 5" />
  </svg>
);

export const MenuIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M4 6.5h16M4 12h16M4 17.5h16" />
  </svg>
);

export const CloseIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M5 5l14 14M19 5 5 19" />
  </svg>
);

export const LogoutIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M9 5H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h3" />
    <path d="M13 15l4-3-4-3M17 12H9" />
  </svg>
);

export const ShieldIcon: React.FC<IconProps> = ({ className }) => (
  <svg {...base} className={className}>
    <path d="M12 3.5 5 6v6c0 4.5 3 7.3 7 8.5 4-1.2 7-4 7-8.5V6Z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);
