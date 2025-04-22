import React from 'react';
import {
  Box,
  Container,
  SimpleGrid,
  VStack,
  Heading,
  Text,
  Button,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaChartLine, FaShoppingCart } from 'react-icons/fa';
import IconWrapper from '../components/IconWrapper';

interface APClassCardProps {
  title: string;
  description: string;
  icon: any;
  to: string;
  textbookPath?: string;
}

const APClassCard: React.FC<APClassCardProps> = ({ 
  title, 
  description, 
  icon, 
  to,
  textbookPath 
}) => {
  const navigate = useNavigate();
  
  return (
    <Box
      p={6}
      maxW={'330px'}
      w={'full'}
      bg={'white'}
      boxShadow={'lg'}
      rounded={'lg'}
      pos={'relative'}
      zIndex={1}
      _hover={{
        transform: 'translateY(-5px)',
        boxShadow: 'xl',
      }}
      transition="all 0.3s ease"
    >
      <VStack spacing={4}>
        <IconWrapper icon={icon} size={24} color="blue.500" />
        <Heading fontSize={'2xl'} fontFamily={'body'} fontWeight={500}>
          {title}
        </Heading>
        <Text color={'gray.500'} textAlign="center">
          {description}
        </Text>
        <Button
          colorScheme="blue"
          rounded="full"
          size="md"
          w="full"
          onClick={() => navigate(to)}
        >
          Enter Course
        </Button>
        {textbookPath && (
          <Button
            colorScheme="teal"
            variant="outline"
            rounded="full"
            size="md"
            w="full"
            onClick={() => navigate(textbookPath)}
          >
            View Textbook
          </Button>
        )}
      </VStack>
    </Box>
  );
};

const HomePage: React.FC = () => {
  return (
    <Container maxW={'6xl'} py={10}>
      <Box textAlign="center" mb={16}>
        <Heading
          as="h1"
          size="2xl"
          fontWeight="bold"
          color="blue.600"
          mb={4}
        >
          Academis
        </Heading>
        <Text fontSize="xl" color="gray.600" maxW="2xl" mx="auto">
          Your intelligent AP class assistant powered by AI
        </Text>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={10} justifyItems="center">
        <APClassCard
          title="AP Microeconomics"
          description="Study individual economic behavior, markets, and business decisions."
          icon={FaShoppingCart}
          to="/micro"
          textbookPath="/textbook/micro"
        />
        <APClassCard
          title="AP Macroeconomics"
          description="Explore national economies, economic indicators, and government policies."
          icon={FaChartLine}
          to="/macro"
          textbookPath="/textbook/macro"
        />
      </SimpleGrid>
    </Container>
  );
};

export default HomePage;