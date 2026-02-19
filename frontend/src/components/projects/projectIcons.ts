import {
  Box,
  Briefcase,
  Building2,
  ClipboardList,
  Compass,
  Folder,
  Hammer,
  HardHat,
  Landmark,
  Layers,
  LayoutGrid,
  Map,
  PenTool,
  Ruler,
  Sparkles,
  Wrench,
} from 'lucide-react';

export type ProjectIconKey =
  | 'folder'
  | 'box'
  | 'briefcase'
  | 'building'
  | 'clipboard'
  | 'compass'
  | 'hammer'
  | 'hardhat'
  | 'landmark'
  | 'layers'
  | 'layout'
  | 'map'
  | 'pen'
  | 'ruler'
  | 'sparkles'
  | 'wrench';

export const PROJECT_ICON_OPTIONS: Array<{
  key: ProjectIconKey;
  label: string;
  Icon: typeof Folder;
}> = [
  { key: 'folder', label: 'Folder', Icon: Folder },
  { key: 'box', label: 'Box', Icon: Box },
  { key: 'briefcase', label: 'Briefcase', Icon: Briefcase },
  { key: 'building', label: 'Building', Icon: Building2 },
  { key: 'clipboard', label: 'Clipboard', Icon: ClipboardList },
  { key: 'compass', label: 'Compass', Icon: Compass },
  { key: 'hammer', label: 'Hammer', Icon: Hammer },
  { key: 'hardhat', label: 'Hardhat', Icon: HardHat },
  { key: 'landmark', label: 'Landmark', Icon: Landmark },
  { key: 'layers', label: 'Layers', Icon: Layers },
  { key: 'layout', label: 'Layout', Icon: LayoutGrid },
  { key: 'map', label: 'Map', Icon: Map },
  { key: 'pen', label: 'Pen', Icon: PenTool },
  { key: 'ruler', label: 'Ruler', Icon: Ruler },
  { key: 'sparkles', label: 'Sparkles', Icon: Sparkles },
  { key: 'wrench', label: 'Wrench', Icon: Wrench },
];

const PROJECT_ICON_MAP = PROJECT_ICON_OPTIONS.reduce<Record<string, typeof Folder>>((acc, item) => {
  acc[item.key] = item.Icon;
  return acc;
}, {});

export const getProjectIcon = (key?: string | null) => {
  if (!key) return Folder;
  return PROJECT_ICON_MAP[key] || Folder;
};
