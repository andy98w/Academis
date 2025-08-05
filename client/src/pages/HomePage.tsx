import React from 'react';
import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  Button,
  VStack,
  SimpleGrid,
  useColorModeValue,
  Center,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaGraduationCap } from 'react-icons/fa';
import IconWrapper, { FeatureCardIcon } from '../components/IconWrapper';
import { getAvailableSubjects } from '../config/subjects';

const SubjectCard: React.FC<{
  title: string;
  description: string;
  icon: any;
  onClick?: () => void;
  primaryColor: string;
  bgColor: string;
}> = ({ title, description, icon: IconComponent, onClick, primaryColor, bgColor }) => {
  return (
    <Box
      p={6}
      shadow="md"
      borderWidth="1px"
      borderRadius="lg"
      bg={useColorModeValue('white', 'gray.700')}
      _hover={{ transform: 'translateY(-5px)', shadow: 'xl' }}
      transition="all 0.3s"
      cursor={onClick ? "pointer" : "default"}
      onClick={onClick}
      height="100%"
    >
      <VStack spacing={4} align="center">
        <Flex
          w={16}
          h={16}
          align="center"
          justify="center"
          color="white"
          rounded="full"
          bg={primaryColor}
          mb={2}
        >
          <FeatureCardIcon icon={IconComponent} size="24px" />
        </Flex>
        <Heading fontSize="xl" textAlign="center">{title}</Heading>
        <Text 
          color={useColorModeValue('gray.600', 'gray.400')}
          textAlign="center"
          fontSize="sm"
        >
          {description}
        </Text>
        <Button
          size="sm"
          colorScheme={primaryColor.split('.')[0]}
          variant="outline"
          onClick={onClick}
        >
          Start Learning
        </Button>
      </VStack>
    </Box>
  );
};

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const subjects = getAvailableSubjects();

  return (
    <Box minH="100vh" bg="gray.50" position="relative">
      <Container maxW="7xl" py={8}>
        {/* Header */}
        <Center mb={12}>
          <VStack spacing={6}>
            <Flex align="center" gap={4}>
              <IconWrapper icon={FaGraduationCap} size={48} color="blue.500" />
              <Heading as="h1" size="2xl" color="gray.800">
                Academis
              </Heading>
            </Flex>
            <Text 
              fontSize="xl" 
              color="gray.600" 
              textAlign="center"
              maxW="2xl"
            >
              Your comprehensive AP learning platform with AI-powered tutoring and interactive textbooks
            </Text>
          </VStack>
        </Center>

        {/* Available Subjects Section */}
        <Box mb={12}>
          <Heading as="h2" size="lg" mb={8} textAlign="center" color="gray.700">
            Choose Your AP Subject
          </Heading>
          <SimpleGrid 
            columns={{ base: 1, sm: 2, md: 3, lg: 5 }} 
            spacing={6}
          >
            {subjects.map((subject) => (
              <SubjectCard
                key={subject.id}
                title={subject.fullName}
                description={subject.description}
                icon={subject.icon}
                primaryColor={subject.colors.primary}
                bgColor={subject.colors.bg}
                onClick={() => navigate(`/subject/${subject.id}`)}
              />
            ))}
          </SimpleGrid>
        </Box>

        {/* Features Section */}
        <Box bg="white" p={8} borderRadius="xl" shadow="md">
          <Heading as="h2" size="lg" mb={6} textAlign="center" color="gray.700">
            Why Choose Academis?
          </Heading>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={8}>
            <VStack spacing={3}>
              <Text fontSize="lg" fontWeight="bold" color="blue.600">
                🤖 AI-Powered Tutoring
              </Text>
              <Text textAlign="center" color="gray.600">
                Get instant, personalized help with our advanced AI tutor that understands your learning needs
              </Text>
            </VStack>
            <VStack spacing={3}>
              <Text fontSize="lg" fontWeight="bold" color="green.600">
                📚 Interactive Textbooks
              </Text>
              <Text textAlign="center" color="gray.600">
                Access comprehensive, college-level content organized by AP curriculum standards
              </Text>
            </VStack>
            <VStack spacing={3}>
              <Text fontSize="lg" fontWeight="bold" color="purple.600">
                🎯 Practice & Assessment
              </Text>
              <Text textAlign="center" color="gray.600">
                Test your knowledge with AP-style questions and track your progress over time
              </Text>
            </VStack>
          </SimpleGrid>
        </Box>

        {/* Coming Soon Section */}
        <Box mt={12} textAlign="center">
          <Text color="gray.500" fontSize="sm">
            More AP subjects coming soon! Currently supporting Economics with Biology, Physics, Chemistry, and more in development.
          </Text>
        </Box>
      </Container>
    </Box>
  );
};

export default HomePage;