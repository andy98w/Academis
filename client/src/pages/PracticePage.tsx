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
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  useDisclosure,
  Select,
  Badge,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Image,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaRedo, FaCheck, FaTimes } from 'react-icons/fa';
import axios from 'axios';
import IconWrapper from '../components/IconWrapper';
import { getSubjectConfig } from '../config/subjects';
import { useAuth } from '../context/AuthContext';
import SignupPromptModal from '../components/SignupPromptModal';

interface QuizQuestion {
  type: 'text' | 'table' | 'graph';
  question: string;
  options: string[];
  correct: number;
  explanation: string;
  chapter_id: string;
  chapter_title: string;
  unit: number;
  unit_title: string;
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

interface PracticePageProps {
  subject: string;
}

const PracticePage: React.FC<PracticePageProps> = ({ subject }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isOpen: isSignupModalOpen, onOpen: openSignupModal, onClose: closeSignupModal } = useDisclosure();
  const subjectConfig = getSubjectConfig(subject);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allQuestions, setAllQuestions] = useState<QuizQuestion[]>([]);
  const [filteredQuestions, setFilteredQuestions] = useState<QuizQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(0);
  const [unitFilter, setUnitFilter] = useState<string>('all');

  const MAX_FREE_QUIZ_ANSWERS = 5;

  const bgColor = useColorModeValue('white', 'gray.800');
  const correctBgColor = useColorModeValue('green.100', 'green.800');
  const incorrectBgColor = useColorModeValue('red.100', 'red.800');
  const optionHoverBg = useColorModeValue('blue.50', 'blue.900');

  // Fetch all questions
  useEffect(() => {
    const fetchQuestions = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(`http://localhost:8080/api/quiz/${subject}/all`);
        if (response.data.questions && response.data.questions.length > 0) {
          // Shuffle questions
          const shuffled = [...response.data.questions].sort(() => Math.random() - 0.5);
          setAllQuestions(shuffled);
          setFilteredQuestions(shuffled);
        } else {
          setAllQuestions([]);
          setFilteredQuestions([]);
        }
      } catch (err) {
        console.error('Error fetching questions:', err);
        setError('Failed to load practice questions. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchQuestions();
  }, [subject]);

  // Filter questions by unit
  useEffect(() => {
    if (unitFilter === 'all') {
      setFilteredQuestions(allQuestions);
    } else {
      const unitNum = parseInt(unitFilter);
      setFilteredQuestions(allQuestions.filter(q => q.unit === unitNum));
    }
    setCurrentIndex(0);
    setSelectedAnswer(null);
    setShowResult(false);
  }, [unitFilter, allQuestions]);

  // Get unique units for filter
  const uniqueUnits = Array.from(new Set(allQuestions.map(q => q.unit))).sort((a, b) => a - b);

  const currentQuestion = filteredQuestions[currentIndex];

  const handleAnswerSelect = (optionIndex: number) => {
    if (showResult) return;
    setSelectedAnswer(optionIndex);
  };

  const handleCheckAnswer = () => {
    if (selectedAnswer === null) return;

    // Check if free user has exceeded quiz limit
    if (!user && answered >= MAX_FREE_QUIZ_ANSWERS) {
      openSignupModal();
      return;
    }

    setShowResult(true);
    setAnswered(prev => prev + 1);
    if (selectedAnswer === currentQuestion.correct) {
      setScore(prev => prev + 1);
    }
  };

  const handleNextQuestion = () => {
    if (currentIndex < filteredQuestions.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setShowResult(false);
    }
  };

  const handlePrevQuestion = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      setSelectedAnswer(null);
      setShowResult(false);
    }
  };

  const handleReset = () => {
    // Reshuffle
    const shuffled = [...filteredQuestions].sort(() => Math.random() - 0.5);
    setFilteredQuestions(shuffled);
    setCurrentIndex(0);
    setSelectedAnswer(null);
    setShowResult(false);
    setScore(0);
    setAnswered(0);
  };

  return (
    <Box minH="100vh" bg="gray.50">
      <Container maxW="4xl" py={6}>
        <Button
          leftIcon={<IconWrapper icon={FaArrowLeft} size={14} />}
          onClick={() => navigate(`/textbook/${subject}`)}
          colorScheme="blue"
          variant="outline"
          mb={6}
        >
          Back to Textbook
        </Button>

        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box bg={bgColor} p={6} borderRadius="lg" shadow="md">
            <HStack justify="space-between" wrap="wrap" spacing={4}>
              <VStack align="start" spacing={1}>
                <Heading size="lg">{subjectConfig.fullName} Practice</Heading>
                <Text color="gray.600">Test your knowledge with questions from all chapters</Text>
              </VStack>
              <HStack spacing={4}>
                <Select
                  value={unitFilter}
                  onChange={(e) => setUnitFilter(e.target.value)}
                  w="200px"
                  bg="white"
                >
                  <option value="all">All Units</option>
                  {uniqueUnits.map(unit => (
                    <option key={unit} value={unit}>Unit {unit}</option>
                  ))}
                </Select>
                <Button
                  leftIcon={<IconWrapper icon={FaRedo} size={14} />}
                  onClick={handleReset}
                  colorScheme="purple"
                  variant="outline"
                >
                  Reset
                </Button>
              </HStack>
            </HStack>

            {/* Progress */}
            {filteredQuestions.length > 0 && (
              <Box mt={4}>
                <HStack justify="space-between" mb={2}>
                  <Text fontSize="sm" color="gray.600">
                    Question {currentIndex + 1} of {filteredQuestions.length}
                  </Text>
                  <HStack spacing={4}>
                    <Badge colorScheme="green">Score: {score}/{answered}</Badge>
                    <Badge colorScheme="blue">
                      {answered > 0 ? Math.round((score / answered) * 100) : 0}%
                    </Badge>
                  </HStack>
                </HStack>
                <Progress
                  value={(currentIndex + 1) / filteredQuestions.length * 100}
                  size="sm"
                  colorScheme="blue"
                  borderRadius="full"
                />
              </Box>
            )}
          </Box>

          {/* Free user quiz limit message */}
          {!user && !loading && filteredQuestions.length > 0 && (
            <Alert status="info" borderRadius="md">
              <AlertIcon />
              <Text fontSize="sm">
                {answered >= MAX_FREE_QUIZ_ANSWERS
                  ? 'You\'ve used all 5 free practice questions. Sign up to continue!'
                  : `Free preview: ${MAX_FREE_QUIZ_ANSWERS - answered} questions remaining. Sign up for unlimited access.`}
              </Text>
            </Alert>
          )}

          {/* Loading/Error states */}
          {loading ? (
            <Flex justify="center" align="center" height="300px" direction="column">
              <Spinner size="xl" mb={4} color="blue.500" />
              <Text>Loading practice questions...</Text>
            </Flex>
          ) : error ? (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {error}
            </Alert>
          ) : filteredQuestions.length === 0 ? (
            <Alert status="info" borderRadius="md">
              <AlertIcon />
              No practice questions available yet. Questions are generated when chapters are created.
            </Alert>
          ) : currentQuestion ? (
            /* Question Card */
            <Box bg={bgColor} p={6} borderRadius="lg" shadow="md">
              {/* Chapter info */}
              <HStack mb={4} spacing={2}>
                <Badge colorScheme="purple">Unit {currentQuestion.unit}</Badge>
                <Badge colorScheme="blue">{currentQuestion.chapter_title}</Badge>
              </HStack>

              {/* Table if present */}
              {currentQuestion.type === 'table' && currentQuestion.table && (
                <Box mb={4} overflowX="auto">
                  <Text fontWeight="medium" mb={2}>{currentQuestion.table.title}</Text>
                  <TableContainer>
                    <Table size="sm" variant="simple">
                      <Thead>
                        <Tr>
                          {currentQuestion.table.columns.map((col, i) => (
                            <Th key={i}>{col}</Th>
                          ))}
                        </Tr>
                      </Thead>
                      <Tbody>
                        {currentQuestion.table.rows.map((row, i) => (
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

              {/* Graph if present */}
              {currentQuestion.type === 'graph' && currentQuestion.graph?.image && (
                <Box mb={4}>
                  <Image
                    src={`data:image/png;base64,${currentQuestion.graph.image}`}
                    alt="Question graph"
                    maxW="400px"
                    borderRadius="md"
                    mx="auto"
                  />
                </Box>
              )}

              {/* Question text */}
              <Text fontSize="lg" fontWeight="medium" mb={6}>
                {currentQuestion.question}
              </Text>

              {/* Options */}
              <VStack align="stretch" spacing={3} mb={6}>
                {currentQuestion.options.map((option, idx) => (
                  <Box
                    key={idx}
                    p={4}
                    borderRadius="md"
                    borderWidth="2px"
                    cursor={showResult ? 'default' : 'pointer'}
                    bg={
                      showResult
                        ? idx === currentQuestion.correct
                          ? correctBgColor
                          : selectedAnswer === idx
                            ? incorrectBgColor
                            : 'white'
                        : selectedAnswer === idx
                          ? 'blue.100'
                          : 'white'
                    }
                    borderColor={
                      showResult
                        ? idx === currentQuestion.correct
                          ? 'green.400'
                          : selectedAnswer === idx
                            ? 'red.400'
                            : 'gray.200'
                        : selectedAnswer === idx
                          ? 'blue.400'
                          : 'gray.200'
                    }
                    onClick={() => handleAnswerSelect(idx)}
                    _hover={!showResult ? { bg: optionHoverBg } : {}}
                    transition="all 0.2s"
                  >
                    <HStack justify="space-between">
                      <HStack>
                        <Text fontWeight="bold" color="gray.600">
                          {String.fromCharCode(65 + idx)}.
                        </Text>
                        <Text>{option}</Text>
                      </HStack>
                      {showResult && idx === currentQuestion.correct && (
                        <IconWrapper icon={FaCheck} size={16} />
                      )}
                      {showResult && selectedAnswer === idx && idx !== currentQuestion.correct && (
                        <IconWrapper icon={FaTimes} size={16} />
                      )}
                    </HStack>
                  </Box>
                ))}
              </VStack>

              {/* Explanation after answering */}
              {showResult && (
                <Box
                  p={4}
                  bg={selectedAnswer === currentQuestion.correct ? 'green.50' : 'red.50'}
                  borderRadius="md"
                  mb={6}
                >
                  <Text fontWeight="bold" color={selectedAnswer === currentQuestion.correct ? 'green.600' : 'red.600'}>
                    {selectedAnswer === currentQuestion.correct ? 'Correct!' : 'Incorrect'}
                  </Text>
                  <Text mt={2}>{currentQuestion.explanation}</Text>
                </Box>
              )}

              {/* Navigation */}
              <HStack justify="space-between">
                <Button
                  onClick={handlePrevQuestion}
                  isDisabled={currentIndex === 0}
                  variant="outline"
                >
                  Previous
                </Button>

                {!showResult ? (
                  <Button
                    colorScheme="blue"
                    onClick={handleCheckAnswer}
                    isDisabled={selectedAnswer === null}
                  >
                    Check Answer
                  </Button>
                ) : (
                  <Button
                    colorScheme="blue"
                    onClick={handleNextQuestion}
                    isDisabled={currentIndex === filteredQuestions.length - 1}
                  >
                    Next Question
                  </Button>
                )}
              </HStack>
            </Box>
          ) : null}
        </VStack>
      </Container>

      {/* Signup Prompt Modal */}
      <SignupPromptModal
        isOpen={isSignupModalOpen}
        onClose={closeSignupModal}
        message="Sign up to answer unlimited practice questions and track your progress across all devices."
      />
    </Box>
  );
};

export default PracticePage;
