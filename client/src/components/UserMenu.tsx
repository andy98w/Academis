import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Icon,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Text,
  HStack,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaUser, FaSignOutAlt, FaCog } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

export default function UserMenu() {
  const { user, loading, signOut } = useAuth();
  const navigate = useNavigate();

  const menuBg = useColorModeValue('white', 'gray.800');
  const menuBorder = useColorModeValue('gray.200', 'gray.700');

  if (loading) {
    return (
      <Box w="40px" h="40px" borderRadius="full" bg="gray.200" />
    );
  }

  if (!user) {
    return (
      <HStack spacing={2}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/login')}
        >
          Sign In
        </Button>
        <Button
          colorScheme="blue"
          size="sm"
          onClick={() => navigate('/signup')}
        >
          Sign Up
        </Button>
      </HStack>
    );
  }

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const displayName = user.displayName || user.email?.split('@')[0] || 'User';
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <Menu>
      <MenuButton
        as={Button}
        variant="ghost"
        p={0}
        minW="auto"
        borderRadius="full"
        _hover={{ opacity: 0.8 }}
      >
        <Avatar
          size="sm"
          name={displayName}
          src={user.photoURL || undefined}
          bg="blue.500"
          color="white"
        >
          {!user.photoURL && initials}
        </Avatar>
      </MenuButton>
      <MenuList
        bg={menuBg}
        borderColor={menuBorder}
        boxShadow="lg"
        py={2}
      >
        <Box px={4} py={2}>
          <Text fontWeight="semibold">{displayName}</Text>
          <Text fontSize="sm" color="gray.500">
            {user.email}
          </Text>
        </Box>
        <MenuDivider />
        <MenuItem
          icon={<Icon as={FaUser as React.ComponentType} />}
          onClick={() => navigate('/profile')}
        >
          Profile
        </MenuItem>
        <MenuItem
          icon={<Icon as={FaCog as React.ComponentType} />}
          onClick={() => navigate('/profile')}
        >
          Settings
        </MenuItem>
        <MenuDivider />
        <MenuItem
          icon={<Icon as={FaSignOutAlt as React.ComponentType} />}
          onClick={handleSignOut}
          color="red.500"
        >
          Sign Out
        </MenuItem>
      </MenuList>
    </Menu>
  );
}
