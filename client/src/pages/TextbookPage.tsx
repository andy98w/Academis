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
  UnorderedList,
  ListItem,
} from '@chakra-ui/react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaBook, FaArrowLeft, FaHome, FaCaretDown, FaCaretRight, FaChartLine, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { Image } from '@chakra-ui/react';
import axios from 'axios';
import ChatInterface from '../components/ChatInterface';
import IconWrapper, { renderIcon } from '../components/IconWrapper';
import { getSubjectConfig } from '../config/subjects';

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

interface GraphData {
  type: string;
  image: string;
  title: string;
  description: string;
}

interface UnitContent {
  type: string;
  units: Record<string, {
    title: string;
    chapters: Record<string, string[]>;
    graphs?: Record<string, GraphData | Record<string | number, GraphData>>;
  }>;
}

interface TextbookPageProps {
  subject: string;
}

const TextbookPage: React.FC<TextbookPageProps> = ({ subject }) => {
  const { unitId, chapterId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const solutionsBgColor = useColorModeValue('blue.50', 'blue.900');

  // Get subject configuration
  const subjectConfig = getSubjectConfig(subject);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableOfContents, setTableOfContents] = useState<TextbookTOC | null>(null);
  const [unitContent, setUnitContent] = useState<UnitContent | null>(null);
  const [chapterContent, setChapterContent] = useState<string[] | null>(null);
  const [solutionVisibility, setSolutionVisibility] = useState<{[key: string]: boolean}>({});
  const [reviewQuestions, setReviewQuestions] = useState<{question: string, solution: string, id?: string}[]>([]);

  // Determine what content to load based on URL params
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setReviewQuestions([]);

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
              const content = unitResponse.data.units[unitId].chapters[chapterTitle];
              setChapterContent(content);
              
              // Process review questions and solutions
              const reviewSectionIndex = content.findIndex((para: string) => 
                para.trim().startsWith('## Review Questions') || para.trim().startsWith('## Practice Problems')
              );
              
              if (reviewSectionIndex !== -1) {
                const questionsAndSolutions: Array<{question: string, solution: string, id?: string}> = [];
                
                // Get all paragraphs after the Review Questions header
                const reviewParagraphs: string[] = content.slice(reviewSectionIndex + 1);
                
                // Find where questions start (they should start with "Question" or "Problem")
                let questionStartIndexes: number[] = [];
                reviewParagraphs.forEach((para: string, idx: number) => {
                  if (
                    (para.trim().startsWith('Question') || para.trim().startsWith('Problem')) &&
                    !para.includes('**Solution:**')
                  ) {
                    questionStartIndexes.push(idx);
                  }
                  
                  // Stop at the next major section
                  if (para.trim().startsWith('## ') && idx > 0) {
                    return;
                  }
                });
                
                // Process each question and its solution
                questionStartIndexes.forEach((startIdx: number, idx: number) => {
                  const endIdx = idx < questionStartIndexes.length - 1 
                    ? questionStartIndexes[idx + 1] 
                    : reviewParagraphs.findIndex((p: string, i: number) => i > startIdx && p.trim().startsWith('## '));
                  
                  const sectionEnd = endIdx === -1 ? reviewParagraphs.length : endIdx;
                  const questionAndSolutionText = reviewParagraphs.slice(startIdx, sectionEnd);
                  
                  // Extract the question text
                  const questionText = questionAndSolutionText[0];
                  
                  // Find the solution
                  const solutionStartIdx = questionAndSolutionText.findIndex((p: string) => 
                    p.includes('**Solution:**') || p.match(/^\*\*Solution to (Question|Problem)/)
                  );
                  
                  let solutionText = '';
                  if (solutionStartIdx !== -1) {
                    // Get the solution text and remove the prefix
                    const rawSolution = questionAndSolutionText[solutionStartIdx]
                      .replace(/^\*\*Solution.*?:\*\*\s*/, '')
                      .trim();
                      
                    // Add any additional paragraphs that are part of the solution
                    const solutionParts: string[] = [rawSolution];
                    for (let i = solutionStartIdx + 1; i < questionAndSolutionText.length; i++) {
                      // Stop if we hit another solution marker or a specific pattern
                      if (
                        questionAndSolutionText[i].includes('**Solution:**') || 
                        questionAndSolutionText[i].match(/^\*\*Solution to (Question|Problem)/) ||
                        questionAndSolutionText[i].trim().startsWith('Question') ||
                        questionAndSolutionText[i].trim().startsWith('Problem')
                      ) {
                        break;
                      }
                      solutionParts.push(questionAndSolutionText[i].trim());
                    }
                    solutionText = solutionParts.join(' ');
                  }
                  
                  // Add this question and solution to our results
                  questionsAndSolutions.push({
                    question: questionText,
                    solution: solutionText,
                    id: `question-${questionsAndSolutions.length}`
                  });
                });
                
                console.log('Processed review questions:', questionsAndSolutions);
                setReviewQuestions(questionsAndSolutions);
              }
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

  // Helper function to get all chapters in order
  const getAllChaptersInOrder = () => {
    if (!tableOfContents?.units) return [];
    
    const chapters: { unitId: string, chapterTitle: string, chapterNumber: string }[] = [];
    
    // Sort units by number and iterate through chapters
    Object.entries(tableOfContents.units)
      .sort(([aId], [bId]) => parseInt(aId) - parseInt(bId))
      .forEach(([unitId, unit]) => {
        if (unit.chapters && Array.isArray(unit.chapters)) {
          unit.chapters.forEach((chapter) => {
            chapters.push({
              unitId,
              chapterTitle: chapter.title,
              chapterNumber: chapter.chapter_number
            });
          });
        }
      });
    
    return chapters;
  };

  // Helper function to get current chapter index
  const getCurrentChapterIndex = () => {
    if (!chapterId) return -1;
    const allChapters = getAllChaptersInOrder();
    return allChapters.findIndex(chapter => 
      chapter.chapterTitle.toLowerCase().includes(chapterId.toLowerCase()) ||
      chapterId.toLowerCase().includes(chapter.chapterTitle.toLowerCase())
    );
  };

  // Helper function to get previous chapter
  const getPreviousChapter = () => {
    const allChapters = getAllChaptersInOrder();
    const currentIndex = getCurrentChapterIndex();
    
    if (currentIndex <= 0) return null;
    return allChapters[currentIndex - 1];
  };

  // Helper function to get next chapter
  const getNextChapter = () => {
    const allChapters = getAllChaptersInOrder();
    const currentIndex = getCurrentChapterIndex();
    
    if (currentIndex === -1 || currentIndex >= allChapters.length - 1) return null;
    return allChapters[currentIndex + 1];
  };

  // Navigation functions
  const navigateToPreviousChapter = () => {
    const prevChapter = getPreviousChapter();
    if (prevChapter) {
      navigate(`/textbook/${subject}/unit/${prevChapter.unitId}/chapter/${encodeURIComponent(prevChapter.chapterTitle)}`);
    }
  };

  const navigateToNextChapter = () => {
    const nextChapter = getNextChapter();
    if (nextChapter) {
      navigate(`/textbook/${subject}/unit/${nextChapter.unitId}/chapter/${encodeURIComponent(nextChapter.chapterTitle)}`);
    }
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
{subjectConfig.fullName} Textbook
          </BreadcrumbLink>
        </BreadcrumbItem>
        {unitId && tableOfContents && tableOfContents.units && tableOfContents.units[unitId] && (
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
    if (!tableOfContents || !tableOfContents.units) return null;

    return (
      <VStack spacing={4} align="stretch" width="100%">
        <Heading as="h2" size="lg" mb={4}>
{subjectConfig.fullName} Textbook
        </Heading>
        
        <Text fontSize="md" color="gray.600" mb={4}>
This textbook covers all the essential concepts and topics for the {subjectConfig.fullName} exam.
          Select a unit to start learning.
        </Text>

        <Accordion allowMultiple defaultIndex={[]} width="100%">
          {Object.entries(tableOfContents.units || {})
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
                    {unit.chapters && Array.isArray(unit.chapters) && unit.chapters.map((chapter, idx) => (
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

  // Render graph component
  const renderGraph = (graphData: GraphData) => {
    return (
      <Box mt={6} mb={6} p={4} bg="gray.50" borderRadius="md" borderWidth="1px">
        <HStack mb={3} spacing={2}>
          <IconWrapper icon={FaChartLine} size={20} />
          <Heading as="h5" size="sm">
            {graphData.title || 'Economic Graph'}
          </Heading>
        </HStack>
        {graphData.description && (
          <Text mb={3} fontSize="sm" color="gray.600">
            {graphData.description}
          </Text>
        )}
        <Image 
          src={`data:image/png;base64,${graphData.image}`}
          alt={graphData.title || 'Economic Graph'}
          maxW={{ base: "100%", md: "600px" }}
          height="auto"
          borderRadius="md"
          boxShadow="sm"
          mx="auto"
          display="block"
        />
      </Box>
    );
  };
  
  // Render all graphs for the chapter
  const renderAllChapterGraphs = () => {
    if (!unitContent || !unitId || !chapterId) return null;
    
    const unit = unitContent.units[unitId];
    if (!unit || !unit.graphs) return null;
    
    // Find the chapter key that matches our current chapter
    const chapterKeys = Object.keys(unit.chapters);
    const matchingChapterKey = chapterKeys.find(title => 
      title.toLowerCase().includes(chapterId.toLowerCase())
    );
    
    if (!matchingChapterKey) return null;
    
    // Try to find the chapter number
    let chapterNumber = null;
    const chapterNumMatch = matchingChapterKey.match(/^(\d+\.\d+)/);
    if (chapterNumMatch) {
      chapterNumber = chapterNumMatch[1];
    } else if (chapterId) {
      const chapterIdMatch = chapterId.match(/(\d+\.\d+)/);
      if (chapterIdMatch) {
        chapterNumber = chapterIdMatch[1];
      }
    }
    
    // If no chapter number found, use first available
    if (!chapterNumber && unit.graphs) {
      const availableKeys = Object.keys(unit.graphs);
      if (availableKeys.length > 0) {
        chapterNumber = availableKeys[0];
      }
    }
    
    if (!chapterNumber || !unit.graphs[chapterNumber]) return null;
    
    const chapterGraphs = unit.graphs[chapterNumber];
    
    // Check if this is the new multi-graph format (has 'main' or numeric keys)
    if (typeof chapterGraphs === 'object' && !(chapterGraphs as GraphData).type) {
      // New format: graphs stored by paragraph index or 'main'
      const graphsMap = chapterGraphs as Record<string | number, GraphData>;
      const graphElements: React.ReactElement[] = [];
      
      // Add all graphs from the map
      Object.entries(graphsMap).forEach(([key, graph]) => {
        graphElements.push(
          <Box key={key}>
            {renderGraph(graph)}
          </Box>
        );
      });
      
      return <>{graphElements}</>;
    } else {
      // Old format: single graph object
      const graphData = chapterGraphs as GraphData;
      return renderGraph(graphData);
    }
  };
  
  // Get graph for a specific paragraph index
  const getGraphForParagraph = (paragraphIndex: number) => {
    if (!unitContent || !unitId || !chapterId) return null;
    
    const unit = unitContent.units[unitId];
    if (!unit || !unit.graphs) {
      console.log('No graphs in unit');
      return null;
    }
    
    // Find the chapter key that matches our current chapter
    const chapterKeys = Object.keys(unit.chapters);
    const matchingChapterKey = chapterKeys.find(title => 
      title.toLowerCase().includes(chapterId.toLowerCase())
    );
    
    if (!matchingChapterKey) return null;
    
    // Try to find the chapter number
    let chapterNumber = null;
    const chapterNumMatch = matchingChapterKey.match(/^(\d+\.\d+)/);
    if (chapterNumMatch) {
      chapterNumber = chapterNumMatch[1];
    } else if (chapterId) {
      const chapterIdMatch = chapterId.match(/(\d+\.\d+)/);
      if (chapterIdMatch) {
        chapterNumber = chapterIdMatch[1];
      }
    }
    
    // If no chapter number found, use first available
    if (!chapterNumber && unit.graphs) {
      const availableKeys = Object.keys(unit.graphs);
      if (availableKeys.length > 0) {
        chapterNumber = availableKeys[0];
      }
    }
    
    if (!chapterNumber || !unit.graphs[chapterNumber]) {
      console.log('No graph for chapter number:', chapterNumber, 'Available:', Object.keys(unit.graphs));
      return null;
    }
    
    const chapterGraphs = unit.graphs[chapterNumber];
    console.log('Chapter graphs:', chapterGraphs);
    
    // Check if this is the new multi-graph format (has 'main' or numeric keys)
    if (typeof chapterGraphs === 'object' && !(chapterGraphs as GraphData).type) {
      // New format: graphs stored by paragraph index or 'main'
      const graphsMap = chapterGraphs as Record<string | number, GraphData>;
      
      // First check for paragraph-specific graph
      if (graphsMap[paragraphIndex]) {
        console.log('Found graph for paragraph index:', paragraphIndex);
        return graphsMap[paragraphIndex];
      }
      
      // If there's a 'main' graph, find the first paragraph with graph keywords
      if (graphsMap['main'] && chapterContent) {
        // Find the first paragraph that mentions graph-related keywords
        let firstGraphParagraph = -1;
        for (let i = 0; i < chapterContent.length; i++) {
          const para = chapterContent[i].toLowerCase();
          if (para.includes('graph') || 
              para.includes('curve') ||
              para.includes('visualized') ||
              para.includes('illustrated') ||
              para.includes('diagram') ||
              para.includes('chart') ||
              para.includes('model') ||
              para.includes('ppf') ||
              para.includes('trade-off')) {
            firstGraphParagraph = i;
            break;
          }
        }
        
        // Only show the graph at the first paragraph that mentions it
        if (firstGraphParagraph === paragraphIndex) {
          console.log('Showing main graph at paragraph', paragraphIndex);
          return graphsMap['main'];
        }
      }
      
      return null;
    } else {
      // Old format: single graph object
      const graphData = chapterGraphs as GraphData;
      // For backwards compatibility with old format, look for generic graph/visualization keywords
      if (chapterContent && chapterContent[paragraphIndex]) {
        const paragraph = chapterContent[paragraphIndex].toLowerCase();
        // Look for generic visualization/graph mentions
        if (paragraph.includes('graph') || 
            paragraph.includes('curve') ||
            paragraph.includes('visualized') ||
            paragraph.includes('illustrated') ||
            paragraph.includes('diagram') ||
            paragraph.includes('chart') ||
            paragraph.includes('model')) {
          console.log('Found graph keyword in paragraph', paragraphIndex);
          return graphData;
        }
      }
    }
    
    return null;
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
{subjectConfig.fullName}
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
              {/* Regular content */}
              {chapterContent.map((paragraph, idx) => {
                // Get the index of the Review Questions section
                const reviewSectionIdx = chapterContent.findIndex(p => 
                  p.trim().startsWith('## Review Questions') || p.trim().startsWith('## Practice Problems')
                );
                
                // Skip review questions section and all content after it
                if (reviewSectionIdx !== -1 && idx >= reviewSectionIdx) {
                  return null;
                }
                // Check if the paragraph is a section heading (starts with ##)
                if (paragraph.trim().startsWith('## ')) {
                  const headingText = paragraph.trim().substring(3);
                  
                  // Special styling for Introduction heading
                  if (headingText === 'Introduction') {
                    return (
                      <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4} key={idx} color="blue.600">
                        {headingText}
                      </Heading>
                    );
                  }
                  
                  // Special styling for Conclusion heading
                  if (headingText === 'Conclusion') {
                    return (
                      <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4} key={idx} color="green.600">
                        {headingText}
                      </Heading>
                    );
                  }
                  
                  // Economic Analysis and Models - display all graphs after this section
                  if (headingText === 'Economic Analysis and Models') {
                    return (
                      <React.Fragment key={idx}>
                        <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4}>
                          {headingText}
                        </Heading>
                        {renderAllChapterGraphs()}
                      </React.Fragment>
                    );
                  }
                  
                  // Still convert graph sections to regular headings
                  if (headingText.startsWith('Graph: ')) {
                    return (
                      <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4} key={idx}>
                        {headingText}
                      </Heading>
                    );
                  }
                  
                  // Regular heading
                  return (
                    <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4} key={idx}>
                      {headingText}
                    </Heading>
                  );
                }
                // Check if paragraph is a horizontal rule
                else if (paragraph.trim() === '---') {
                  return <Divider key={idx} my={4} />;
                }
                // Check if paragraph is a bullet point list
                else if (paragraph.trim().match(/^\* /m)) {
                  const listItems = paragraph.split(/^\* /m).filter(item => item.trim());
                  return (
                    <UnorderedList key={idx} mb={4} pl={4} spacing={2}>
                      {listItems.map((item, itemIdx) => (
                        <ListItem key={itemIdx}>
                          {item.split(/(\*\*[^*]+\*\*)/g).map((part, partIdx) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              return <Text as="span" fontWeight="bold" color="blue.700" key={partIdx}>{part.slice(2, -2)}</Text>;
                            }
                            return part;
                          })}
                        </ListItem>
                      ))}
                    </UnorderedList>
                  );
                }
                // Check if it's a solution paragraph for in-text examples
                else if (paragraph.trim().startsWith('**Solution:**') || paragraph.trim().match(/^\*\*Solution to (Problem|Example) \d+:/)) {
                  const solutionId = `solution-${idx}`;
                  const solutionText = paragraph.replace(/^\*\*Solution.*?:\*\*\s*/, '');
                  
                  return (
                    <Box key={idx} mb={4}>
                      <Button 
                        size="sm" 
                        onClick={() => setSolutionVisibility(prev => ({
                          ...prev, 
                          [solutionId]: !prev[solutionId]
                        }))}
                        variant="outline"
                        colorScheme="blue"
                        mb={2}
                        rightIcon={solutionVisibility[solutionId] ? renderIcon(FaCaretDown) : renderIcon(FaCaretRight)}
                      >
                        {solutionVisibility[solutionId] ? "Hide Solution" : "Show Solution"}
                      </Button>
                      {solutionVisibility[solutionId] && (
                        <Box p={4} bg={solutionsBgColor} borderRadius="md" mt={2}>
                          <Text fontStyle="italic" fontWeight="medium">Solution:</Text>
                          <Text mt={2}>
                            {solutionText.split(/(\*\*[^*]+\*\*)/g).map((part, partIdx) => {
                              if (part.startsWith('**') && part.endsWith('**')) {
                                return <Text as="span" fontWeight="bold" color="blue.700" key={partIdx}>{part.slice(2, -2)}</Text>;
                              }
                              return part;
                            })}
                          </Text>
                        </Box>
                      )}
                    </Box>
                  );
                }
                // For normal paragraphs, replace markdown-style bold with actual bold text
                else {
                  // Convert markdown bold (**text**) to React components
                  const parts = paragraph.split(/(\*\*[^*]+\*\*)/g);
                  
                  // Check if this paragraph is part of Introduction or Conclusion
                  const introHeadingIndex = chapterContent.findIndex(p => p.trim() === '## Introduction');
                  const nextHeadingAfterIntroIndex = chapterContent.findIndex((p, i) => 
                    i > introHeadingIndex && p.trim().startsWith('## ') && !p.includes('Introduction')
                  );
                  
                  const conclusionHeadingIndex = chapterContent.findIndex(p => p.trim() === '## Conclusion');
                  const reviewQuestionsIndex = chapterContent.findIndex(p => p.trim() === '## Review Questions');
                  
                  const isIntroductionParagraph = 
                    introHeadingIndex !== -1 && 
                    nextHeadingAfterIntroIndex !== -1 &&
                    chapterContent.indexOf(paragraph) > introHeadingIndex && 
                    chapterContent.indexOf(paragraph) < nextHeadingAfterIntroIndex;
                  
                  const isConclusionParagraph = 
                    conclusionHeadingIndex !== -1 &&
                    chapterContent.indexOf(paragraph) > conclusionHeadingIndex && 
                    (reviewQuestionsIndex === -1 || chapterContent.indexOf(paragraph) < reviewQuestionsIndex);
                  
                  
                  // Special styling for Introduction and Conclusion paragraphs
                  if (isIntroductionParagraph) {
                    return (
                      <React.Fragment key={idx}>
                        <Text mb={4} borderLeft="4px solid" borderColor="blue.100" pl={3} bg="blue.50" p={2} borderRadius="md">
                          {parts.map((part, partIdx) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              return <Text as="span" fontWeight="bold" color="blue.700" key={partIdx}>{part.slice(2, -2)}</Text>;
                            }
                            return part;
                          })}
                        </Text>
                      </React.Fragment>
                    );
                  } else if (isConclusionParagraph) {
                    return (
                      <React.Fragment key={idx}>
                        <Text mb={4} borderLeft="4px solid" borderColor="green.100" pl={3} bg="green.50" p={2} borderRadius="md">
                          {parts.map((part, partIdx) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              return <Text as="span" fontWeight="bold" color="green.700" key={partIdx}>{part.slice(2, -2)}</Text>;
                            }
                            return part;
                          })}
                        </Text>
                      </React.Fragment>
                    );
                  }
                  
                  // Regular paragraph styling
                  return (
                    <React.Fragment key={idx}>
                      <Text mb={4}>
                        {parts.map((part, partIdx) => {
                          if (part.startsWith('**') && part.endsWith('**')) {
                            return <Text as="span" fontWeight="bold" color="blue.700" key={partIdx}>{part.slice(2, -2)}</Text>;
                          }
                          return part;
                        })}
                      </Text>
                    </React.Fragment>
                  );
                }
              })}
              {renderReviewQuestions()}
            </Box>
          </VStack>
        )}
      </VStack>
    );
  };

  // Render the review questions section
  const renderReviewQuestions = () => {
    if (reviewQuestions.length === 0) return null;
    
    return (
      <Box mt={8}>
        <Heading as="h4" size="md" mb={6}>Review Questions</Heading>
        
        <VStack spacing={6} align="stretch">
          {reviewQuestions.map((item: {question: string, solution: string, id?: string}, idx: number) => (
            <Box key={idx} p={4} borderWidth="1px" borderRadius="md" borderColor="gray.200">
              <Text mb={3}>{item.question}</Text>
              
              <Button 
                size="sm" 
                onClick={() => setSolutionVisibility(prev => ({
                  ...prev, 
                  [item.id || `question-${idx}`]: !prev[item.id || `question-${idx}`]
                }))}
                variant="outline"
                colorScheme="blue"
                rightIcon={solutionVisibility[item.id || `question-${idx}`] ? renderIcon(FaCaretDown) : renderIcon(FaCaretRight)}
              >
                {solutionVisibility[item.id || `question-${idx}`] ? "Hide Solution" : "Show Solution"}
              </Button>
              
              {solutionVisibility[item.id || `question-${idx}`] && (
                <Box p={4} bg={solutionsBgColor} borderRadius="md" mt={3}>
                  <Text fontStyle="italic" fontWeight="medium">Solution:</Text>
                  <Text mt={2}>
                    {item.solution.split(/(\*\*[^*]+\*\*)/g).map((part: string, partIdx: number) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <Text as="span" fontWeight="bold" color="blue.700" key={partIdx}>{part.slice(2, -2)}</Text>;
                      }
                      return part;
                    })}
                  </Text>
                </Box>
              )}
            </Box>
          ))}
        </VStack>
      </Box>
    );
  };

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
      
      {/* Floating Navigation Arrows - only show when viewing a specific chapter */}
      {chapterId && (
        <>
          {/* Previous Chapter Arrow */}
          {getPreviousChapter() && (
            <Box
              position="fixed"
              bottom="50%"
              left="20px"
              transform="translateY(50%)"
              zIndex={1000}
            >
              <Button
                onClick={navigateToPreviousChapter}
                colorScheme="blue"
                variant="solid"
                size="lg"
                borderRadius="full"
                boxShadow="lg"
                _hover={{ transform: "scale(1.1)" }}
                transition="all 0.2s"
                p={4}
                minW="auto"
                h="60px"
                w="60px"
              >
                <IconWrapper icon={FaChevronLeft} size={20} />
              </Button>
            </Box>
          )}
          
          {/* Next Chapter Arrow */}
          {getNextChapter() && (
            <Box
              position="fixed"
              bottom="50%"
              right="20px"
              transform="translateY(50%)"
              zIndex={1000}
            >
              <Button
                onClick={navigateToNextChapter}
                colorScheme="blue"
                variant="solid"
                size="lg"
                borderRadius="full"
                boxShadow="lg"
                _hover={{ transform: "scale(1.1)" }}
                transition="all 0.2s"
                p={4}
                minW="auto"
                h="60px"
                w="60px"
              >
                <IconWrapper icon={FaChevronRight} size={20} />
              </Button>
            </Box>
          )}
        </>
      )}

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