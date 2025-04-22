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
import { FaChartLine, FaBook, FaRobot, FaChalkboardTeacher } from 'react-icons/fa';
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
          bg="teal.500"
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

const MacroEconomicsPage: React.FC = () => {
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
          <Box mr={4}><IconWrapper icon={FaChartLine} size={24} color="teal.500" /></Box>
          <Box>
            <Heading as="h1" size="xl" color="teal.600">
              AP Macroeconomics
            </Heading>
            <Text color="gray.600" mt={2}>
              Explore national economies, economic indicators, and government policies.
            </Text>
          </Box>
        </Flex>

        <Box mb={10}>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={10} mb={10}>
            <FeatureCard
              title="Interactive Textbook"
              description="Access complete AP Macroeconomics content organized by units and chapters."
              icon={FaBook}
              onClick={() => navigate('/textbook/macro')}
            />
            
            <FeatureCard
              title="AI Tutor"
              description="Get personalized help and ask questions about any macroeconomics topic."
              icon={FaRobot}
            />
            
            <FeatureCard
              title="Practice Questions"
              description="Test your knowledge with AP-style questions and get instant feedback."
              icon={FaChalkboardTeacher}
            />
          </SimpleGrid>
          
          <Box bg="teal.50" p={6} borderRadius="lg" mb={6}>
            <Heading as="h2" size="lg" mb={4} color="teal.600">
              Welcome to AP Macroeconomics
            </Heading>
            <Text mb={4}>
              This interactive learning platform helps you master AP Macroeconomics concepts through a comprehensive
              textbook, AI-powered tutoring, and practice materials.
            </Text>
            <Text mb={4}>
              To get started, navigate to the textbook section to explore content by unit, or use the chat assistant
              in the bottom right corner to ask specific questions about any macroeconomics topic.
            </Text>
            <HStack spacing={4} mt={4}>
              <Button colorScheme="teal" onClick={() => navigate('/textbook/macro')}>
                View Textbook
              </Button>
              <Button colorScheme="blue" variant="outline">
                Start Practice Quiz
              </Button>
            </HStack>
          </Box>
        </Box>
      </Container>
      
      {/* Floating Chat Interface */}
      <ChatInterface subject="macro" floatingMode={true} defaultOpen={false} />
    </Box>
  );
};

export default MacroEconomicsPage;