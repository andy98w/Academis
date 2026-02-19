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

export default function SignupPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const { signUp, signInWithGoogle, error, clearError } = useAuth();
  const navigate = useNavigate();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);
    try {
      await signUp(email, password, name);
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

  const displayError = localError || error;

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
              <Heading size="xl">Create an account</Heading>
              <Text color="gray.500">Start your learning journey</Text>
            </Stack>

            {displayError && (
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                {displayError}
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
                <FormControl>
                  <FormLabel>Name</FormLabel>
                  <Input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    size="lg"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Email</FormLabel>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      clearError();
                      setLocalError(null);
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
                      setLocalError(null);
                    }}
                    placeholder="At least 6 characters"
                    size="lg"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Confirm Password</FormLabel>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setLocalError(null);
                    }}
                    placeholder="Confirm your password"
                    size="lg"
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="blue"
                  size="lg"
                  isLoading={isLoading}
                >
                  Create Account
                </Button>
              </Stack>
            </form>

            <Text textAlign="center" color="gray.500">
              Already have an account?{' '}
              <Text
                as={RouterLink}
                to="/login"
                color="blue.500"
                fontWeight="semibold"
                _hover={{ textDecoration: 'underline' }}
              >
                Sign in
              </Text>
            </Text>
          </Stack>
        </Box>
      </Container>
    </Box>
  );
}
