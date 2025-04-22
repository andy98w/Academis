import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Text,
  Button,
  Flex,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Divider,
  SimpleGrid,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  useToast,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Icon,
} from '@chakra-ui/react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaBook, FaArrowLeft, FaHome } from 'react-icons/fa';
import axios from 'axios';
import ChatInterface from '../components/ChatInterface';
import IconWrapper from '../components/IconWrapper';

interface Chapter {
  chapter_number: string;
  title: string;
}

interface Unit {
  title: string;
  chapters: Chapter[];
}

interface TextbookTOC {
  type: string;
  units: Record<string, Unit>;
}

interface UnitContent {
  type: string;
  units: Record<string, {
    title: string;
    chapters: Record<string, string[]>;
  }>;
}

interface TextbookPageProps {
  subject: 'micro' | 'macro';
}

const TextbookPage: React.FC<TextbookPageProps> = ({ subject }) => {
  const { unitId, chapterId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableOfContents, setTableOfContents] = useState<TextbookTOC | null>(null);
  const [unitContent, setUnitContent] = useState<UnitContent | null>(null);
  const [chapterContent, setChapterContent] = useState<string[] | null>(null);
  const [showChat, setShowChat] = useState(true);

  // Determine what content to load based on URL params
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // First always get the table of contents
        const tocResponse = await axios.get(`http://localhost:8080/api/textbook/${subject}/toc`);
        setTableOfContents(tocResponse.data);

        // If we have a unitId, fetch that unit's content
        if (unitId) {
          const unitResponse = await axios.get(`http://localhost:8080/api/textbook/${subject}/unit/${unitId}`);
          setUnitContent(unitResponse.data);

          // If we also have a chapterId, find that chapter's content
          if (chapterId && unitResponse.data.units[unitId] && unitResponse.data.units[unitId].chapters) {
            // Find the chapter content
            const chapterTitle = Object.keys(unitResponse.data.units[unitId].chapters)
              .find(title => title.toLowerCase().includes(chapterId.toLowerCase()));
            
            if (chapterTitle) {
              setChapterContent(unitResponse.data.units[unitId].chapters[chapterTitle]);
            } else {
              toast({
                title: 'Chapter not found',
                description: `Could not find chapter "${chapterId}" in Unit ${unitId}`,
                status: 'warning',
                duration: 3000,
                isClosable: true,
              });
            }
          }
        }
      } catch (err) {
        console.error('Error fetching textbook data:', err);
        setError('Failed to load textbook content. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [subject, unitId, chapterId, toast]);

  // Helper function to get a clean unit number for display
  const getUnitNumber = (id: string): number => {
    return parseInt(id, 10);
  };

  // Render breadcrumbs navigation
  const renderBreadcrumbs = () => {
    return (
      <Breadcrumb spacing="8px" separator=">" fontSize="sm" mb={4}>
        <BreadcrumbItem>
          <BreadcrumbLink as={Link} to="/">
            <Flex align="center">
              <IconWrapper icon={FaHome} size={14} />
              <Text ml={1}>Home</Text>
            </Flex>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbItem>
          <BreadcrumbLink as={Link} to={`/textbook/${subject}`}>
            AP {subject === 'micro' ? 'Microeconomics' : 'Macroeconomics'} Textbook
          </BreadcrumbLink>
        </BreadcrumbItem>
        {unitId && tableOfContents?.units[unitId] && (
          <BreadcrumbItem>
            <BreadcrumbLink as={Link} to={`/textbook/${subject}/unit/${unitId}`}>
              Unit {getUnitNumber(unitId)}: {tableOfContents.units[unitId].title}
            </BreadcrumbLink>
          </BreadcrumbItem>
        )}
        {unitId && chapterId && (
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink href="#">{chapterId}</BreadcrumbLink>
          </BreadcrumbItem>
        )}
      </Breadcrumb>
    );
  };

  // Render the table of contents for the textbook
  const renderTableOfContents = () => {
    if (!tableOfContents) return null;

    return (
      <VStack spacing={4} align="stretch" width="100%">
        <Heading as="h2" size="lg" mb={4}>
          AP {subject === 'micro' ? 'Microeconomics' : 'Macroeconomics'} Textbook
        </Heading>
        
        <Text fontSize="md" color="gray.600" mb={4}>
          This textbook covers all the essential concepts and topics for the AP {subject === 'micro' ? 'Microeconomics' : 'Macroeconomics'} exam.
          Select a unit to start learning.
        </Text>

        <Accordion allowMultiple defaultIndex={[]} width="100%">
          {Object.entries(tableOfContents.units)
            .sort(([aId], [bId]) => parseInt(aId) - parseInt(bId))
            .map(([unitId, unit]) => (
              <AccordionItem key={unitId} borderWidth="1px" borderRadius="md" mb={3}>
                <h2>
                  <AccordionButton 
                    _expanded={{ bg: 'blue.50', color: 'blue.700' }}
                    borderRadius="md"
                    py={3}
                  >
                    <Box flex="1" textAlign="left" fontWeight="bold">
                      Unit {getUnitNumber(unitId)}: {unit.title}
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  <VStack align="stretch" spacing={3} pl={2}>
                    {unit.chapters && unit.chapters.map((chapter, idx) => (
                      <Button 
                        key={idx}
                        variant="ghost" 
                        justifyContent="flex-start"
                        leftIcon={<IconWrapper icon={FaBook} size={16} />}
                        onClick={() => navigate(`/textbook/${subject}/unit/${unitId}/chapter/${encodeURIComponent(chapter.title)}`)}
                        py={2}
                        px={4}
                        borderRadius="md"
                        _hover={{ bg: 'blue.50' }}
                      >
                        {chapter.chapter_number && (
                          <Text as="span" fontWeight="bold" mr={2}>
                            {chapter.chapter_number}:
                          </Text>
                        )}
                        {chapter.title}
                      </Button>
                    ))}
                    <Box pt={2}>
                      <Button 
                        colorScheme="blue" 
                        variant="outline" 
                        size="sm"
                        onClick={() => navigate(`/textbook/${subject}/unit/${unitId}`)}
                      >
                        View Full Unit
                      </Button>
                    </Box>
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            ))}
        </Accordion>
      </VStack>
    );
  };

  // Render a specific unit's content
  const renderUnitContent = () => {
    if (!unitContent || !unitId || !unitContent.units[unitId]) return null;
    
    const unit = unitContent.units[unitId];
    
    return (
      <VStack spacing={6} align="stretch" width="100%">
        <Box>
          <Heading as="h2" size="xl">
            Unit {getUnitNumber(unitId)}: {unit.title}
          </Heading>
          <Text color="gray.600" mt={2}>
            AP {subject === 'micro' ? 'Microeconomics' : 'Macroeconomics'}
          </Text>
        </Box>
        
        <Divider />
        
        {/* If we're not looking at a specific chapter, show the chapters list */}
        {!chapterId && (
          <VStack spacing={6} align="stretch">
            <Heading as="h3" size="lg">Chapters</Heading>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              {Object.entries(unit.chapters).map(([title, content], idx) => (
                <Box 
                  key={idx} 
                  p={5} 
                  shadow="md" 
                  borderWidth="1px" 
                  borderRadius="md"
                  bg={bgColor}
                  _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
                  transition="all 0.3s"
                  cursor="pointer"
                  onClick={() => navigate(`/textbook/${subject}/unit/${unitId}/chapter/${encodeURIComponent(title)}`)}
                >
                  <Heading fontSize="xl" mb={2}>
                    {title}
                  </Heading>
                  <Text noOfLines={3} color="gray.600">
                    {content[0].substring(0, 150)}...
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </VStack>
        )}
        
        {/* If we have a chapter to show, display its content */}
        {chapterId && chapterContent && (
          <VStack spacing={6} align="stretch">
            <Heading as="h3" size="lg">{chapterId}</Heading>
            <Box 
              p={6} 
              shadow="md" 
              borderWidth="1px" 
              borderRadius="md"
              bg={bgColor}
            >
              {chapterContent.map((paragraph, idx) => (
                <Text key={idx} mb={4}>
                  {paragraph}
                </Text>
              ))}
            </Box>
          </VStack>
        )}
      </VStack>
    );
  };

  // Toggle the chat visibility
  const toggleChat = () => setShowChat(!showChat);

  return (
    <Box minH="100vh" bg="gray.50" position="relative">
      <Container maxW="6xl" py={6}>
        <Button 
          leftIcon={<IconWrapper icon={FaArrowLeft} size={14} />}
          onClick={() => navigate('/')}
          colorScheme="blue" 
          variant="outline" 
          mb={6}
        >
          Back to Home
        </Button>
        
        {renderBreadcrumbs()}
        
        {loading ? (
          <Flex justify="center" align="center" height="400px" direction="column">
            <Spinner size="xl" mb={4} color="blue.500" />
            <Text>Loading textbook content...</Text>
          </Flex>
        ) : error ? (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        ) : (
          <Box>
            {/* If we have a unit to display, show that; otherwise show TOC */}
            {unitId ? renderUnitContent() : renderTableOfContents()}
          </Box>
        )}
      </Container>
      
      {/* Floating Chat Interface */}
      <ChatInterface 
        subject={subject} 
        floatingMode={true}
        defaultOpen={false}
      />
    </Box>
  );
};

export default TextbookPage;