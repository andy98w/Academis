import React from 'react';
import { Box } from '@chakra-ui/react';
import { IconType } from 'react-icons';

// This type allows us to handle both IconType (from react-icons) and generic React.ElementType
type IconComponentType = IconType | React.ElementType;

// Create a wrapper component for icons
const IconWrapper: React.FC<{ icon: IconComponentType; size?: number; color?: string }> = ({ 
  icon: Icon, 
  size = 6,
  color = 'currentColor'
}) => {
  return (
    <Box display="inline-block" color={color}>
      {/* Cast as any to avoid TypeScript errors with createElement */}
      {React.createElement(Icon as any, { size })}
    </Box>
  );
};

// Helper function for conditional icon rendering (useful for IconButton components)
export const renderIcon = (Icon: IconComponentType, props = {}) => {
  // For Chakra UI's IconButton, we need to return the element directly, not a function
  return React.createElement(Icon as any, props);
};

// Create a feature card icon component that works with both IconType and React.ElementType
export const FeatureCardIcon: React.FC<{ icon: any; size?: string }> = ({ 
  icon: Icon,
  size = "20px" 
}) => {
  return React.createElement(Icon, { size });
};

export default IconWrapper;