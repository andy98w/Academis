import React from 'react';
import { ChakraProvider, Box, Flex, Container, Heading, Spacer } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, useParams, Link as RouterLink } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SubjectPage from './pages/SubjectPage';
import TextbookPage from './pages/TextbookPage';
import PracticePage from './pages/PracticePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import UserMenu from './components/UserMenu';
import { AuthProvider } from './context/AuthContext';
import { getSubjectConfig } from './config/subjects';
import './App.css';

// Wrapper component to extract subject from URL params
const SubjectPageWrapper: React.FC = () => {
  const { subject } = useParams<{ subject: string }>();

  if (!subject) {
    return <div>Subject not specified</div>;
  }

  try {
    // Validate subject exists
    getSubjectConfig(subject);
    return <SubjectPage subjectId={subject} />;
  } catch (error) {
    return <div>Subject not found: {subject}</div>;
  }
};

const TextbookPageWrapper: React.FC = () => {
  const { subject } = useParams<{ subject: string }>();

  if (!subject) {
    return <div>Subject not specified</div>;
  }

  try {
    // Validate subject exists
    getSubjectConfig(subject);
    return <TextbookPage subject={subject} />;
  } catch (error) {
    return <div>Subject not found: {subject}</div>;
  }
};

const PracticePageWrapper: React.FC = () => {
  const { subject } = useParams<{ subject: string }>();

  if (!subject) {
    return <div>Subject not specified</div>;
  }

  try {
    getSubjectConfig(subject);
    return <PracticePage subject={subject} />;
  } catch (error) {
    return <div>Subject not found: {subject}</div>;
  }
};

// Navigation header component
const Header: React.FC = () => {
  return (
    <Box
      as="header"
      position="fixed"
      top={0}
      left={0}
      right={0}
      zIndex={1000}
      bg="white"
      borderBottom="1px"
      borderColor="gray.200"
      boxShadow="sm"
    >
      <Container maxW="container.xl">
        <Flex h="60px" align="center">
          <Heading
            as={RouterLink}
            to="/"
            size="md"
            color="blue.600"
            fontWeight="bold"
            _hover={{ textDecoration: 'none', color: 'blue.700' }}
          >
            Academis
          </Heading>
          <Spacer />
          <UserMenu />
        </Flex>
      </Container>
    </Box>
  );
};

function AppContent() {
  return (
    <BrowserRouter>
      <Box minH="100vh" bg="gray.50">
        <Header />
        <Box pt="60px">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/profile" element={<ProfilePage />} />

            {/* Dynamic subject routes */}
            <Route path="/subject/:subject" element={<SubjectPageWrapper />} />
            <Route path="/textbook/:subject" element={<TextbookPageWrapper />} />
            <Route path="/textbook/:subject/unit/:unitId" element={<TextbookPageWrapper />} />
            <Route path="/textbook/:subject/unit/:unitId/chapter/:chapterId" element={<TextbookPageWrapper />} />
            <Route path="/practice/:subject" element={<PracticePageWrapper />} />

            {/* Catch-all for unknown routes */}
            <Route path="*" element={<div>Page not found</div>} />
          </Routes>
        </Box>
      </Box>
    </BrowserRouter>
  );
}

function App() {
  return (
    <ChakraProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ChakraProvider>
  );
}

export default App;
