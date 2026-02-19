import React, { useState, useEffect, useMemo, useRef } from 'react';
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useDisclosure,
  Badge,
} from '@chakra-ui/react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaBook, FaArrowLeft, FaHome, FaCaretDown, FaCaretRight, FaChartLine, FaChevronLeft, FaChevronRight, FaTable, FaLock } from 'react-icons/fa';
import { Image } from '@chakra-ui/react';
import axios from 'axios';
import ChatInterface from '../components/ChatInterface';
import IconWrapper, { renderIcon } from '../components/IconWrapper';
import { getSubjectConfig } from '../config/subjects';
import { useAuth } from '../context/AuthContext';
import SignupPromptModal from '../components/SignupPromptModal';

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
  image?: string;
  title: string;
  description: string;
  columns?: string[];
  rows?: string[][];
}

interface UnitContent {
  type: string;
  units: Record<string, {
    title: string;
    chapters: Record<string, string[]>;
    graphs?: Record<string, GraphData | Record<string | number, GraphData>>;
    quiz?: Record<string, QuizQuestion[]>;
  }>;
}

interface QuizQuestion {
  type: 'text' | 'table' | 'graph';
  question: string;
  options: string[];
  correct: number;
  explanation: string;
  table?: {
    title: string;
    columns: string[];
    rows: string[][];
  };
  graph?: {
    spec: any;
    image?: string;
  };
}

interface TextbookPageProps {
  subject: string;
}

const TextbookPage: React.FC<TextbookPageProps> = ({ subject }) => {
  const { unitId, chapterId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { user } = useAuth();
  const { isOpen: isSignupModalOpen, onOpen: openSignupModal, onClose: closeSignupModal } = useDisclosure();
  const [signupModalMessage, setSignupModalMessage] = useState('Create a free account to access all chapters and track your progress.');

  const bgColor = useColorModeValue('white', 'gray.800');
  const solutionsBgColor = useColorModeValue('blue.50', 'blue.900');
  const quizBgColor = useColorModeValue('purple.50', 'purple.900');
  const correctBgColor = useColorModeValue('green.100', 'green.800');
  const incorrectBgColor = useColorModeValue('red.100', 'red.800');

  // Get subject configuration
  const subjectConfig = getSubjectConfig(subject);

  // Free chapters: 1.1 and 1.2 only
  const FREE_CHAPTER_LIMIT = 1.2;
  const MAX_FREE_QUIZ_ANSWERS = 5;

  // Check if a chapter number is locked (requires signup)
  const isChapterLocked = (chapterNumber: string): boolean => {
    if (user) return false; // Authenticated users have full access
    const num = parseFloat(chapterNumber);
    return !isNaN(num) && num > FREE_CHAPTER_LIMIT;
  };

  // Get total quiz answers submitted (for limiting free users)
  const getTotalQuizAnswersSubmitted = (): number => {
    return Object.keys(quizSubmitted).filter(key => quizSubmitted[parseInt(key)]).length;
  };

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableOfContents, setTableOfContents] = useState<TextbookTOC | null>(null);
  const [unitContent, setUnitContent] = useState<UnitContent | null>(null);
  const [chapterContent, setChapterContent] = useState<string[] | null>(null);
  const [solutionVisibility, setSolutionVisibility] = useState<{[key: string]: boolean}>({});
  const [reviewQuestions, setReviewQuestions] = useState<{question: string, solution: string, id?: string}[]>([]);

  // Quiz state
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);
  const [quizAnswers, setQuizAnswers] = useState<{[key: number]: number}>({});
  const [quizSubmitted, setQuizSubmitted] = useState<{[key: number]: boolean}>({});

  // Generate storage key for quiz state
  const getQuizStorageKey = () => `quiz_${subject}_${unitId}_${chapterId}`;

  // Load quiz state from localStorage when chapter changes
  useEffect(() => {
    if (chapterId && unitId) {
      const storageKey = getQuizStorageKey();
      const savedState = localStorage.getItem(storageKey);
      if (savedState) {
        try {
          const { answers, submitted } = JSON.parse(savedState);
          setQuizAnswers(answers || {});
          setQuizSubmitted(submitted || {});
        } catch (e) {
          console.error('Error loading quiz state:', e);
        }
      }
    }
  }, [subject, unitId, chapterId]);

  // Save quiz state to localStorage when it changes
  useEffect(() => {
    if (chapterId && unitId && (Object.keys(quizAnswers).length > 0 || Object.keys(quizSubmitted).length > 0)) {
      const storageKey = getQuizStorageKey();
      localStorage.setItem(storageKey, JSON.stringify({
        answers: quizAnswers,
        submitted: quizSubmitted
      }));
    }
  }, [quizAnswers, quizSubmitted, subject, unitId, chapterId]);

  // Reset quiz progress
  const resetQuiz = () => {
    setQuizAnswers({});
    setQuizSubmitted({});
    const storageKey = getQuizStorageKey();
    localStorage.removeItem(storageKey);
  };

  // Scroll position persistence
  const getScrollStorageKey = () => `scroll_${subject}_${unitId}_${chapterId || 'overview'}`;

  // Save scroll position before navigating away
  useEffect(() => {
    const saveScrollPosition = () => {
      const storageKey = getScrollStorageKey();
      localStorage.setItem(storageKey, String(window.scrollY));
    };

    // Save on scroll (debounced via the browser)
    window.addEventListener('beforeunload', saveScrollPosition);

    // Save when component unmounts (navigation)
    return () => {
      saveScrollPosition();
      window.removeEventListener('beforeunload', saveScrollPosition);
    };
  }, [subject, unitId, chapterId]);

  // Restore scroll position after content loads
  useEffect(() => {
    if (!loading) {
      const storageKey = getScrollStorageKey();
      const savedPosition = localStorage.getItem(storageKey);
      if (savedPosition) {
        // Small delay to ensure DOM is rendered
        setTimeout(() => {
          window.scrollTo(0, parseInt(savedPosition, 10));
        }, 100);
      }
    }
  }, [loading, subject, unitId, chapterId]);

  // Cache: TOC per subject, chapter data per chapter key
  const tocCache = useRef<Record<string, TextbookTOC>>({});
  const chapterCache = useRef<Record<string, UnitContent>>({});

  // Determine what content to load based on URL params
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setReviewQuestions([]);

      try {
        // Get TOC (cached per subject)
        let tocData: TextbookTOC;
        if (tocCache.current[subject]) {
          tocData = tocCache.current[subject];
        } else {
          const tocResponse = await axios.get(`http://localhost:8080/api/textbook/${subject}/toc`);
          tocData = tocResponse.data;
          tocCache.current[subject] = tocData;
        }
        setTableOfContents(tocData);

        // Check if trying to access a locked chapter via direct URL
        if (chapterId && unitId && !user) {
          const tocChapter = tocData.units?.[unitId]?.chapters?.find(
            (ch: Chapter) => ch.title.toLowerCase() === decodeURIComponent(chapterId).toLowerCase()
          );
          if (tocChapter && isChapterLocked(tocChapter.chapter_number)) {
            setSignupModalMessage('Sign up to unlock this chapter and access all content.');
            openSignupModal();
            navigate(`/textbook/${subject}`);
            setLoading(false);
            return;
          }
        }

        // If we have a unitId, fetch content
        if (unitId) {
          let responseData: UnitContent;

          if (chapterId) {
            // Fetch only the specific chapter (much smaller payload)
            const cacheKey = `${subject}/${unitId}/${chapterId}`;
            if (chapterCache.current[cacheKey]) {
              responseData = chapterCache.current[cacheKey];
            } else {
              const chapterResponse = await axios.get(
                `http://localhost:8080/api/textbook/${subject}/unit/${unitId}/chapter/${encodeURIComponent(chapterId)}`
              );
              responseData = chapterResponse.data;
              chapterCache.current[cacheKey] = responseData;
            }
          } else {
            // Fetch whole unit (unit overview, no specific chapter)
            const unitResponse = await axios.get(`http://localhost:8080/api/textbook/${subject}/unit/${unitId}`);
            responseData = unitResponse.data;
          }

          setUnitContent(responseData);

          // If we also have a chapterId, find that chapter's content
          if (chapterId && responseData.units[unitId] && responseData.units[unitId].chapters) {
            // Find the chapter content (exact match, case-insensitive)
            const decodedChapterId = decodeURIComponent(chapterId).toLowerCase();
            const chapterTitle = Object.keys(responseData.units[unitId].chapters)
              .find(title => title.toLowerCase() === decodedChapterId);

            if (chapterTitle) {
              const content = responseData.units[unitId].chapters[chapterTitle];
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

                setReviewQuestions(questionsAndSolutions);
              }

              // Get quiz questions from chapter data
              const chapterNum = tocData?.units?.[parseInt(unitId)]?.chapters?.find(
                (ch: Chapter) => ch.title.toLowerCase() === decodedChapterId
              )?.chapter_number;

              if (chapterNum) {
                const quizData = responseData.units[unitId]?.quiz?.[chapterNum];
                if (quizData) {
                  setQuizQuestions(quizData);
                } else {
                  setQuizQuestions([]);
                }
              } else {
                setQuizQuestions([]);
              }
              // Quiz state is loaded from localStorage via useEffect
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
  }, [subject, unitId, chapterId, toast, tableOfContents]);

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
    const decodedChapterId = decodeURIComponent(chapterId).toLowerCase();
    // Use exact match to avoid substring collisions (e.g., "Demand" matching "Demand and Supply for Factors")
    return allChapters.findIndex(chapter =>
      chapter.chapterTitle.toLowerCase() === decodedChapterId
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

  // Get all unit IDs in order
  const getAllUnitsInOrder = () => {
    if (!tableOfContents?.units) return [];
    return Object.keys(tableOfContents.units)
      .map(id => parseInt(id))
      .sort((a, b) => a - b);
  };

  // Navigation functions
  const navigateToPrevious = () => {
    // If on unit page (no chapter), navigate between units
    if (!chapterId && unitId) {
      const allUnits = getAllUnitsInOrder();
      const currentUnitIndex = allUnits.indexOf(parseInt(unitId));
      if (currentUnitIndex > 0) {
        navigate(`/textbook/${subject}/unit/${allUnits[currentUnitIndex - 1]}`);
      }
      return;
    }

    // Otherwise navigate between chapters
    const prevChapter = getPreviousChapter();
    if (prevChapter) {
      navigate(`/textbook/${subject}/unit/${prevChapter.unitId}/chapter/${encodeURIComponent(prevChapter.chapterTitle)}`);
    }
  };

  const navigateToNext = () => {
    // If on unit page (no chapter), navigate between units
    if (!chapterId && unitId) {
      const allUnits = getAllUnitsInOrder();
      const currentUnitIndex = allUnits.indexOf(parseInt(unitId));
      if (currentUnitIndex < allUnits.length - 1) {
        navigate(`/textbook/${subject}/unit/${allUnits[currentUnitIndex + 1]}`);
      }
      return;
    }

    // Otherwise navigate between chapters
    const nextChapter = getNextChapter();
    if (nextChapter) {
      navigate(`/textbook/${subject}/unit/${nextChapter.unitId}/chapter/${encodeURIComponent(nextChapter.chapterTitle)}`);
    }
  };

  // Check if there's a previous/next item to navigate to
  const hasPrevious = () => {
    if (!chapterId && unitId) {
      const allUnits = getAllUnitsInOrder();
      return allUnits.indexOf(parseInt(unitId)) > 0;
    }
    return getPreviousChapter() !== null;
  };

  const hasNext = () => {
    if (!chapterId && unitId) {
      const allUnits = getAllUnitsInOrder();
      return allUnits.indexOf(parseInt(unitId)) < allUnits.length - 1;
    }
    return getNextChapter() !== null;
  };

  // Keyboard navigation with arrow keys
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle arrow keys when not in an input field
      if (event.target instanceof HTMLInputElement ||
          event.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (event.key === 'ArrowLeft') {
        navigateToPrevious();
      } else if (event.key === 'ArrowRight') {
        navigateToNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [unitContent, chapterId]); // Re-attach when content or chapter changes

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
                    {unit.chapters && Array.isArray(unit.chapters) && unit.chapters.map((chapter, idx) => {
                      const locked = isChapterLocked(chapter.chapter_number);
                      return (
                        <Button
                          key={idx}
                          variant="ghost"
                          justifyContent="flex-start"
                          leftIcon={locked ? <IconWrapper icon={FaLock} size={14} /> : <IconWrapper icon={FaBook} size={16} />}
                          onClick={() => {
                            if (locked) {
                              setSignupModalMessage('Sign up to unlock this chapter and access all content.');
                              openSignupModal();
                            } else {
                              navigate(`/textbook/${subject}/unit/${unitId}/chapter/${encodeURIComponent(chapter.title)}`);
                            }
                          }}
                          py={2}
                          px={4}
                          borderRadius="md"
                          _hover={{ bg: locked ? 'gray.100' : 'blue.50' }}
                          opacity={locked ? 0.7 : 1}
                        >
                          {chapter.chapter_number && (
                            <Text as="span" fontWeight="bold" mr={2}>
                              {chapter.chapter_number}:
                            </Text>
                          )}
                          {chapter.title}
                          {locked && (
                            <Badge ml={2} colorScheme="gray" fontSize="xs">
                              Sign up to unlock
                            </Badge>
                          )}
                        </Button>
                      );
                    })}
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

  // Render graph or table component
  const renderGraph = (graphData: GraphData) => {
    const isTable = graphData.type === 'table' && graphData.columns && graphData.rows;

    return (
      <Box mt={6} mb={6} p={4} bg="gray.50" borderRadius="md" borderWidth="1px">
        <HStack mb={3} spacing={2}>
          <IconWrapper icon={isTable ? FaTable : FaChartLine} size={20} />
          <Heading as="h5" size="sm">
            {graphData.title || 'Visualization'}
          </Heading>
        </HStack>
        {graphData.description && (
          <Text mb={3} fontSize="sm" color="gray.600">
            {graphData.description}
          </Text>
        )}
        {isTable ? (
          <TableContainer>
            <Table variant="striped" colorScheme="blue" size="md">
              <Thead>
                <Tr>
                  {graphData.columns!.map((col, i) => (
                    <Th key={i} bg="blue.500" color="white" fontSize="sm" textTransform="none">
                      {col}
                    </Th>
                  ))}
                </Tr>
              </Thead>
              <Tbody>
                {graphData.rows!.map((row, i) => (
                  <Tr key={i}>
                    {row.map((cell, j) => (
                      <Td key={j} fontSize="sm">{cell}</Td>
                    ))}
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        ) : graphData.image ? (
          <Image
            src={`data:image/png;base64,${graphData.image}`}
            alt={graphData.title || 'Graph'}
            maxW={{ base: "100%", md: "600px" }}
            height="auto"
            borderRadius="md"
            boxShadow="sm"
            mx="auto"
            display="block"
          />
        ) : null}
      </Box>
    );
  };
  
  // Build a map of paragraph index → graph/table data for inline rendering
  const graphsByIndex = useMemo((): Record<number, GraphData> => {
    if (!unitContent || !unitId || !chapterId) return {};

    const unit = unitContent.units[unitId];
    if (!unit || !unit.graphs) return {};

    // Find the chapter number by matching chapterId (title) against the TOC
    let chapterNumber: string | null = null;

    // Method 1: Use TOC to map title → chapter_number
    if (tableOfContents?.units?.[unitId]?.chapters) {
      const tocChapter = tableOfContents.units[unitId].chapters.find(
        (ch: Chapter) => ch.title.toLowerCase() === chapterId.toLowerCase()
      );
      if (tocChapter) {
        chapterNumber = tocChapter.chapter_number;
      }
    }

    // Method 2: Try extracting number from chapterId directly (e.g. "1.2: Title")
    if (!chapterNumber) {
      const numMatch = chapterId.match(/(\d+\.\d+)/);
      if (numMatch) {
        chapterNumber = numMatch[1];
      }
    }

    if (!chapterNumber || !unit.graphs[chapterNumber]) return {};

    const chapterGraphs = unit.graphs[chapterNumber];
    const result: Record<number, GraphData> = {};

    if (typeof chapterGraphs === 'object' && !(chapterGraphs as GraphData).type) {
      // Multi-graph format: keys are paragraph indices
      const graphsMap = chapterGraphs as Record<string | number, GraphData>;
      Object.entries(graphsMap).forEach(([key, graph]) => {
        const idx = parseInt(key, 10);
        if (!isNaN(idx)) {
          result[idx] = graph;
        }
      });
    } else {
      // Old format: single graph — render after paragraph 0
      result[0] = chapterGraphs as GraphData;
    }

    return result;
  }, [unitContent, unitId, chapterId, tableOfContents]);

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
              {(() => {
                return chapterContent.map((paragraph, idx) => {
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
                      <React.Fragment key={idx}>
                        <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4} color="blue.600">
                          {headingText}
                        </Heading>
                        {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                      </React.Fragment>
                    );
                  }

                  // Special styling for Conclusion heading
                  if (headingText === 'Conclusion') {
                    return (
                      <React.Fragment key={idx}>
                        <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4} color="green.600">
                          {headingText}
                        </Heading>
                        {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                      </React.Fragment>
                    );
                  }
                  
                  // Regular heading (including Graph: prefixed)
                  return (
                    <React.Fragment key={idx}>
                      <Heading as="h4" size="md" mt={idx > 0 ? 8 : 0} mb={4}>
                        {headingText}
                      </Heading>
                      {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                    </React.Fragment>
                  );
                }
                // Check for ### subheadings
                else if (paragraph.trim().startsWith('### ')) {
                  const subheadingText = paragraph.trim().substring(4);
                  return (
                    <React.Fragment key={idx}>
                      <Heading as="h5" size="sm" mt={6} mb={3} color="gray.700">
                        {subheadingText}
                      </Heading>
                      {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                    </React.Fragment>
                  );
                }
                // Check if paragraph is a horizontal rule
                else if (paragraph.trim() === '---') {
                  return (
                    <React.Fragment key={idx}>
                      <Divider my={4} />
                      {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                    </React.Fragment>
                  );
                }
                // Check if paragraph is a bullet point list
                else if (paragraph.trim().match(/^\* /m)) {
                  const listItems = paragraph.split(/^\* /m).filter(item => item.trim());
                  return (
                    <React.Fragment key={idx}>
                      <UnorderedList mb={4} pl={4} spacing={2}>
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
                      {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                    </React.Fragment>
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
                        {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
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
                        {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
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
                      {graphsByIndex[idx] && renderGraph(graphsByIndex[idx])}
                    </React.Fragment>
                  );
                }
              });
              })()}
              {renderReviewQuestions()}
              {renderPracticeQuiz()}
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

  // Render practice quiz section
  const renderPracticeQuiz = () => {
    const answeredCount = Object.keys(quizSubmitted).length;
    const correctCount = Object.entries(quizSubmitted).filter(
      ([idx]) => quizAnswers[parseInt(idx)] === quizQuestions[parseInt(idx)]?.correct
    ).length;

    return (
      <Box mt={8} p={6} bg={quizBgColor} borderRadius="md">
        <HStack justify="space-between" mb={6}>
          <Heading as="h4" size="md">Practice Quiz</Heading>
          {quizQuestions.length > 0 && (
            <HStack spacing={4}>
              {answeredCount > 0 && (
                <Text fontSize="sm" color="gray.600">
                  Score: {correctCount}/{answeredCount}
                </Text>
              )}
              <Button
                size="sm"
                variant="outline"
                colorScheme="purple"
                onClick={resetQuiz}
              >
                Reset Quiz
              </Button>
            </HStack>
          )}
        </HStack>

        {/* Free user quiz limit message */}
        {!user && quizQuestions.length > 0 && (
          <Alert status="info" mb={4} borderRadius="md">
            <AlertIcon />
            <Text fontSize="sm">
              {getTotalQuizAnswersSubmitted() >= MAX_FREE_QUIZ_ANSWERS
                ? 'You\'ve used all 5 free practice questions. Sign up to continue!'
                : `Free preview: ${MAX_FREE_QUIZ_ANSWERS - getTotalQuizAnswersSubmitted()} questions remaining. Sign up for unlimited access.`}
            </Text>
          </Alert>
        )}

        {quizQuestions.length === 0 ? (
          <Text color="gray.600">
            No practice quiz available for this chapter yet. Regenerate the chapter to create one.
          </Text>
        ) : (
          <VStack spacing={6} align="stretch">
            {quizQuestions.map((q, idx) => (
              <Box
                key={idx}
                p={4}
                bg="white"
                borderRadius="md"
                borderWidth="1px"
                borderColor={
                  quizSubmitted[idx]
                    ? quizAnswers[idx] === q.correct
                      ? 'green.400'
                      : 'red.400'
                    : 'gray.200'
                }
              >
                <Text fontWeight="bold" mb={3}>Question {idx + 1}</Text>

                {/* Render table if present */}
                {q.type === 'table' && q.table && (
                  <Box mb={4} overflowX="auto">
                    <Text fontWeight="medium" mb={2}>{q.table.title}</Text>
                    <TableContainer>
                      <Table size="sm" variant="simple">
                        <Thead>
                          <Tr>
                            {q.table.columns.map((col, i) => (
                              <Th key={i}>{col}</Th>
                            ))}
                          </Tr>
                        </Thead>
                        <Tbody>
                          {q.table.rows.map((row, i) => (
                            <Tr key={i}>
                              {row.map((cell, j) => (
                                <Td key={j}>{cell}</Td>
                              ))}
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}

                {/* Render graph if present */}
                {q.type === 'graph' && q.graph?.image && (
                  <Box mb={4}>
                    <Image
                      src={`data:image/png;base64,${q.graph.image}`}
                      alt="Question graph"
                      maxW="400px"
                      borderRadius="md"
                    />
                  </Box>
                )}

                <Text mb={4}>{q.question}</Text>

                {/* Answer options */}
                <VStack align="stretch" spacing={2} mb={4}>
                  {q.options.map((option, optIdx) => (
                    <Box
                      key={optIdx}
                      p={3}
                      borderRadius="md"
                      borderWidth="1px"
                      cursor={quizSubmitted[idx] ? 'default' : 'pointer'}
                      bg={
                        quizSubmitted[idx]
                          ? optIdx === q.correct
                            ? correctBgColor
                            : quizAnswers[idx] === optIdx
                              ? incorrectBgColor
                              : 'white'
                          : quizAnswers[idx] === optIdx
                            ? 'blue.100'
                            : 'white'
                      }
                      borderColor={
                        quizAnswers[idx] === optIdx ? 'blue.400' : 'gray.200'
                      }
                      onClick={() => {
                        if (!quizSubmitted[idx]) {
                          setQuizAnswers(prev => ({ ...prev, [idx]: optIdx }));
                        }
                      }}
                      _hover={!quizSubmitted[idx] ? { bg: 'blue.50' } : {}}
                    >
                      <HStack>
                        <Text fontWeight="bold" color="gray.600">
                          {String.fromCharCode(65 + optIdx)}.
                        </Text>
                        <Text>{option}</Text>
                      </HStack>
                    </Box>
                  ))}
                </VStack>

                {/* Check Answer button */}
                {!quizSubmitted[idx] && (
                  <Button
                    colorScheme="blue"
                    size="sm"
                    isDisabled={quizAnswers[idx] === undefined}
                    onClick={() => {
                      // Check if free user has exceeded quiz limit
                      if (!user && getTotalQuizAnswersSubmitted() >= MAX_FREE_QUIZ_ANSWERS) {
                        setSignupModalMessage('Sign up to answer unlimited practice questions and track your progress.');
                        openSignupModal();
                        return;
                      }
                      setQuizSubmitted(prev => ({ ...prev, [idx]: true }));
                    }}
                  >
                    Check Answer
                  </Button>
                )}

                {/* Explanation after submission */}
                {quizSubmitted[idx] && (
                  <Box
                    mt={4}
                    p={4}
                    bg={quizAnswers[idx] === q.correct ? 'green.50' : 'red.50'}
                    borderRadius="md"
                  >
                    <Text fontWeight="bold" color={quizAnswers[idx] === q.correct ? 'green.600' : 'red.600'}>
                      {quizAnswers[idx] === q.correct ? '✓ Correct!' : '✗ Incorrect'}
                    </Text>
                    <Text mt={2}>{q.explanation}</Text>
                  </Box>
                )}
              </Box>
            ))}

            {/* Score summary */}
            {Object.keys(quizSubmitted).length === quizQuestions.length && quizQuestions.length > 0 && (
              <Box p={4} bg="blue.100" borderRadius="md" textAlign="center">
                <Text fontSize="lg" fontWeight="bold">
                  Score: {Object.entries(quizSubmitted).filter(([idx]) =>
                    quizAnswers[parseInt(idx)] === quizQuestions[parseInt(idx)].correct
                  ).length} / {quizQuestions.length}
                </Text>
              </Box>
            )}
          </VStack>
        )}
      </Box>
    );
  };

  return (
    <Box minH="100vh" bg="gray.50" position="relative">
      <Container maxW="6xl" py={6}>
        <HStack spacing={4} mb={6}>
          <Button
            leftIcon={<IconWrapper icon={FaArrowLeft} size={14} />}
            onClick={() => navigate('/')}
            colorScheme="blue"
            variant="outline"
          >
            Back to Home
          </Button>
          <Button
            colorScheme="purple"
            onClick={() => navigate(`/practice/${subject}`)}
          >
            Practice Questions
          </Button>
        </HStack>

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
      
      {/* Floating Navigation Arrows - show on unit and chapter pages */}
      {unitId && (
        <>
          {/* Previous Arrow */}
          {hasPrevious() && (
            <Box
              position="fixed"
              bottom="50%"
              left="20px"
              transform="translateY(50%)"
              zIndex={1000}
            >
              <Button
                onClick={navigateToPrevious}
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

          {/* Next Arrow */}
          {hasNext() && (
            <Box
              position="fixed"
              bottom="50%"
              right="20px"
              transform="translateY(50%)"
              zIndex={1000}
            >
              <Button
                onClick={navigateToNext}
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

      {/* Signup Prompt Modal */}
      <SignupPromptModal
        isOpen={isSignupModalOpen}
        onClose={closeSignupModal}
        message={signupModalMessage}
      />
    </Box>
  );
};

export default TextbookPage;