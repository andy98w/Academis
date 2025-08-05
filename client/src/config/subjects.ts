import { FaShoppingCart, FaChartLine, FaDna, FaAtom, FaFlask } from 'react-icons/fa';
import { IconType } from 'react-icons';

export interface SubjectConfig {
  id: string;
  name: string;
  fullName: string;
  description: string;
  icon: IconType;
  colors: {
    primary: string;
    secondary: string;
    bg: string;
  };
  path: string;
}

export const SUBJECTS: Record<string, SubjectConfig> = {
  micro: {
    id: 'micro',
    name: 'Microeconomics',
    fullName: 'AP Microeconomics',
    description: 'Study individual economic behavior, markets, and business decisions.',
    icon: FaShoppingCart,
    colors: {
      primary: 'blue.500',
      secondary: 'blue.600',
      bg: 'blue.50'
    },
    path: '/micro'
  },
  macro: {
    id: 'macro',
    name: 'Macroeconomics',
    fullName: 'AP Macroeconomics',
    description: 'Explore national economies, economic indicators, and government policies.',
    icon: FaChartLine,
    colors: {
      primary: 'teal.500',
      secondary: 'teal.600',
      bg: 'teal.50'
    },
    path: '/macro'
  },
  biology: {
    id: 'biology',
    name: 'Biology',
    fullName: 'AP Biology',
    description: 'Explore life sciences, cellular processes, genetics, and evolution.',
    icon: FaDna,
    colors: {
      primary: 'green.500',
      secondary: 'green.600',
      bg: 'green.50'
    },
    path: '/biology'
  },
  physics: {
    id: 'physics',
    name: 'Physics',
    fullName: 'AP Physics',
    description: 'Study mechanics, thermodynamics, waves, and modern physics.',
    icon: FaAtom,
    colors: {
      primary: 'purple.500',
      secondary: 'purple.600',
      bg: 'purple.50'
    },
    path: '/physics'
  },
  chemistry: {
    id: 'chemistry',
    name: 'Chemistry',
    fullName: 'AP Chemistry',
    description: 'Understand atomic structure, chemical bonding, and reactions.',
    icon: FaFlask,
    colors: {
      primary: 'orange.500',
      secondary: 'orange.600',
      bg: 'orange.50'
    },
    path: '/chemistry'
  }
};

export const getSubjectConfig = (subjectId: string): SubjectConfig => {
  const config = SUBJECTS[subjectId];
  if (!config) {
    throw new Error(`Subject "${subjectId}" not found`);
  }
  return config;
};

export const getAvailableSubjects = (): SubjectConfig[] => {
  return Object.values(SUBJECTS);
};