import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Container,
  Divider,
  Heading,
  HStack,
  Icon,
  Stack,
  Text,
  useColorModeValue,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Badge,
} from '@chakra-ui/react';
import { FaSignOutAlt, FaArrowLeft } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const statBg = useColorModeValue('gray.50', 'gray.700');
  const pageBg = useColorModeValue('gray.50', 'gray.900');

  if (!user) {
    navigate('/login');
    return null;
  }

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const displayName = user.displayName || user.email?.split('@')[0] || 'User';
  const memberSince = user.metadata.creationTime
    ? new Date(user.metadata.creationTime).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Unknown';

  return (
    <Box minH="100vh" bg={pageBg} py={8}>
      <Container maxW="4xl">
        <Button
          leftIcon={<Icon as={FaArrowLeft as React.ComponentType} />}
          variant="ghost"
          mb={6}
          onClick={() => navigate(-1)}
        >
          Back
        </Button>

        <Stack spacing={6}>
          {/* Profile Header */}
          <Box
            bg={bgColor}
            p={8}
            borderRadius="xl"
            boxShadow="md"
            border="1px"
            borderColor={borderColor}
          >
            <HStack spacing={6} align="start">
              <Avatar
                size="2xl"
                name={displayName}
                src={user.photoURL || undefined}
                bg="blue.500"
              />
              <Stack spacing={2} flex={1}>
                <HStack>
                  <Heading size="lg">{displayName}</Heading>
                  {user.emailVerified && (
                    <Badge colorScheme="green">Verified</Badge>
                  )}
                </HStack>
                <Text color="gray.500">{user.email}</Text>
                <Text fontSize="sm" color="gray.400">
                  Member since {memberSince}
                </Text>
              </Stack>
              <Button
                leftIcon={<Icon as={FaSignOutAlt as React.ComponentType} />}
                colorScheme="red"
                variant="outline"
                onClick={handleSignOut}
              >
                Sign Out
              </Button>
            </HStack>
          </Box>

          {/* Learning Stats */}
          <Box
            bg={bgColor}
            p={6}
            borderRadius="xl"
            boxShadow="md"
            border="1px"
            borderColor={borderColor}
          >
            <Heading size="md" mb={4}>
              Learning Progress
            </Heading>
            <StatGroup>
              <Stat bg={statBg} p={4} borderRadius="lg">
                <StatLabel>Chapters Completed</StatLabel>
                <StatNumber>0</StatNumber>
              </Stat>
              <Stat bg={statBg} p={4} borderRadius="lg">
                <StatLabel>Quiz Score Average</StatLabel>
                <StatNumber>--%</StatNumber>
              </Stat>
              <Stat bg={statBg} p={4} borderRadius="lg">
                <StatLabel>Study Streak</StatLabel>
                <StatNumber>0 days</StatNumber>
              </Stat>
            </StatGroup>
            <Text fontSize="sm" color="gray.500" mt={4}>
              Start learning to track your progress!
            </Text>
          </Box>

          {/* Account Settings */}
          <Box
            bg={bgColor}
            p={6}
            borderRadius="xl"
            boxShadow="md"
            border="1px"
            borderColor={borderColor}
          >
            <Heading size="md" mb={4}>
              Account Settings
            </Heading>
            <Stack spacing={4}>
              <HStack justify="space-between">
                <Box>
                  <Text fontWeight="medium">Email</Text>
                  <Text fontSize="sm" color="gray.500">
                    {user.email}
                  </Text>
                </Box>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <Box>
                  <Text fontWeight="medium">Sign-in Method</Text>
                  <Text fontSize="sm" color="gray.500">
                    {user.providerData[0]?.providerId === 'google.com'
                      ? 'Google'
                      : 'Email/Password'}
                  </Text>
                </Box>
              </HStack>
            </Stack>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}
