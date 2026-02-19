import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Text,
  VStack,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaLock } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

interface SignupPromptModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message?: string;
}

export default function SignupPromptModal({
  isOpen,
  onClose,
  title = 'Sign Up to Continue',
  message = 'Create a free account to access all chapters and track your progress.',
}: SignupPromptModalProps) {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('white', 'gray.800');

  const handleSignUp = () => {
    onClose();
    navigate('/signup');
  };

  const handleSignIn = () => {
    onClose();
    navigate('/login');
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="md">
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent bg={bgColor} mx={4}>
        <ModalHeader textAlign="center" pt={8}>
          <VStack spacing={4}>
            <Icon as={FaLock as React.ComponentType} boxSize={12} color="blue.500" />
            <Text fontSize="xl" fontWeight="bold">
              {title}
            </Text>
          </VStack>
        </ModalHeader>
        <ModalBody textAlign="center" pb={4}>
          <Text color="gray.600">{message}</Text>
        </ModalBody>
        <ModalFooter justifyContent="center" pb={8}>
          <VStack spacing={3} width="100%">
            <Button
              colorScheme="blue"
              size="lg"
              width="100%"
              onClick={handleSignUp}
            >
              Sign Up Free
            </Button>
            <Button
              variant="ghost"
              size="md"
              onClick={handleSignIn}
            >
              Already have an account? Sign In
            </Button>
          </VStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
