import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Divider,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
  Alert,
  AlertIcon,
  useColorModeValue,
  Icon,
} from '@chakra-ui/react';
import { FaGoogle } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { signIn, signInWithGoogle, error, clearError } = useAuth();
  const navigate = useNavigate();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await signIn(email, password);
      navigate('/');
    } catch {
      // Error is handled by AuthContext
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      await signInWithGoogle();
      navigate('/');
    } catch {
      // Error is handled by AuthContext
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')} py={12}>
      <Container maxW="md">
        <Box
          bg={bgColor}
          p={8}
          borderRadius="xl"
          boxShadow="lg"
          border="1px"
          borderColor={borderColor}
        >
          <Stack spacing={6}>
            <Stack spacing={2} textAlign="center">
              <Heading size="xl">Welcome back</Heading>
              <Text color="gray.500">Sign in to continue learning</Text>
            </Stack>

            {error && (
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                {error}
              </Alert>
            )}

            <Button
              onClick={handleGoogleSignIn}
              isLoading={isLoading}
              size="lg"
              variant="outline"
              leftIcon={<Icon as={FaGoogle as React.ComponentType} />}
            >
              Continue with Google
            </Button>

            <Stack direction="row" align="center">
              <Divider />
              <Text color="gray.500" whiteSpace="nowrap" px={3}>
                or
              </Text>
              <Divider />
            </Stack>

            <form onSubmit={handleSubmit}>
              <Stack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Email</FormLabel>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      clearError();
                    }}
                    placeholder="you@example.com"
                    size="lg"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Password</FormLabel>
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      clearError();
                    }}
                    placeholder="Enter your password"
                    size="lg"
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="blue"
                  size="lg"
                  isLoading={isLoading}
                >
                  Sign In
                </Button>
              </Stack>
            </form>

            <Text textAlign="center" color="gray.500">
              Don't have an account?{' '}
              <Text
                as={RouterLink}
                to="/signup"
                color="blue.500"
                fontWeight="semibold"
                _hover={{ textDecoration: 'underline' }}
              >
                Sign up
              </Text>
            </Text>
          </Stack>
        </Box>
      </Container>
    </Box>
  );
}
