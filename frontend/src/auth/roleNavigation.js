import { 
  LayoutDashboard, FolderOpen, Users, Search, Network, 
  BarChart3, AlertTriangle, Bot, FileText, TrendingUp, Globe, User, ShieldCheck, GitMerge
} from 'lucide-react';

export const USER_ROLES = {
  CITIZEN: 'CITIZEN',
  INVESTIGATING_OFFICER: 'INVESTIGATING_OFFICER',
  IPS_OFFICER: 'IPS_OFFICER',
  HOME_MINISTRY: 'HOME_MINISTRY'
};

export const ROLE_DISPLAY_NAMES = {
  [USER_ROLES.CITIZEN]: 'CITIZEN',
  [USER_ROLES.INVESTIGATING_OFFICER]: 'INVESTIGATING OFFICER',
  [USER_ROLES.IPS_OFFICER]: 'IPS OFFICER',
  [USER_ROLES.HOME_MINISTRY]: 'HOME MINISTRY'
};

export const ROLE_BADGE_COLORS = {
  [USER_ROLES.CITIZEN]: 'bg-teal-500/20 text-teal-300 border-teal-500/40',
  [USER_ROLES.INVESTIGATING_OFFICER]: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
  [USER_ROLES.IPS_OFFICER]: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  [USER_ROLES.HOME_MINISTRY]: 'bg-purple-500/20 text-purple-300 border-purple-500/40'
};

export const DEFAULT_ROLE_REDIRECTS = {
  [USER_ROLES.CITIZEN]: '/citizen/dashboard',
  [USER_ROLES.INVESTIGATING_OFFICER]: '/dashboard',
  [USER_ROLES.IPS_OFFICER]: '/dashboard',
  [USER_ROLES.HOME_MINISTRY]: '/ministry/dashboard'
};

/**
 * Returns navigation sections for a given role.
 * Citizen and Home Ministry never see investigator modules.
 */
export function getNavigationForRole(role) {
  switch (role) {
    case USER_ROLES.CITIZEN:
      return [
        {
          title: 'CITIZEN PORTAL',
          items: [
            { name: 'My Dashboard', path: '/citizen/dashboard', icon: LayoutDashboard },
            { name: 'My Cases', path: '/citizen/cases', icon: FolderOpen },
          ]
        },
        {
          title: 'ACCOUNT',
          items: [
            { name: 'Profile & Security', path: '/profile', icon: User },
          ]
        }
      ];

    case USER_ROLES.INVESTIGATING_OFFICER:
      return [
        {
          title: 'COMMAND CENTER',
          items: [
            { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          ]
        },
        {
          title: 'INVESTIGATION',
          items: [
            { name: 'Cases', path: '/cases', icon: FolderOpen },
            { name: 'People', path: '/entities', icon: Users },
            { name: 'Advanced Search', path: '/search', icon: Search },
            { name: 'Network', path: '/network', icon: Network },
            { name: 'Analytics', path: '/analytics', icon: BarChart3 },
            { name: 'Priority Leads', path: '/priority', icon: AlertTriangle },
          ]
        },
        {
          title: 'AI & INTELLIGENCE',
          items: [
            { name: 'Investigation Assistant', path: '/assistant', icon: Bot },
          ]
        },
        {
          title: 'ACCOUNT',
          items: [
            { name: 'Profile', path: '/profile', icon: User },
          ]
        }
      ];

    case USER_ROLES.IPS_OFFICER:
      return [
        {
          title: 'COMMAND CENTER',
          items: [
            { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          ]
        },
        {
          title: 'SUPERVISORY OVERSIGHT',
          items: [
            { name: 'Cross-Case Intelligence', path: '/supervisory/cross-case', icon: GitMerge },
            { name: 'Executive Reports', path: '/supervisory/reports', icon: FileText },
            { name: 'Audit & Compliance', path: '/audit', icon: ShieldCheck },
          ]
        },
        {
          title: 'INVESTIGATION',
          items: [
            { name: 'Cases', path: '/cases', icon: FolderOpen },
            { name: 'People', path: '/entities', icon: Users },
            { name: 'Advanced Search', path: '/search', icon: Search },
            { name: 'Network', path: '/network', icon: Network },
            { name: 'Analytics', path: '/analytics', icon: BarChart3 },
            { name: 'Priority Leads', path: '/priority', icon: AlertTriangle },
          ]
        },
        {
          title: 'AI & INTELLIGENCE',
          items: [
            { name: 'Investigation Assistant', path: '/assistant', icon: Bot },
          ]
        },
        {
          title: 'ACCOUNT',
          items: [
            { name: 'Profile', path: '/profile', icon: User },
          ]
        }
      ];

    case USER_ROLES.HOME_MINISTRY:
      return [
        {
          title: 'NATIONAL OVERSIGHT',
          items: [
            { name: 'Strategic Dashboard', path: '/ministry/dashboard', icon: LayoutDashboard },
            { name: 'Aggregated Analytics', path: '/ministry/analytics', icon: BarChart3 },
            { name: 'Strategic Trends', path: '/ministry/trends', icon: TrendingUp },
            { name: 'Regional Statistics', path: '/ministry/regional', icon: Globe },
            { name: 'Strategic Reports', path: '/ministry/reports', icon: FileText },
            { name: 'Audit & Compliance', path: '/audit', icon: ShieldCheck },
          ]
        },
        {
          title: 'ACCOUNT',
          items: [
            { name: 'Profile', path: '/profile', icon: User },
          ]
        }
      ];

    default:
      return [];
  }
}
