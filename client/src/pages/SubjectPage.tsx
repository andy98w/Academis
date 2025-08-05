import React from 'react';
import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  SimpleGrid,
  useColorModeValue,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaBook, FaRobot, FaChalkboardTeacher } from 'react-icons/fa';
import ChatInterface from '../components/ChatInterface';
import IconWrapper, { FeatureCardIcon } from '../components/IconWrapper';
import { getSubjectConfig } from '../config/subjects';

const FeatureCard: React.FC<{
  title: string;
  description: string;
  icon: any;
  onClick?: () => void;
  bgColor: string;
}> = ({ title, description, icon: IconComponent, onClick, bgColor }) => {
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
          bg={bgColor}
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

interface SubjectPageProps {
  subjectId: string;
}

const SubjectPage: React.FC<SubjectPageProps> = ({ subjectId }) => {
  const navigate = useNavigate();
  const subjectConfig = getSubjectConfig(subjectId);

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
          <Box mr={4}>
            <IconWrapper 
              icon={subjectConfig.icon} 
              size={24} 
              color={subjectConfig.colors.primary} 
            />
          </Box>
          <Box>
            <Heading as="h1" size="xl" color={subjectConfig.colors.secondary}>
              {subjectConfig.fullName}
            </Heading>
            <Text color="gray.600" mt={2}>
              {subjectConfig.description}
            </Text>
          </Box>
        </Flex>

        <Box mb={10}>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={10} mb={10}>
            <FeatureCard
              title="Interactive Textbook"
              description={`Access complete ${subjectConfig.fullName} content organized by units and chapters.`}
              icon={FaBook}
              bgColor={subjectConfig.colors.primary}
              onClick={() => navigate(`/textbook/${subjectId}`)}
            />
            
            <FeatureCard
              title="AI Tutor"
              description={`Get personalized help and ask questions about any ${subjectConfig.name.toLowerCase()} topic.`}
              icon={FaRobot}
              bgColor={subjectConfig.colors.primary}
            />
            
            <FeatureCard
              title="Practice Questions"
              description="Test your knowledge with AP-style questions and get instant feedback."
              icon={FaChalkboardTeacher}
              bgColor={subjectConfig.colors.primary}
            />
          </SimpleGrid>
          
          <Box bg={subjectConfig.colors.bg} p={6} borderRadius="lg" mb={6}>
            <Heading as="h2" size="lg" mb={4} color={subjectConfig.colors.secondary}>
              Welcome to {subjectConfig.fullName}
            </Heading>
            <Text mb={4}>
              This interactive learning platform helps you master {subjectConfig.fullName} concepts through a comprehensive
              textbook, AI-powered tutoring, and practice materials.
            </Text>
            <Text mb={4}>
              To get started, navigate to the textbook section to explore content by unit, or use the chat assistant
              in the bottom right corner to ask specific questions about any {subjectConfig.name.toLowerCase()} topic.
            </Text>
            <HStack spacing={4} mt={4}>
              <Button 
                colorScheme={subjectConfig.colors.primary.split('.')[0]} 
                onClick={() => navigate(`/textbook/${subjectId}`)}
              >
                View Textbook
              </Button>
              <Button 
                colorScheme="blue" 
                variant="outline"
              >
                Start Practice Quiz
              </Button>
            </HStack>
          </Box>
        </Box>
      </Container>
      
      {/* Floating Chat Interface */}
      <ChatInterface subject={subjectId} floatingMode={true} defaultOpen={false} />
    </Box>
  );
};

export default SubjectPage;