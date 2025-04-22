import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Flex,
  Input,
  Button,
  VStack,
  Text,
  Spinner,
  InputGroup,
  InputRightElement,
  useColorModeValue,
  IconButton,
  Heading,
} from '@chakra-ui/react';
import { FaArrowUp, FaChevronUp, FaChevronDown, FaTimes, FaQuestion } from 'react-icons/fa';
import axios from 'axios';
import IconWrapper, { renderIcon } from './IconWrapper';

interface Message {
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatInterfaceProps {
  subject: 'micro' | 'macro';
  floatingMode?: boolean;
  onClose?: () => void;
  defaultOpen?: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  subject, 
  floatingMode = false, 
  onClose,
  defaultOpen = true
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      text: `Welcome to AP ${
        subject === 'micro' ? 'Microeconomics' : 'Macroeconomics'
      }! How can I help you today?`,
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(defaultOpen);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Define all color mode values up front to avoid conditional hook calls
  const userBg = useColorModeValue('blue.50', 'blue.900');
  const botBg = useColorModeValue('gray.100', 'gray.700');
  const bgColor = useColorModeValue('white', 'gray.800');
  const inputBg = useColorModeValue('white', 'gray.700');

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = {
      text: input,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Use the appropriate endpoint based on the subject
      const endpoint = `http://localhost:8080/api/rag/${subject}/ask`;
      const response = await axios.post(endpoint, {
        question: input,
        session_id: `user_${subject}`, // Create a session ID for the user
      });

      const botMessage: Message = {
        text: response.data.answer,
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error fetching response:', error);
      
      const errorMessage: Message = {
        text: 'Sorry, I encountered an error. Please try again later.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpansion = () => {
    setIsExpanded(!isExpanded);
  };

  // Different styling for floating mode vs embedded mode
  if (floatingMode) {
    return (
      <Box
        position="fixed"
        bottom="20px"
        right="20px"
        width={isExpanded ? "400px" : "auto"}
        zIndex={1000}
        transition="all 0.3s ease"
        boxShadow="xl"
        borderRadius="lg"
        overflow="hidden"
      >
        {/* Chat Header */}
        <Flex 
          bg="blue.500" 
          color="white" 
          p={2} 
          justify="space-between" 
          align="center"
          cursor="pointer"
          onClick={toggleExpansion}
        >
          <Flex align="center">
            <Box mr={2}>
              <IconWrapper icon={FaQuestion} size={14} />
            </Box>
            <Heading size="sm">
              AP {subject === 'micro' ? 'Microeconomics' : 'Macroeconomics'} Chat
            </Heading>
          </Flex>
          <Flex>
            {isExpanded && onClose && (
              <IconButton
                aria-label="Close chat"
                icon={<IconWrapper icon={FaTimes} size={14} />}
                size="sm"
                variant="ghost"
                color="white"
                onClick={(e) => {
                  e.stopPropagation();
                  onClose();
                }}
                mr={1}
              />
            )}
            <IconButton
              aria-label={isExpanded ? "Collapse chat" : "Expand chat"}
              icon={<IconWrapper icon={isExpanded ? FaChevronDown : FaChevronUp} size={14} />}
              size="sm"
              variant="ghost"
              color="white"
              onClick={toggleExpansion}
            />
          </Flex>
        </Flex>

        {/* Collapsible Content */}
        {isExpanded && (
          <Box
            bg={bgColor}
            width="100%"
            display="flex"
            flexDir="column"
            height="500px"
          >
            {/* Chat Messages */}
            <VStack
              flex="1"
              p={4}
              overflowY="auto"
              spacing={4}
              align="stretch"
              mb={2}
            >
              {messages.map((message, index) => (
                <Flex
                  key={index}
                  justify={message.isUser ? 'flex-end' : 'flex-start'}
                  w="100%"
                >
                  <Box
                    maxW="80%"
                    p={3}
                    borderRadius="lg"
                    bg={message.isUser ? userBg : botBg}
                    boxShadow="sm"
                  >
                    <Text>{message.text}</Text>
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      {message.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </Text>
                  </Box>
                </Flex>
              ))}
              {isLoading && (
                <Flex justify="flex-start" w="100%">
                  <Box p={3} borderRadius="lg" bg={botBg} boxShadow="sm">
                    <Spinner size="sm" mr={2} />
                    <Text as="span">Thinking...</Text>
                  </Box>
                </Flex>
              )}
              <div ref={messagesEndRef} />
            </VStack>

            {/* Input Area */}
            <Box as="form" onSubmit={handleSubmit} p={2}>
              <InputGroup size="md">
                <Input
                  placeholder="Ask a question..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  borderRadius="full"
                  focusBorderColor="blue.400"
                  autoComplete="off"
                  bg={inputBg}
                  boxShadow="sm"
                  _focus={{ boxShadow: 'outline' }}
                />
                <InputRightElement width="4.5rem">
                  <Button
                    h="1.75rem"
                    size="sm"
                    colorScheme="blue"
                    borderRadius="full"
                    isLoading={isLoading}
                    type="submit"
                    disabled={!input.trim() || isLoading}
                  >
                    Send
                  </Button>
                </InputRightElement>
              </InputGroup>
            </Box>
          </Box>
        )}
      </Box>
    );
  }

  // Original embedded chat interface
  return (
    <Box
      w="100%"
      h="100%"
      display="flex"
      flexDir="column"
      borderRadius="lg"
      overflow="hidden"
    >
      {/* Chat Messages */}
      <VStack
        flex="1"
        p={4}
        overflowY="auto"
        spacing={4}
        align="stretch"
        bg={bgColor}
        boxShadow="sm"
        borderRadius="lg"
        mb={4}
        maxH="70vh"
      >
        {messages.map((message, index) => (
          <Flex
            key={index}
            justify={message.isUser ? 'flex-end' : 'flex-start'}
            w="100%"
          >
            <Box
              maxW="80%"
              p={3}
              borderRadius="lg"
              bg={message.isUser ? userBg : botBg}
              boxShadow="sm"
            >
              <Text>{message.text}</Text>
              <Text fontSize="xs" color="gray.500" mt={1}>
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </Text>
            </Box>
          </Flex>
        ))}
        {isLoading && (
          <Flex justify="flex-start" w="100%">
            <Box p={3} borderRadius="lg" bg={botBg} boxShadow="sm">
              <Spinner size="sm" mr={2} />
              <Text as="span">Thinking...</Text>
            </Box>
          </Flex>
        )}
        <div ref={messagesEndRef} />
      </VStack>

      {/* Input Area */}
      <Box as="form" onSubmit={handleSubmit}>
        <InputGroup size="lg">
          <Input
            placeholder="Ask a question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            borderRadius="full"
            focusBorderColor="blue.400"
            autoComplete="off"
            bg={inputBg}
            boxShadow="sm"
            _focus={{ boxShadow: 'outline' }}
          />
          <InputRightElement width="4.5rem">
            <Button
              h="1.75rem"
              size="sm"
              colorScheme="blue"
              borderRadius="full"
              isLoading={isLoading}
              type="submit"
              disabled={!input.trim() || isLoading}
            >
              Send
            </Button>
          </InputRightElement>
        </InputGroup>
      </Box>
    </Box>
  );
};

export default ChatInterface;