import React from 'react';
import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  Button,
  VStack,
  Image,
  HStack,
  SimpleGrid,
  useColorModeValue,
  Icon
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaShoppingCart, FaBook, FaRobot, FaChalkboardTeacher } from 'react-icons/fa';
import ChatInterface from '../components/ChatInterface';
import IconWrapper, { renderIcon, FeatureCardIcon } from '../components/IconWrapper';

const FeatureCard: React.FC<{
  title: string;
  description: string;
  icon: any; // Use any to bypass the type checking for icon props
  onClick?: () => void;
}> = ({ title, description, icon: IconComponent, onClick }) => {
  return (
    <Box
      p={5}
      shadow="md"
      borderWidth="1px"
      borderRadius="lg"
      bg={useColorModeValue('white', 'gray.700')}
      _hover={{ transform: 'translateY(-5px)', shadow: 'lg' }}
      transition="all 0.3s"
      cursor={onClick ? "pointer" : "default"}
      onClick={onClick}
      height="100%"
    >
      <VStack spacing={4} align="flex-start">
        <Flex
          w={12}
          h={12}
          align="center"
          justify="center"
          color="white"
          rounded="full"
          bg="blue.500"
          mb={1}
        >
          <FeatureCardIcon icon={IconComponent} />
        </Flex>
        <Heading fontSize="xl">{title}</Heading>
        <Text color={useColorModeValue('gray.600', 'gray.400')}>
          {description}
        </Text>
      </VStack>
    </Box>
  );
};

const MicroEconomicsPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box minH="100vh" bg="gray.50" position="relative">
      <Container maxW="6xl" py={6}>
        <Button 
          onClick={() => navigate('/')}
          colorScheme="blue" 
          variant="outline" 
          mb={6}
        >
          Back to Home
        </Button>

        <Flex direction={{ base: 'column', md: 'row' }} align="center" mb={8}>
          <Box mr={4}><IconWrapper icon={FaShoppingCart} size={24} color="blue.500" /></Box>
          <Box>
            <Heading as="h1" size="xl" color="blue.600">
              AP Microeconomics
            </Heading>
            <Text color="gray.600" mt={2}>
              Study individual economic behavior, markets, and business decisions.
            </Text>
          </Box>
        </Flex>

        <Box mb={10}>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={10} mb={10}>
            <FeatureCard
              title="Interactive Textbook"
              description="Access complete AP Microeconomics content organized by units and chapters."
              icon={FaBook}
              onClick={() => navigate('/textbook/micro')}
            />
            
            <FeatureCard
              title="AI Tutor"
              description="Get personalized help and ask questions about any microeconomics topic."
              icon={FaRobot}
            />
            
            <FeatureCard
              title="Practice Questions"
              description="Test your knowledge with AP-style questions and get instant feedback."
              icon={FaChalkboardTeacher}
            />
          </SimpleGrid>
          
          <Box bg="blue.50" p={6} borderRadius="lg" mb={6}>
            <Heading as="h2" size="lg" mb={4} color="blue.600">
              Welcome to AP Microeconomics
            </Heading>
            <Text mb={4}>
              This interactive learning platform helps you master AP Microeconomics concepts through a comprehensive
              textbook, AI-powered tutoring, and practice materials.
            </Text>
            <Text mb={4}>
              To get started, navigate to the textbook section to explore content by unit, or use the chat assistant
              in the bottom right corner to ask specific questions about any microeconomics topic.
            </Text>
            <HStack spacing={4} mt={4}>
              <Button colorScheme="blue" onClick={() => navigate('/textbook/micro')}>
                View Textbook
              </Button>
              <Button colorScheme="teal" variant="outline">
                Start Practice Quiz
              </Button>
            </HStack>
          </Box>
        </Box>
      </Container>
      
      {/* Floating Chat Interface */}
      <ChatInterface subject="micro" floatingMode={true} defaultOpen={false} />
    </Box>
  );
};

export default MicroEconomicsPage;