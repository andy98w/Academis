import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const API_BASE = 'http://localhost:8000';

interface QuizProgress {
  answers: { [key: number]: number };
  submitted: { [key: number]: boolean };
  score?: number;
  total?: number;
}

interface UseProgressReturn {
  // Quiz progress
  quizAnswers: { [key: number]: number };
  quizSubmitted: { [key: number]: boolean };
  setQuizAnswer: (questionIndex: number, answerIndex: number) => void;
  setQuizSubmitted: (questionIndex: number, isSubmitted: boolean) => void;
  saveQuizProgress: (score?: number, total?: number) => Promise<void>;
  resetQuiz: () => void;

  // Scroll position
  scrollPosition: number | null;
  saveScrollPosition: (position: number) => Promise<void>;
  loadScrollPosition: () => Promise<number | null>;

  // Loading state
  loading: boolean;
  syncing: boolean;
}

export function useProgress(
  subject: string,
  unitId: string | undefined,
  chapterId: string | undefined
): UseProgressReturn {
  const { user, getIdToken } = useAuth();
  const [quizAnswers, setQuizAnswers] = useState<{ [key: number]: number }>({});
  const [quizSubmitted, setQuizSubmittedState] = useState<{ [key: number]: boolean }>({});
  const [scrollPosition, setScrollPosition] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const storageKey = `quiz_${subject}_${unitId}_${chapterId}`;
  const scrollKey = `scroll_${subject}_${unitId}_${chapterId || 'overview'}`;

  // Load progress on mount or when chapter changes
  useEffect(() => {
    const loadProgress = async () => {
      setLoading(true);

      if (user && chapterId) {
        // Try to load from server if authenticated
        try {
          const token = await getIdToken();
          if (token) {
            const response = await axios.get(
              `${API_BASE}/api/user/progress/${subject}/${chapterId}`,
              { headers: { Authorization: `Bearer ${token}` } }
            );

            if (response.data.quiz) {
              setQuizAnswers(response.data.quiz.answers || {});
              setQuizSubmittedState(response.data.quiz.submitted || {});
            }
            if (response.data.scroll_position != null) {
              setScrollPosition(response.data.scroll_position);
            }
            setLoading(false);
            return;
          }
        } catch (error) {
          console.warn('Failed to load progress from server, falling back to localStorage');
        }
      }

      // Fall back to localStorage
      const savedState = localStorage.getItem(storageKey);
      if (savedState) {
        try {
          const { answers, submitted } = JSON.parse(savedState);
          setQuizAnswers(answers || {});
          setQuizSubmittedState(submitted || {});
        } catch {
          // Invalid JSON, ignore
        }
      } else {
        setQuizAnswers({});
        setQuizSubmittedState({});
      }

      const savedScroll = localStorage.getItem(scrollKey);
      if (savedScroll) {
        setScrollPosition(parseInt(savedScroll, 10));
      }

      setLoading(false);
    };

    loadProgress();
  }, [user, subject, unitId, chapterId, storageKey, scrollKey, getIdToken]);

  // Save to localStorage whenever quiz state changes
  useEffect(() => {
    if (!loading && chapterId) {
      localStorage.setItem(
        storageKey,
        JSON.stringify({ answers: quizAnswers, submitted: quizSubmitted })
      );
    }
  }, [quizAnswers, quizSubmitted, storageKey, loading, chapterId]);

  const setQuizAnswer = useCallback((questionIndex: number, answerIndex: number) => {
    setQuizAnswers((prev) => ({ ...prev, [questionIndex]: answerIndex }));
  }, []);

  const setQuizSubmitted = useCallback((questionIndex: number, isSubmitted: boolean) => {
    setQuizSubmittedState((prev) => ({ ...prev, [questionIndex]: isSubmitted }));
  }, []);

  const saveQuizProgress = useCallback(async (score?: number, total?: number) => {
    if (!user || !chapterId) return;

    setSyncing(true);
    try {
      const token = await getIdToken();
      if (token) {
        await axios.post(
          `${API_BASE}/api/user/progress`,
          {
            subject,
            chapter_id: chapterId,
            answers: quizAnswers,
            submitted: quizSubmitted,
            score,
            total,
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (error) {
      console.error('Failed to save quiz progress:', error);
    } finally {
      setSyncing(false);
    }
  }, [user, subject, chapterId, quizAnswers, quizSubmitted, getIdToken]);

  const resetQuiz = useCallback(() => {
    setQuizAnswers({});
    setQuizSubmittedState({});
    localStorage.removeItem(storageKey);

    // Also reset on server if authenticated
    if (user && chapterId) {
      getIdToken().then((token) => {
        if (token) {
          axios.post(
            `${API_BASE}/api/user/progress`,
            {
              subject,
              chapter_id: chapterId,
              answers: {},
              submitted: {},
            },
            { headers: { Authorization: `Bearer ${token}` } }
          ).catch(console.error);
        }
      });
    }
  }, [user, subject, chapterId, storageKey, getIdToken]);

  const saveScrollPosition = useCallback(async (position: number) => {
    localStorage.setItem(scrollKey, String(position));

    if (!user || !chapterId) return;

    try {
      const token = await getIdToken();
      if (token) {
        await axios.post(
          `${API_BASE}/api/user/scroll`,
          {
            subject,
            chapter_id: chapterId,
            scroll_position: position,
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (error) {
      console.error('Failed to save scroll position:', error);
    }
  }, [user, subject, chapterId, scrollKey, getIdToken]);

  const loadScrollPosition = useCallback(async (): Promise<number | null> => {
    if (user && chapterId) {
      try {
        const token = await getIdToken();
        if (token) {
          const response = await axios.get(
            `${API_BASE}/api/user/progress/${subject}/${chapterId}`,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (response.data.scroll_position != null) {
            return response.data.scroll_position;
          }
        }
      } catch {
        // Fall through to localStorage
      }
    }

    const saved = localStorage.getItem(scrollKey);
    return saved ? parseInt(saved, 10) : null;
  }, [user, subject, chapterId, scrollKey, getIdToken]);

  return {
    quizAnswers,
    quizSubmitted,
    setQuizAnswer,
    setQuizSubmitted,
    saveQuizProgress,
    resetQuiz,
    scrollPosition,
    saveScrollPosition,
    loadScrollPosition,
    loading,
    syncing,
  };
}
